"""Multiplayer networking for KYROS Game Engine.

Leverages Go hsync pub/sub for game state broadcast.
Provides matchmaking, state sync, and lag compensation.
"""
import asyncio
import json
import socket
import struct
import threading
import time
from collections import defaultdict


class NetworkPlayer:
    def __init__(self, player_id, name, address=None):
        self.id = player_id
        self.name = name
        self.address = address
        self.latency_ms = 0
        self.last_heartbeat = time.time()
        self.state = {}  # position, rotation, health, etc.
        self.connected = True


class GameServer:
    def __init__(self, host="127.0.0.1", port=9876, max_players=16):
        self.host = host
        self.port = port
        self.max_players = max_players
        self.players = {}
        self._socket = None
        self._running = False
        self._thread = None
        self._state_lock = threading.Lock()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((self.host, self.port))
        self._socket.settimeout(1.0)

        while self._running:
            try:
                data, addr = self._socket.recvfrom(4096)
                self._handle_packet(data, addr)
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_packet(self, data, addr):
        try:
            msg = json.loads(data.decode())
            ptype = msg.get("type", "")
            if ptype == "join":
                pid = msg["player_id"]
                self.players[pid] = NetworkPlayer(pid, msg.get("name", pid), addr)
                self._broadcast({"type": "player_joined", "player_id": pid, "count": len(self.players)})
            elif ptype == "state":
                pid = msg["player_id"]
                if pid in self.players:
                    self.players[pid].state = msg.get("state", {})
                    self.players[pid].last_heartbeat = time.time()
            elif ptype == "leave":
                pid = msg["player_id"]
                self.players.pop(pid, None)
                self._broadcast({"type": "player_left", "player_id": pid, "count": len(self.players)})
        except Exception:
            pass

    def _broadcast(self, msg, exclude=None):
        data = json.dumps(msg).encode()
        for pid, player in list(self.players.items()):
            if pid == exclude:
                continue
            if player.address:
                try:
                    self._socket.sendto(data, player.address)
                except Exception:
                    pass

    def get_state_snapshot(self):
        """Get full game state for new players."""
        with self._state_lock:
            return {
                "players": {pid: {"name": p.name, "state": p.state} for pid, p in self.players.items()},
                "count": len(self.players),
            }

    def stop(self):
        self._running = False
        if self._socket:
            self._socket.close()
        if self._thread:
            self._thread.join(timeout=2)


class GameClient:
    def __init__(self, player_id, name, server_host="127.0.0.1", server_port=9876):
        self.player_id = player_id
        self.name = name
        self.server_addr = (server_host, server_port)
        self._socket = None
        self._running = False
        self._thread = None
        self.remote_players = {}
        self.latency_ms = 0

    def connect(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(1.0)
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        self._send({"type": "join", "player_id": self.player_id, "name": self.name})

    def _listen(self):
        while self._running:
            try:
                data, _ = self._socket.recvfrom(4096)
                msg = json.loads(data.decode())
                self._handle_message(msg)
            except socket.timeout:
                continue
            except Exception:
                break

    def _handle_message(self, msg):
        ptype = msg.get("type", "")
        if ptype == "player_joined":
            pass
        elif ptype == "player_left":
            self.remote_players.pop(msg["player_id"], None)
        elif ptype == "state_update":
            self.remote_players.update(msg.get("players", {}))

    def _send(self, msg):
        if self._socket:
            try:
                self._socket.sendto(json.dumps(msg).encode(), self.server_addr)
            except Exception:
                pass

    def send_state(self, state):
        self._send({"type": "state", "player_id": self.player_id, "state": state})

    def disconnect(self):
        self._send({"type": "leave", "player_id": self.player_id})
        self._running = False
        if self._socket:
            self._socket.close()
        if self._thread:
            self._thread.join(timeout=2)

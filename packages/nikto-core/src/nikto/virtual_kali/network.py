"""Network Simulator — Virtual Kali network environment.

Simulates network interfaces, routing, services, and targets
for the virtual Kali environment. Supports:
- Virtual interfaces (eth0, wlan0, lo, tun0)
- IP configuration
- ARP table, routing table
- Simulated target hosts/networks
- Service discovery simulation
"""

from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple


@dataclass
class VirtualInterface:
    name: str
    ip: str = "0.0.0.0"
    netmask: str = "255.255.255.0"
    mac: str = ""
    state: str = "UP"
    type: str = "wired"
    speed: int = 1000
    rx_bytes: int = 0
    tx_bytes: int = 0

    def __post_init__(self):
        if not self.mac:
            self.mac = ":".join(f"{random.randint(0,255):02x}" for _ in range(6))


@dataclass
class RouteEntry:
    destination: str
    gateway: str
    netmask: str
    flags: str = "UG"
    metric: int = 100
    iface: str = "eth0"


@dataclass
class ARPEntry:
    ip: str
    mac: str
    iface: str = "eth0"
    type: str = "dynamic"


@dataclass
class VirtualHost:
    ip: str
    hostname: str = ""
    open_ports: List[int] = field(default_factory=list)
    os: str = "Linux"
    services: Dict[int, str] = field(default_factory=dict)


class NetworkSimulator:
    """Simulated Kali Linux network environment."""

    def __init__(self):
        self.interfaces: Dict[str, VirtualInterface] = {}
        self.routes: List[RouteEntry] = []
        self.arp_table: List[ARPEntry] = []
        self.hosts: Dict[str, VirtualHost] = {}
        self.dns_cache: Dict[str, str] = {}
        self._init_defaults()

    def _init_defaults(self):
        self.interfaces["lo"] = VirtualInterface("lo", "127.0.0.1", "255.0.0.0",
                                                  "00:00:00:00:00:00", type="loopback")
        self.interfaces["eth0"] = VirtualInterface("eth0", "192.168.1.100",
                                                    "255.255.255.0", type="wired")
        self.interfaces["wlan0"] = VirtualInterface("wlan0", "192.168.1.101",
                                                     "255.255.255.0", type="wireless")
        self.routes = [
            RouteEntry("0.0.0.0", "192.168.1.1", "0.0.0.0"),
            RouteEntry("192.168.1.0", "0.0.0.0", "255.255.255.0"),
            RouteEntry("10.0.0.0", "192.168.1.1", "255.0.0.0"),
        ]
        self.arp_table = [
            ARPEntry("192.168.1.1", "aa:bb:cc:dd:ee:01"),
            ARPEntry("192.168.1.102", "aa:bb:cc:dd:ee:02"),
        ]
        self.dns_cache = {
            "google.com": "142.250.80.46",
            "kali.org": "192.99.200.113",
            "github.com": "140.82.121.3",
            "nikto.ai": "10.0.0.10",
        }

    def ifconfig(self, iface: Optional[str] = None) -> str:
        if iface:
            ifs = [self.interfaces.get(iface)] if iface in self.interfaces else []
        else:
            ifs = list(self.interfaces.values())
        if not ifs:
            return f"Device \"{iface}\" does not exist.\n"
        result = ""
        for i in ifs:
            result += (f"{i.name}: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n"
                       f"        inet {i.ip}  netmask {i.netmask}  broadcast {'.'.join(i.ip.split('.')[:3])}.255\n"
                       f"        inet6 fe80::{i.mac.replace(':','')[:4]}:{i.mac.replace(':','')[4:8]}  prefixlen 64  scopeid 0x20<link>\n"
                       f"        ether {i.mac}  txqueuelen 1000  (Ethernet)\n"
                       f"        RX packets {i.rx_bytes}  bytes {i.rx_bytes * 1500} (1.4 MB)\n"
                       f"        TX packets {i.tx_bytes}  bytes {i.tx_bytes * 1500} (1.4 MB)\n\n")
        return result

    def ping(self, target: str, count: int = 4) -> str:
        ip = self.dns_cache.get(target, target)
        if self.interfaces["eth0"].state != "UP":
            return f"connect: Network is unreachable\n"
        ttl = random.randint(56, 64)
        result = f"PING {target} ({ip}) 56(84) bytes of data.\n"
        times = []
        for i in range(count):
            delay = random.uniform(0.5, 15.0)
            times.append(delay)
            result += (f"{ip} bytes from {ip}: icmp_seq={i+1} ttl={ttl} "
                       f"time={delay:.2f} ms\n")
        loss = 0
        avg = sum(times) / len(times) if times else 0
        result += (f"\n--- {target} ping statistics ---\n"
                   f"{count} packets transmitted, {count - loss} received, "
                   f"{loss/count*100 if count else 0}% packet loss, time {count*1000}ms\n"
                   f"rtt min/avg/max/mdev = {min(times):.3f}/{avg:.3f}/{max(times):.3f}/{avg*.15:.3f} ms\n")
        return result

    def traceroute(self, target: str, max_hops: int = 30) -> str:
        ip = self.dns_cache.get(target, target)
        result = f"traceroute to {target} ({ip}), {max_hops} hops max, 60 byte packets\n"
        hops = random.randint(5, 15)
        for i in range(1, hops + 1):
            delay1 = random.uniform(0.5, 20.0)
            delay2 = random.uniform(0.5, 20.0)
            delay3 = random.uniform(0.5, 20.0)
            if i == hops:
                result += f" {i:2d}  {ip} ({ip})  {delay1:.3f} ms  {delay2:.3f} ms  {delay3:.3f} ms\n"
            else:
                hop_ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
                result += f" {i:2d}  {hop_ip} ({hop_ip})  {delay1:.3f} ms  {delay2:.3f} ms  {delay3:.3f} ms\n"
        return result

    def netstat(self, flags: str = "") -> str:
        result = "Active Internet connections (servers and established)\n"
        result += "Proto Recv-Q Send-Q Local Address           Foreign Address         State\n"
        connections = [
            ("tcp", "0", "0", "0.0.0.0:22", "0.0.0.0:*", "LISTEN"),
            ("tcp", "0", "0", "127.0.0.1:3306", "0.0.0.0:*", "LISTEN"),
            ("tcp", "0", "0", "0.0.0.0:80", "0.0.0.0:*", "LISTEN"),
            ("tcp", "0", "0", "0.0.0.0:443", "0.0.0.0:*", "LISTEN"),
            ("tcp", "0", "0", "192.168.1.100:22", "192.168.1.50:54321", "ESTABLISHED"),
            ("udp", "0", "0", "0.0.0.0:68", "0.0.0.0:*", ""),
            ("tcp6", "0", "0", ":::22", ":::*", "LISTEN"),
        ]
        for proto, rq, sq, local, foreign, state in connections:
            result += f"{proto:<6} {rq:<5} {sq:<5} {local:<22} {foreign:<22} {state}\n"
        return result

    def route_table(self) -> str:
        result = "Kernel IP routing table\n"
        result += "Destination     Gateway         Genmask         Flags Metric Ref    Use Iface\n"
        for r in self.routes:
            result += (f"{r.destination:<16} {r.gateway:<16} {r.netmask:<16} "
                       f"{r.flags:<5} {r.metric:<6} 0        {r.iface}\n")
        return result

    def arp_table(self) -> str:
        result = "Address                  HWtype  HWaddress           Flags Mask            Iface\n"
        for a in self.arp_table:
            result += f"{a.ip:<25} ether   {a.mac:<19} C                     {a.iface}\n"
        return result

    def resolve(self, hostname: str) -> Optional[str]:
        return self.dns_cache.get(hostname)

    def add_host(self, ip: str, hostname: str = "", ports: Optional[List[int]] = None):
        host = VirtualHost(ip=ip, hostname=hostname, open_ports=ports or [])
        for p in host.open_ports:
            host.services[p] = self._service_name(p)
        self.hosts[ip] = host

    def scan_network(self, subnet: str = "192.168.1.0/24") -> str:
        result = (f"Starting Nmap 7.94 ( https://nmap.org )\n"
                  f"Nmap scan report for {subnet}\n"
                  f"Host is up (0.042s latency).\n\n")
        hosts_found = 0
        for i in range(1, 255):
            ip = f"192.168.1.{i}"
            if ip in [a.ip for a in self.arp_table] or ip == "192.168.1.100":
                continue
            if random.random() < 0.15:
                hosts_found += 1
                hostname = f"host-{ip.replace('.','-')}"
                ports = random.sample([22, 80, 443, 8080, 3306, 21, 25, 110, 143, 445],
                                       random.randint(1, 5))
                result += f"Nmap scan report for {hostname} ({ip})\n"
                result += f"Host is up (0.0{random.randint(1,9)}s latency).\n"
                result += "PORT     STATE    SERVICE\n"
                for p in sorted(ports):
                    svc = self._service_name(p)
                    result += f"{p:5}/tcp  open     {svc}\n"
                result += "\n"
        result += (f"Nmap done: 256 IP addresses ({hosts_found} hosts up) "
                   f"scanned in {random.uniform(1.5, 5.0):.2f} seconds\n")
        return result

    def _service_name(self, port: int) -> str:
        services = {21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "domain",
                    80: "http", 110: "pop3", 111: "rpcbind", 135: "msrpc",
                    139: "netbios-ssn", 143: "imap", 443: "https", 445: "microsoft-ds",
                    993: "imaps", 995: "pop3s", 1433: "ms-sql-s", 1521: "oracle-tns",
                    2049: "nfs", 3306: "mysql", 3389: "ms-wbt-server",
                    5432: "postgresql", 5900: "vnc", 5985: "wsman", 6379: "redis",
                    8080: "http-proxy", 8443: "https-alt", 9090: "zeus-admin",
                    27017: "mongod"}
        return services.get(port, "unknown")

    def get_stats(self) -> dict:
        return {
            "interfaces": list(self.interfaces.keys()),
            "routes": len(self.routes),
            "arp_entries": len(self.arp_table),
            "dns_cache": len(self.dns_cache),
            "hosts": len(self.hosts),
        }

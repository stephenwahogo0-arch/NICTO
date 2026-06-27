"""Virtual File System — Kali Linux directory structure.

Simulates the full Kali Linux filesystem hierarchy with:
- /root, /home, /etc, /var, /usr, /opt, /tmp, /proc
- /usr/bin with all tool symlinks
- /etc/apt/sources.list and configs
- /var/log for tool output logs
- NICTO-specific /opt/nikto directory
"""

from __future__ import annotations
import os
import time
import json
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from datetime import datetime


class FileType:
    FILE = "file"
    DIR = "dir"
    SYMLINK = "symlink"
    MOUNT = "mount"


@dataclass
class VNode:
    """A virtual filesystem node."""
    name: str
    type: str = FileType.FILE
    content: str = ""
    permissions: str = "rw-r--r--"
    owner: str = "root"
    group: str = "root"
    size: int = 0
    created: float = 0.0
    modified: float = 0.0
    children: Dict[str, 'VNode'] = field(default_factory=dict)
    symlink_target: Optional[str] = None

    def __post_init__(self):
        now = time.time()
        if not self.created:
            self.created = now
        if not self.modified:
            self.modified = now


class VirtualFileSystem:
    """Kali Linux virtual filesystem.

    Maintains a full directory tree and provides file operations
    (ls, cd, cat, touch, mkdir, rm, cp, mv, chmod, find, grep).
    """

    DIRS_KALI = [
        "/root", "/root/Desktop", "/root/Documents", "/root/Downloads",
        "/root/tools", "/root/reports", "/root/wordlists",
        "/home", "/home/nikto", "/home/nikto/Desktop",
        "/etc", "/etc/apt", "/etc/network", "/etc/samba",
        "/etc/apache2", "/etc/ssh", "/etc/nmap", "/etc/metasploit",
        "/etc/wireshark", "/etc/burp", "/etc/sqlmap",
        "/var", "/var/log", "/var/log/nikto", "/var/log/audit",
        "/var/log/apache2", "/var/log/nginx",
        "/var/www", "/var/www/html",
        "/var/lib", "/var/lib/metasploit", "/var/lib/dpkg",
        "/var/cache", "/var/cache/apt",
        "/usr", "/usr/bin", "/usr/share", "/usr/local", "/usr/local/bin",
        "/usr/share/nmap", "/usr/share/metasploit",
        "/usr/share/wordlists", "/usr/share/exploitdb",
        "/usr/share/hashcat", "/usr/share/john",
        "/usr/share/sqlmap", "/usr/share/hydra",
        "/usr/share/burpsuite", "/usr/share/wireshark",
        "/usr/share/aircrack-ng", "/usr/share/social-engineer-toolkit",
        "/opt", "/opt/nikto", "/opt/nikto/tools", "/opt/nikto/scripts",
        "/opt/nikto/plugins", "/opt/nikto/config",
        "/opt/nikto/reports", "/opt/nikto/targets",
        "/tmp", "/tmp/nikto_workspace",
        "/proc", "/sys", "/dev",
        "/boot", "/lib", "/lib/modules",
        "/mnt", "/mnt/share",
        "/media", "/media/cdrom",
        "/srv", "/srv/ftp", "/srv/http",
        "/run", "/run/lock",
    ]

    FILES_KALI = {
        "/etc/hostname": "nikto-kali\n",
        "/etc/hosts": "127.0.0.1\tlocalhost\n127.0.1.1\tnikto-kali\n::1\t\tlocalhost\n",
        "/etc/hostname": "nikto-kali\n",
        "/etc/issue": "Kali GNU/Linux Rolling \\n \\l\n",
        "/etc/debian_version": "Kali Linux Rolling\n",
        "/etc/os-release": 'PRETTY_NAME="Kali GNU/Linux Rolling"\nNAME="Kali GNU/Linux"\nID=kali\nVERSION_ID="2024.1"\n',
        "/etc/resolv.conf": "nameserver 8.8.8.8\nnameserver 8.8.4.4\n",
        "/etc/network/interfaces": "auto lo\niface lo inet loopback\n\nauto eth0\niface eth0 inet dhcp\n",
        "/etc/apt/sources.list": "deb http://http.kali.org/kali kali-rolling main contrib non-free non-free-firmware\ndeb-src http://http.kali.org/kali kali-rolling main contrib non-free non-free-firmware\n",
        "/etc/ssh/sshd_config": "Port 22\nPermitRootLogin yes\nPasswordAuthentication yes\n",
        "/etc/nmap/nmap.conf": "# Nmap config\n",
        "/etc/shells": "/bin/bash\n/bin/sh\n/usr/bin/zsh\n",
        "/root/.bashrc": 'export PS1="\\[\\033[01;31m\\]┌──(\\[\\033[01;32m\\]nikto\\[\\033[01;31m\\])─(\\[\\033[01;34m\\]\\w\\[\\033[01;31m\\])\n\\[\\033[01;31m\\]└──\\[\\033[00m\\]\\$ "\nalias ll="ls -la"\nalias la="ls -A"\n',
        "/root/.bash_profile": "source ~/.bashrc\n",
        "/root/.bash_logout": "clear\n",
        "/root/Desktop/README.txt": "NICTO Virtual Kali Linux\n=========================\nExclusive cyber operations environment.\nAll tools pre-installed and ready.\nType 'nikto-help' for NICTO-specific commands.\n",
        "/home/nikto/.bashrc": 'export PS1="\\[\\033[01;31m\\]┌──(\\[\\033[01;32m\\]nikto\\[\\033[01;31m\\])─(\\[\\033[01;34m\\]\\w\\[\\033[01;31m\\])\n\\[\\033[01;31m\\]└──\\[\\033[00m\\]\\$ "\n',
        "/opt/nikto/config/nikto.conf": "# NICTO Virtual Kali Configuration\nversion: 8.2.0\nenvironment: virtual_kali\nmode: offensive\nintegration: full\n",
        "/opt/nikto/README": "NICTO Virtual Kali Linux — For exclusive NICTO use only.\n",
    }

    def __init__(self):
        self.root: VNode = VNode("/", type=FileType.DIR, permissions="rwxr-xr-x")
        self._current_path = "/root"
        self._build_tree()

    def _build_tree(self):
        """Construct the full Kali directory tree."""
        for path in self.DIRS_KALI:
            self._ensure_dir(path)
        for path, content in self.FILES_KALI.items():
            self._write_file(path, content)

    def _ensure_dir(self, path: str) -> VNode:
        parts = [p for p in path.split("/") if p]
        node = self.root
        for part in parts:
            if part not in node.children:
                node.children[part] = VNode(part, type=FileType.DIR, permissions="rwxr-xr-x")
            node = node.children[part]
        return node

    def _resolve(self, path: str) -> Optional[VNode]:
        if not path:
            return None
        if path == "/":
            return self.root
        parts = [p for p in path.split("/") if p]
        node = self.root
        for part in parts:
            if part == "..":
                continue
            if part == ".":
                continue
            if part in node.children:
                node = node.children[part]
                if node.type == FileType.SYMLINK and node.symlink_target:
                    return self._resolve(node.symlink_target)
            else:
                return None
        return node

    def _resolve_parent(self, path: str) -> Tuple[Optional[VNode], str]:
        parts = [p for p in path.split("/") if p]
        if not parts:
            return self.root, ""
        parent_path = "/" + "/".join(parts[:-1])
        name = parts[-1]
        parent = self._resolve(parent_path) if parts[:-1] else self.root
        return parent, name

    def _write_file(self, path: str, content: str):
        parent, name = self._resolve_parent(path)
        if parent:
            parent.children[name] = VNode(name, type=FileType.FILE, content=content,
                                          size=len(content), permissions="rw-r--r--")

    def pwd(self) -> str:
        return self._current_path

    def cd(self, path: str) -> Tuple[bool, str]:
        if path == "..":
            parts = [p for p in self._current_path.split("/") if p]
            self._current_path = "/" + "/".join(parts[:-1]) if parts else "/"
            return True, ""
        if path.startswith("/"):
            target = path
        else:
            target = os.path.normpath(self._current_path + "/" + path).replace("\\", "/")
        node = self._resolve(target)
        if node and node.type == FileType.DIR:
            self._current_path = target
            return True, ""
        return False, f"cd: {path}: No such directory"

    def ls(self, path: Optional[str] = None, show_all: bool = False, long: bool = False) -> List[str]:
        target = path if path else self._current_path
        node = self._resolve(target)
        if not node:
            return [f"ls: {target}: No such file or directory"]
        if node.type == FileType.FILE:
            if long:
                return [f"{node.permissions} 1 {node.owner} {node.group} {node.size} {self._fmt_time(node.modified)} {node.name}"]
            return [node.name]
        results = []
        for name, child in sorted(node.children.items()):
            if not show_all and name.startswith("."):
                continue
            if long:
                prefix = "d" if child.type == FileType.DIR else "l" if child.type == FileType.SYMLINK else "-"
                results.append(f"{prefix}{child.permissions} 1 {child.owner} {child.group} {child.size} {self._fmt_time(child.modified)} {name}")
            else:
                suffix = "/" if child.type == FileType.DIR else "@" if child.type == FileType.SYMLINK else ""
                results.append(f"{name}{suffix}")
        return results

    def cat(self, path: str) -> Tuple[bool, str]:
        node = self._resolve(path)
        if not node:
            return False, f"cat: {path}: No such file"
        if node.type == FileType.DIR:
            return False, f"cat: {path}: Is a directory"
        return True, node.content

    def touch(self, path: str) -> Tuple[bool, str]:
        parent, name = self._resolve_parent(path)
        if not parent:
            return False, f"touch: {path}: No such directory"
        if name in parent.children:
            parent.children[name].modified = time.time()
        else:
            parent.children[name] = VNode(name, content="", size=0)
        return True, ""

    def mkdir(self, path: str) -> Tuple[bool, str]:
        parent, name = self._resolve_parent(path)
        if not parent:
            return False, f"mkdir: {path}: No such directory"
        if name in parent.children:
            return False, f"mkdir: {name}: File exists"
        parent.children[name] = VNode(name, type=FileType.DIR, permissions="rwxr-xr-x")
        return True, ""

    def rm(self, path: str, recursive: bool = False) -> Tuple[bool, str]:
        parent, name = self._resolve_parent(path)
        if not parent or name not in parent.children:
            return False, f"rm: {path}: No such file"
        child = parent.children[name]
        if child.type == FileType.DIR and not recursive:
            return False, f"rm: {path}: Is a directory (use -r)"
        del parent.children[name]
        return True, ""

    def cp(self, src: str, dst: str) -> Tuple[bool, str]:
        node = self._resolve(src)
        if not node:
            return False, f"cp: {src}: No such file"
        dst_parent, dst_name = self._resolve_parent(dst)
        if not dst_parent:
            return False, f"cp: {dst}: No such directory"
        new_node = VNode(dst_name, type=node.type, content=node.content,
                         permissions=node.permissions, size=node.size)
        dst_parent.children[dst_name] = new_node
        return True, ""

    def mv(self, src: str, dst: str) -> Tuple[bool, str]:
        ok, msg = self.cp(src, dst)
        if not ok:
            return ok, msg
        self.rm(src, recursive=True)
        return True, ""

    def chmod(self, path: str, mode: str) -> Tuple[bool, str]:
        node = self._resolve(path)
        if not node:
            return False, f"chmod: {path}: No such file"
        node.permissions = mode
        return True, ""

    def find(self, pattern: str, start_path: str = "/") -> List[str]:
        results = []
        self._find_recursive(self._resolve(start_path) or self.root, pattern, start_path, results)
        return results

    def _find_recursive(self, node: VNode, pattern: str, current_path: str, results: List[str]):
        if pattern in node.name:
            results.append(current_path)
        for name, child in node.children.items():
            child_path = current_path.rstrip("/") + "/" + name
            self._find_recursive(child, pattern, child_path, results)

    def grep(self, pattern: str, path: str) -> List[str]:
        node = self._resolve(path)
        if not node or node.type != FileType.FILE:
            return []
        return [line for line in node.content.split("\n") if pattern in line]

    def write(self, path: str, content: str):
        parent, name = self._resolve_parent(path)
        if parent:
            parent.children[name] = VNode(name, content=content, size=len(content),
                                          permissions="rw-r--r--")

    def read(self, path: str) -> Optional[str]:
        node = self._resolve(path)
        if node and node.type == FileType.FILE:
            return node.content
        return None

    def exists(self, path: str) -> bool:
        return self._resolve(path) is not None

    def is_dir(self, path: str) -> bool:
        node = self._resolve(path)
        return node is not None and node.type == FileType.DIR

    def is_file(self, path: str) -> bool:
        node = self._resolve(path)
        return node is not None and node.type == FileType.FILE

    def get_size(self, path: str) -> int:
        node = self._resolve(path)
        if node:
            if node.type == FileType.DIR:
                return self._dir_size(node)
            return node.size
        return 0

    def _dir_size(self, node: VNode) -> int:
        total = 0
        for child in node.children.values():
            if child.type == FileType.DIR:
                total += self._dir_size(child)
            else:
                total += child.size
        return total

    def _fmt_time(self, ts: float) -> str:
        return datetime.fromtimestamp(ts).strftime("%b %d %H:%M")

    def get_absolute_path(self, path: str) -> str:
        if path.startswith("/"):
            return path
        return os.path.normpath(self._current_path + "/" + path).replace("\\", "/")

    def get_stats(self) -> dict:
        total_files = 0
        total_dirs = 0
        def count(node):
            nonlocal total_files, total_dirs
            if node.type == FileType.DIR:
                total_dirs += 1
                for c in node.children.values():
                    count(c)
            else:
                total_files += 1
        count(self.root)
        return {
            "total_files": total_files,
            "total_dirs": total_dirs,
            "size_bytes": self._dir_size(self.root),
            "current_dir": self._current_path,
        }

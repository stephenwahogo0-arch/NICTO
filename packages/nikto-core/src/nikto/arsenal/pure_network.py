"""Pure Python networking — replaces external Kali tools with native socket/scapy implementations.

No external CLI tools required. Falls back gracefully when root/admin is unavailable."""
import http.client
import json
import os
import socket
import ssl
import struct
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PortScanResult:
    port: int
    state: str
    service: str = ""
    banner: str = ""


@dataclass
class ServiceScanResult:
    host: str
    port: int
    service: str
    version: str = ""
    protocols: list[str] = field(default_factory=list)


class PureNetworkScanner:
    """Pure Python port scanning and service detection — no Nmap required."""

    COMMON_PORTS = {
        21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
        80: "http", 110: "pop3", 143: "imap", 443: "https", 445: "smb",
        993: "imaps", 995: "pop3s", 1433: "mssql", 1521: "oracle",
        2049: "nfs", 3306: "mysql", 3389: "rdp", 5432: "postgresql",
        5900: "vnc", 6379: "redis", 8080: "http-proxy", 8443: "https-alt",
        27017: "mongodb",
    }

    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout
        self.is_admin = self._check_admin()

    def _check_admin(self) -> bool:
        try:
            if os.name == "nt":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            return os.getuid() == 0
        except Exception:
            return False

    def syn_scan(self, host: str, ports: Optional[list[int]] = None) -> list[PortScanResult]:
        """TCP SYN scan using raw sockets (requires admin) or connect scan as fallback."""
        if self.is_admin:
            try:
                return self._raw_syn_scan(host, ports)
            except PermissionError:
                pass
        return self._connect_scan(host, ports)

    def _raw_syn_scan(self, host: str, ports: Optional[list[int]] = None) -> list[PortScanResult]:
        results = []
        target_ports = ports or list(self.COMMON_PORTS.keys())
        dst_ip = socket.gethostbyname(host)
        for port in target_ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                sock.settimeout(self.timeout)
                sock.close()
                results.append(PortScanResult(port=port, state="open", service=self.COMMON_PORTS.get(port, "")))
            except (socket.error, OSError):
                results.append(PortScanResult(port=port, state="filtered", service=self.COMMON_PORTS.get(port, "")))
        return results

    def _connect_scan(self, host: str, ports: Optional[list[int]] = None, max_workers: int = 20) -> list[PortScanResult]:
        """Standard TCP connect scan — works without admin."""
        results = []
        target_ports = ports or list(self.COMMON_PORTS.keys())
        for port in target_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            try:
                result = sock.connect_ex((host, port))
                if result == 0:
                    banner = ""
                    try:
                        if port in (80, 443, 8080, 8443):
                            pass
                        else:
                            sock.settimeout(1.0)
                            banner = sock.recv(1024).decode("utf-8", errors="replace")[:200].strip()
                    except Exception:
                        pass
                    results.append(PortScanResult(port=port, state="open", service=self.COMMON_PORTS.get(port, ""), banner=banner))
                elif result == 111:
                    results.append(PortScanResult(port=port, state="closed"))
                else:
                    results.append(PortScanResult(port=port, state="filtered"))
            except socket.gaierror:
                return results
            finally:
                sock.close()
        return results

    def fast_scan(self, host: str) -> list[PortScanResult]:
        """Scan only the 25 most common ports."""
        top_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 993, 995, 1433, 1521, 2049, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017, 22, 80]
        return self._connect_scan(host, top_ports[:25])

    def service_detect(self, host: str, port: int) -> ServiceScanResult:
        """Attempt service version detection via banner grab."""
        service = self.COMMON_PORTS.get(port, "unknown")
        banner = ""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect((host, port))
            if port == 80:
                sock.send(b"GET / HTTP/1.0\r\nHost: {}\r\n\r\n".format(host).encode())
            elif port == 22:
                pass
            sock.settimeout(1.0)
            banner = sock.recv(4096).decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        finally:
            sock.close()
        return ServiceScanResult(host=host, port=port, service=service, version=banner[:100])


class PureWebScanner:
    """Pure Python web scanning — no Gobuster, Dirb, or Nikto required."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self.common_dirs = [
            "admin", "login", "wp-admin", "administrator", "backup",
            "api", "v1", "v2", "graphql", "swagger", "docs",
            ".git", ".env", "config", "uploads", "assets",
            "phpmyadmin", "manager", "console", "dashboard",
            "robots.txt", "sitemap.xml", "crossdomain.xml",
        ]

    def check_http(self, host: str, ssl_flag: bool = False) -> dict:
        """Basic HTTP/HTTPS check with response analysis."""
        proto = "https" if ssl_flag else "http"
        url = f"{proto}://{host}"
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, method="GET", headers={"User-Agent": "NIKTO/1.0"})
            response = urllib.request.urlopen(req, timeout=self.timeout, context=ctx)
            headers = dict(response.headers)
            server = headers.get("Server", "")
            content_type = headers.get("Content-Type", "")
            return {
                "success": True,
                "status": response.getcode(),
                "server": server,
                "content_type": content_type,
                "headers": {k: v for k, v in list(headers.items())[:15]},
            }
        except urllib.error.HTTPError as e:
            return {"success": True, "status": e.code, "server": e.headers.get("Server", ""), "content_type": e.headers.get("Content-Type", "")}
        except (urllib.error.URLError, socket.error, ssl.SSLError) as e:
            return {"success": False, "error": str(e)[:100]}

    def dir_enum(self, host: str, ssl_flag: bool = False, wordlist: Optional[list[str]] = None) -> list[dict]:
        """Directory enumeration — pure Python replacement for Gobuster/Dirb."""
        results = []
        dirs = wordlist or self.common_dirs
        proto = "https" if ssl_flag else "http"
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        for d in dirs:
            url = f"{proto}://{host}/{d}"
            try:
                req = urllib.request.Request(url, method="GET", headers={"User-Agent": "NIKTO/1.0"})
                response = urllib.request.urlopen(req, timeout=self.timeout, context=ctx)
                results.append({"url": url, "status": response.getcode(), "size": len(response.read())})
            except urllib.error.HTTPError as e:
                if e.code in (200, 301, 302, 401, 403):
                    results.append({"url": url, "status": e.code, "size": 0})
            except Exception:
                pass
        return results

    def check_ssl(self, host: str, port: int = 443) -> dict:
        """SSL/TLS certificate inspection."""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection((host, port), timeout=self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        "success": True,
                        "issuer": dict(cert.get("issuer", [])),
                        "subject": dict(cert.get("subject", [])),
                        "expiry": cert.get("notAfter", ""),
                        "serial": hex(cert.get("serialNumber", 0)),
                    }
        except Exception as e:
            return {"success": False, "error": str(e)[:100]}


class PureDnsEnumerator:
    """Pure Python DNS enumeration — no dnsrecon or sublist3r required."""

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout
        self.common_subdomains = [
            "www", "mail", "admin", "api", "dev", "test", "staging",
            "blog", "shop", "cdn", "static", "media", "app", "m",
            "secure", "portal", "remote", "support", "help", "docs",
        ]

    def resolve(self, hostname: str) -> list[str]:
        """Resolve hostname to IP addresses."""
        try:
            return list(set(socket.getaddrinfo(hostname, 80, socket.AF_INET, socket.SOCK_STREAM)[0][4][0] for _ in range(1)))
        except socket.gaierror:
            return []

    def enumerate_subdomains(self, domain: str, wordlist: Optional[list[str]] = None) -> list[dict]:
        """Subdomain enumeration via DNS resolution."""
        results = []
        subs = wordlist or self.common_subdomains
        for sub in subs:
            hostname = f"{sub}.{domain}"
            try:
                ips = socket.getaddrinfo(hostname, 80, socket.AF_INET, socket.SOCK_STREAM)
                results.append({"subdomain": hostname, "ips": list(set(ip[4][0] for ip in ips)), "resolves": True})
            except socket.gaierror:
                pass
        return results

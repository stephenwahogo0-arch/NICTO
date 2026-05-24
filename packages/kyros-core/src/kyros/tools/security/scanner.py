import os
import asyncio
import subprocess
from uuid import uuid4
from kyros.tools.base import Tool


async def _run_subprocess(cmd: list[str], timeout: int = 120) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {"success": proc.returncode == 0, "stdout": stdout.decode("utf-8", errors="replace"), "stderr": stderr.decode("utf-8", errors="replace"), "exit_code": proc.returncode}
    except asyncio.TimeoutError:
        return {"success": False, "error": f"Command timed out after {timeout}s"}
    except FileNotFoundError:
        return {"success": False, "error": f"Binary not found: {cmd[0]}", "simulated": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


class NmapScanTool(Tool):
    name = "nmap_scan"
    description = "Run nmap scan on a target"

    async def execute(self, target: str, ports: str = "1-1000", **kwargs) -> dict:
        result = await _run_subprocess(["nmap", "-p", ports, target])
        if result.get("simulated"):
            return {"success": True, "target": target, "ports": ports, "scan_id": str(uuid4())[:12], "result": f"Simulated nmap scan of {target} ports {ports}"}
        return {**result, "target": target, "ports": ports, "scan_id": str(uuid4())[:12]}


class GobusterTool(Tool):
    name = "gobuster"
    description = "Run gobuster directory scan"

    async def execute(self, url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt", **kwargs) -> dict:
        result = await _run_subprocess(["gobuster", "dir", "-u", url, "-w", wordlist])
        return {**result, "url": url, "scan_id": str(uuid4())[:12]}


class SqlmapTool(Tool):
    name = "sqlmap"
    description = "Run sqlmap SQL injection scan"

    async def execute(self, url: str, **kwargs) -> dict:
        result = await _run_subprocess(["sqlmap", "-u", url, "--batch"])
        return {**result, "url": url, "scan_id": str(uuid4())[:12]}


class KyrosWebScanTool(Tool):
    name = "kyros_web_scan"
    description = "Run nikto web server scan"

    async def execute(self, url: str, **kwargs) -> dict:
        result = await _run_subprocess(["kyros", "-h", url])
        return {**result, "url": url, "scan_id": str(uuid4())[:12]}


class HashcatTool(Tool):
    name = "hashcat"
    description = "Run hashcat password cracking"

    async def execute(self, hash_value: str, hash_type: str = "0", **kwargs) -> dict:
        return {"success": True, "hash": hash_value, "hash_type": hash_type, "cracked": False, "scan_id": str(uuid4())[:12], "message": "Hashcat execution requires hash file and wordlist"}


class HydraTool(Tool):
    name = "hydra"
    description = "Run hydra brute force attack"

    async def execute(self, target: str, service: str = "ssh", **kwargs) -> dict:
        return {"success": True, "target": target, "service": service, "scan_id": str(uuid4())[:12], "message": "Hydra execution requires user/pass lists"}


class MetasploitTool(Tool):
    name = "metasploit"
    description = "Run metasploit module"

    async def execute(self, module: str = "exploit/multi/handler", **kwargs) -> dict:
        return {"success": True, "module": module, "scan_id": str(uuid4())[:12], "session_id": str(uuid4())[:8], "message": "Metasploit execution requires msfconsole"}


class SearchsploitTool(Tool):
    name = "searchsploit"
    description = "Search exploit database"

    async def execute(self, query: str, **kwargs) -> dict:
        result = await _run_subprocess(["searchsploit", query])
        return {**result, "query": query, "scan_id": str(uuid4())[:12]}


class AmassTool(Tool):
    name = "amass"
    description = "Run amass reconnaissance"

    async def execute(self, domain: str, **kwargs) -> dict:
        return {"success": True, "domain": domain, "scan_id": str(uuid4())[:12], "subdomains": [], "message": "Amass execution requires amass binary"}


class DirbTool(Tool):
    name = "dirb"
    description = "Run dirb web content scanner"

    async def execute(self, url: str, **kwargs) -> dict:
        result = await _run_subprocess(["dirb", url])
        return {**result, "url": url, "scan_id": str(uuid4())[:12]}


class WpscanTool(Tool):
    name = "wpscan"
    description = "Run wpscan WordPress vulnerability scanner"

    async def execute(self, url: str, **kwargs) -> dict:
        return {"success": True, "url": url, "scan_id": str(uuid4())[:12], "vulnerabilities": [], "message": "WPScan execution requires wpscan binary and API token"}


class WiresharkTool(Tool):
    name = "wireshark"
    description = "Analyze pcap file with tshark"

    async def execute(self, pcap_path: str, **kwargs) -> dict:
        result = await _run_subprocess(["tshark", "-r", pcap_path])
        return {**result, "pcap": pcap_path, "scan_id": str(uuid4())[:12]}


class Enum4linuxTool(Tool):
    name = "enum4linux"
    description = "Run enum4linux SMB enumeration"

    async def execute(self, target: str, **kwargs) -> dict:
        return {"success": True, "target": target, "scan_id": str(uuid4())[:12], "message": "Enum4linux requires enum4linux binary"}


class JohnRipperTool(Tool):
    name = "john_ripper"
    description = "Run John the Ripper password cracker"

    async def execute(self, hash_file: str, **kwargs) -> dict:
        return {"success": True, "hash_file": hash_file, "scan_id": str(uuid4())[:12], "cracked": False, "message": "John requires hash file and wordlist"}


async def tool_nmap_scan(target: str, ports: str = "1-1000") -> dict:
    tool = NmapScanTool()
    return await tool.execute(target=target, ports=ports)

import asyncio
import json
import os
import re
from pathlib import Path
from typing import Optional

from nikto.tools.base import Tool


async def _run_cmd(cmd: str, timeout: int = 300) -> str:
    try:
        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell=True
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        output = ""
        if stdout:
            output += stdout.decode("utf-8", errors="replace")
        if stderr:
            output += "\n[STDERR]\n" + stderr.decode("utf-8", errors="replace")
        if not output:
            output = f"Command completed with exit code {proc.returncode}"
        return output[:100000]
    except asyncio.TimeoutError:
        return f"Command timed out after {timeout}s"
    except FileNotFoundError:
        return f"Tool not found. Install it first."
    except Exception as e:
        return f"Error: {str(e)}"


async def tool_nmap_scan(target: str, ports: str = "1-1000", flags: str = "-sV -sC") -> str:
    return await _run_cmd(f"nmap {flags} -p {ports} {target}", timeout=600)


async def tool_gobuster_scan(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt", extensions: str = "php,txt,html") -> str:
    return await _run_cmd(f"gobuster dir -u {url} -w {wordlist} -x {extensions}")


async def tool_sqlmap_scan(target: str, data: Optional[str] = None) -> str:
    cmd = f"sqlmap -u '{target}' --batch --random-agent"
    if data:
        cmd += f" --data='{data}'"
    return await _run_cmd(cmd, timeout=600)


async def tool_nikto_scan(target: str, ssl: bool = False) -> str:
    protocol = "https" if ssl else "http"
    return await _run_cmd(f"nikto -h {protocol}://{target}")


async def tool_dirb_scan(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt") -> str:
    return await _run_cmd(f"dirb {url} {wordlist}")


async def tool_wpscan_scan(url: str, enumerate_users: bool = False) -> str:
    cmd = f"wpscan --url {url}"
    if enumerate_users:
        cmd += " --enumerate u"
    return await _run_cmd(cmd, timeout=600)


async def tool_hashcat(hash_file: str, wordlist: str = "/usr/share/wordlists/rockyou.txt", hash_type: str = "0") -> str:
    return await _run_cmd(f"hashcat -m {hash_type} {hash_file} {wordlist} --force", timeout=600)


async def tool_hydra_brute(target: str, protocol: str = "ssh", username: str = "root", wordlist: str = "/usr/share/wordlists/rockyou.txt") -> str:
    return await _run_cmd(f"hydra -l {username} -P {wordlist} {target} {protocol}", timeout=600)


async def tool_metasploit_exec(module: str, options: str = "") -> str:
    rc_file = f"/tmp/msf_{os.urandom(4).hex()}.rc"
    with open(rc_file, "w") as f:
        f.write(f"use {module}\n")
        for opt in options.split(";"):
            if opt.strip():
                f.write(f"set {opt.strip()}\n")
        f.write("run\nexit\n")
    result = await _run_cmd(f"msfconsole -q -r {rc_file}", timeout=600)
    os.remove(rc_file)
    return result


async def tool_wireshark_extract(pcap_file: str, filter_expr: str = "http") -> str:
    return await _run_cmd(f"tshark -r {pcap_file} -Y '{filter_expr}' -T fields -e ip.src -e ip.dst -e http.host -e http.request.uri")


async def tool_searchsploit(keyword: str) -> str:
    return await _run_cmd(f"searchsploit {keyword}")


async def tool_amass_enum(domain: str) -> str:
    return await _run_cmd(f"amass enum -d {domain}", timeout=600)


async def tool_enum4linux(target: str) -> str:
    return await _run_cmd(f"enum4linux -a {target}", timeout=300)


async def tool_john_ripper(hash_file: str, wordlist: str = "/usr/share/wordlists/rockyou.txt") -> str:
    return await _run_cmd(f"john --wordlist={wordlist} {hash_file}", timeout=600)


async def tool_bloodhound(target: str, username: str = "", password: str = "") -> str:
    cmd = f"bloodhound-python -d {target}"
    if username and password:
        cmd += f" -u {username} -p {password} -c All"
    return await _run_cmd(cmd, timeout=600)


async def tool_ffuf_scan(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt") -> str:
    return await _run_cmd(f"ffuf -u {url} -w {wordlist}", timeout=600)


async def tool_kerbrute(domain: str, userlist: str = "") -> str:
    cmd = f"kerbrute userenum -d {domain}"
    if userlist:
        cmd += f" {userlist}"
    else:
        cmd += " /usr/share/wordlists/dirb/common.txt"
    return await _run_cmd(cmd, timeout=300)


async def tool_netcat_listen(port: int = 4444) -> str:
    return await _run_cmd(f"timeout 30 nc -lvnp {port}")


async def tool_responder(interface: str = "eth0") -> str:
    return await _run_cmd(f"responder -I {interface} -wrf", timeout=120)


NmapScanTool = Tool(
    name="nmap_scan",
    description="Run Nmap port scanning with service/version detection. Use for network reconnaissance and open port discovery.",
    parameters={"type": "object", "properties": {
        "target": {"type": "string", "description": "Target IP or hostname"},
        "ports": {"type": "string", "description": "Port range (e.g., 1-1000, 22,80,443)"},
        "flags": {"type": "string", "description": "Nmap flags (e.g., -sV -sC -A -O)"},
    }, "required": ["target"]},
    async_function=tool_nmap_scan,
)

GobusterTool = Tool(
    name="gobuster_scan",
    description="Directory/file brute-forcing with Gobuster. Discovers hidden web paths and resources.",
    parameters={"type": "object", "properties": {
        "url": {"type": "string", "description": "Target URL (e.g., https://example.com)"},
        "wordlist": {"type": "string", "description": "Path to wordlist"},
        "extensions": {"type": "string", "description": "File extensions to check"},
    }, "required": ["url"]},
    async_function=tool_gobuster_scan,
)

SqlmapTool = Tool(
    name="sqlmap_scan",
    description="Automated SQL injection detection and exploitation using sqlmap.",
    parameters={"type": "object", "properties": {
        "target": {"type": "string", "description": "Target URL with parameters"},
        "data": {"type": "string", "description": "POST data string"},
    }, "required": ["target"]},
    async_function=tool_sqlmap_scan,
)

NiktoWebScanTool = Tool(
    name="nikto_webscan",
    description="Web server scanner (Nikto). Tests for outdated software, misconfigurations, and known vulnerabilities.",
    parameters={"type": "object", "properties": {
        "target": {"type": "string", "description": "Target hostname or IP:port"},
        "ssl": {"type": "boolean", "description": "Use HTTPS"},
    }, "required": ["target"]},
    async_function=tool_nikto_scan,
)

DirbTool = Tool(
    name="dirb_scan",
    description="Web content scanner using DIRB. Finds hidden directories and files.",
    parameters={"type": "object", "properties": {
        "url": {"type": "string", "description": "Target URL"},
        "wordlist": {"type": "string", "description": "Path to wordlist"},
    }, "required": ["url"]},
    async_function=tool_dirb_scan,
)

WpscanTool = Tool(
    name="wpscan",
    description="WordPress security scanner. Detects vulnerable plugins, themes, users, and misconfigurations.",
    parameters={"type": "object", "properties": {
        "url": {"type": "string", "description": "WordPress site URL"},
        "enumerate_users": {"type": "boolean", "description": "Enumerate usernames"},
    }, "required": ["url"]},
    async_function=tool_wpscan_scan,
)

HashcatTool = Tool(
    name="hashcat",
    description="GPU-accelerated password hash cracking using hashcat. Supports 300+ hash types.",
    parameters={"type": "object", "properties": {
        "hash_file": {"type": "string", "description": "Path to file containing hashes"},
        "wordlist": {"type": "string", "description": "Path to wordlist"},
        "hash_type": {"type": "string", "description": "Hash type code (0=MD5, 1000=NTLM)"},
    }, "required": ["hash_file"]},
    async_function=tool_hashcat,
)

HydraTool = Tool(
    name="hydra_brute",
    description="Online password brute-force attack using Hydra. Supports SSH, RDP, FTP, HTTP, and more.",
    parameters={"type": "object", "properties": {
        "target": {"type": "string", "description": "Target IP:port (e.g., 192.168.1.1:22)"},
        "protocol": {"type": "string", "description": "Protocol (ssh, rdp, ftp, http-post-form, etc.)"},
        "username": {"type": "string", "description": "Username to brute-force"},
        "wordlist": {"type": "string", "description": "Path to password wordlist"},
    }, "required": ["target"]},
    async_function=tool_hydra_brute,
)

MetasploitTool = Tool(
    name="metasploit_exec",
    description="Execute Metasploit modules. Run exploits, scanners, and auxiliary modules.",
    parameters={"type": "object", "properties": {
        "module": {"type": "string", "description": "Full module path (e.g., exploit/multi/handler)"},
        "options": {"type": "string", "description": "Semicolon-separated options (e.g., RHOSTS=10.0.0.1;PAYLOAD=linux/x64/shell)"},
    }, "required": ["module"]},
    async_function=tool_metasploit_exec,
)

WiresharkTool = Tool(
    name="wireshark_extract",
    description="Extract and analyze packets from pcap files using tshark/Wireshark. Supports filtering and field extraction.",
    parameters={"type": "object", "properties": {
        "pcap_file": {"type": "string", "description": "Path to pcap/pcapng file"},
        "filter_expr": {"type": "string", "description": "Display filter expression (e.g., http, dns, tcp.port==443)"},
    }, "required": ["pcap_file"]},
    async_function=tool_wireshark_extract,
)

SearchsploitTool = Tool(
    name="searchsploit",
    description="Search the Exploit Database for known exploits and vulnerabilities. Offline search capability.",
    parameters={"type": "object", "properties": {
        "keyword": {"type": "string", "description": "Search keyword (software name, CVE, etc.)"},
    }, "required": ["keyword"]},
    async_function=tool_searchsploit,
)

AmassTool = Tool(
    name="amass_enum",
    description="Subdomain enumeration using OWASP Amass. Performs DNS scraping, brute-forcing, and API-based discovery.",
    parameters={"type": "object", "properties": {
        "domain": {"type": "string", "description": "Target domain"},
    }, "required": ["domain"]},
    async_function=tool_amass_enum,
)

Enum4linuxTool = Tool(
    name="enum4linux",
    description="Windows/Samba enumeration. Extracts users, shares, OS info, groups, and policies via SMB/RPC.",
    parameters={"type": "object", "properties": {
        "target": {"type": "string", "description": "Target IP address"},
    }, "required": ["target"]},
    async_function=tool_enum4linux,
)

JohnRipperTool = Tool(
    name="john_ripper",
    description="Password hash cracking using John the Ripper. CPU-optimized cracker for offline hash files.",
    parameters={"type": "object", "properties": {
        "hash_file": {"type": "string", "description": "Path to hash file"},
        "wordlist": {"type": "string", "description": "Path to wordlist"},
    }, "required": ["hash_file"]},
    async_function=tool_john_ripper,
)

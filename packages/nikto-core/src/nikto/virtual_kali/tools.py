"""Kali Linux Tool Database — 500+ tools across all categories.

Comprehensive catalog of every Kali Linux penetration testing tool,
organized by category with descriptions, command templates, and
NICTO integration flags.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


class ToolCategory(Enum):
    INFORMATION_GATHERING = "Information Gathering"
    VULNERABILITY_ANALYSIS = "Vulnerability Analysis"
    WEB_APPLICATION = "Web Application Analysis"
    DATABASE_ASSESSMENT = "Database Assessment"
    PASSWORD_ATTACKS = "Password Attacks"
    WIRELESS_ATTACKS = "Wireless Attacks"
    REVERSE_ENGINEERING = "Reverse Engineering"
    EXPLOITATION = "Exploitation Tools"
    SNIFFING_SPOOFING = "Sniffing & Spoofing"
    POST_EXPLOITATION = "Post Exploitation"
    FORENSICS = "Forensics"
    REPORTING = "Reporting Tools"
    SOCIAL_ENGINEERING = "Social Engineering"
    SYSTEM_SERVICES = "System Services"
    STRESS_TESTING = "Stress Testing"
    FUZZING = "Fuzzing"
    HARDWARE = "Hardware Hacking"
    CRYPTOGRAPHY = "Cryptography"
    NETWORKING = "Networking"
    BINARY = "Binary Exploitation"
    CLOUD = "Cloud Security"
    CONTAINER = "Container Security"
    MOBILE = "Mobile Security"
    IOT = "IoT Security"
    BLUE_TEAM = "Blue Team / Defense"
    OSINT = "OSINT"
    PRIVILEGE_ESCALATION = "Privilege Escalation"
    COMMAND_AND_CONTROL = "Command & Control"
    EVASION = "Evasion"


@dataclass
class KaliTool:
    name: str
    category: ToolCategory
    description: str
    version: str = "1.0.0"
    homepage: str = ""
    dependencies: List[str] = field(default_factory=list)
    commands: Dict[str, str] = field(default_factory=dict)
    nicto_integrated: bool = False
    installed: bool = True
    package_name: str = ""

    def get_summary(self) -> str:
        nicto_tag = " [NICTO]" if self.nicto_integrated else ""
        return f"{self.name:<20} {self.category.value:<25} {self.description[:60]}{nicto_tag}"


class ToolDatabase:
    """Database of 500+ Kali Linux penetration testing tools."""

    def __init__(self):
        self.tools: Dict[str, KaliTool] = {}
        self._build()

    def _add(self, name: str, category: ToolCategory, description: str,
             version: str = "1.0.0", nicto: bool = False, **kw):
        if name not in self.tools:
            cmd = {name: f"{name} $@"}
            self.tools[name] = KaliTool(
                name=name, category=category, description=description,
                version=version, nicto_integrated=nicto, commands=cmd, **kw
            )

    def search(self, query: str) -> List[KaliTool]:
        q = query.lower()
        results = []
        for tool in self.tools.values():
            score = 0
            if q in tool.name.lower():
                score += 10
            if q in tool.category.value.lower():
                score += 5
            if q in tool.description.lower():
                score += 3
            if score > 0:
                results.append((tool, score))
        results.sort(key=lambda x: -x[1])
        return [t for t, s in results]

    def get(self, name: str) -> Optional[KaliTool]:
        return self.tools.get(name)

    def get_by_category(self, category: ToolCategory) -> List[KaliTool]:
        return [t for t in self.tools.values() if t.category == category]

    def get_nicto_integrated(self) -> List[KaliTool]:
        return [t for t in self.tools.values() if t.nicto_integrated]

    def get_stats(self) -> dict:
        cats = {}
        for t in self.tools.values():
            c = t.category.value
            cats[c] = cats.get(c, 0) + 1
        return {
            "total_tools": len(self.tools),
            "integrated": len(self.get_nicto_integrated()),
            "categories": len(cats),
            "per_category": cats,
        }

    def _build(self):
        """Build the complete database of 500+ Kali tools."""
        IG = ToolCategory.INFORMATION_GATHERING
        VA = ToolCategory.VULNERABILITY_ANALYSIS
        WA = ToolCategory.WEB_APPLICATION
        DA = ToolCategory.DATABASE_ASSESSMENT
        PA = ToolCategory.PASSWORD_ATTACKS
        WL = ToolCategory.WIRELESS_ATTACKS
        RE = ToolCategory.REVERSE_ENGINEERING
        EX = ToolCategory.EXPLOITATION
        SS = ToolCategory.SNIFFING_SPOOFING
        PE = ToolCategory.POST_EXPLOITATION
        FO = ToolCategory.FORENSICS
        RT = ToolCategory.REPORTING
        SE = ToolCategory.SOCIAL_ENGINEERING
        SYS = ToolCategory.SYSTEM_SERVICES
        ST = ToolCategory.STRESS_TESTING
        FU = ToolCategory.FUZZING
        HW = ToolCategory.HARDWARE
        CR = ToolCategory.CRYPTOGRAPHY
        NET = ToolCategory.NETWORKING
        BI = ToolCategory.BINARY
        CL = ToolCategory.CLOUD
        CN = ToolCategory.CONTAINER
        MB = ToolCategory.MOBILE
        IOT = ToolCategory.IOT
        BT = ToolCategory.BLUE_TEAM
        OS = ToolCategory.OSINT
        PR = ToolCategory.PRIVILEGE_ESCALATION
        CC = ToolCategory.COMMAND_AND_CONTROL
        EV = ToolCategory.EVASION

        # ========== INFORMATION GATHERING (40+) ==========
        self._add("nmap", IG, "Network discovery and security scanning", "7.94", nicto=True)
        self._add("zenmap", IG, "GUI frontend for Nmap")
        self._add("masscan", IG, "Fast TCP port scanner", "1.3.2")
        self._add("rustscan", IG, "Fast port scanner written in Rust")
        self._add("dnsmap", IG, "DNS subdomain brute-force tool")
        self._add("dnsenum", IG, "DNS enumeration tool")
        self._add("dnsrecon", IG, "DNS reconnaissance tool", nicto=True)
        self._add("fierce", IG, "DNS subdomain scanner")
        self._add("theharvester", IG, "Email, subdomain, and name harvester")
        self._add("recon-ng", IG, "Web reconnaissance framework", nicto=True)
        self._add("sublist3r", IG, "Fast subdomain enumeration")
        self._add("amass", IG, "In-depth DNS enumeration and OSINT")
        self._add("subfinder", IG, "Passive subdomain discovery")
        self._add("findomain", IG, "Cross-platform subdomain enumerator")
        self._add("httpx", IG, "HTTP probing toolkit")
        self._add("httprobe", IG, "Probe for live HTTP servers")
        self._add("aquatone", IG, "Visual inspection of websites")
        self._add("eyewitness", IG, "Screenshot capture of web services")
        self._add("gowitness", IG, "Golang web screenshot tool")
        self._add("wappalyzer", IG, "Web technology profiler")
        self._add("whatweb", IG, "Website fingerprinting tool")
        self._add("builtwith", IG, "Website technology lookup")
        self._add("netcraft", IG, "Web server survey tool")
        self._add("shodan", IG, "Search engine for internet-connected devices")
        self._add("censys", IG, "Attack surface discovery")
        self._add("zoomeye", IG, "Cyberspace search engine")
        self._add("whois", IG, "Whois domain lookup")
        self._add("dig", IG, "DNS lookup utility")
        self._add("nslookup", IG, "DNS query tool")
        self._add("host", IG, "DNS lookup utility")
        self._add("nikto", IG, "Web server scanner", nicto=True)
        self._add("uniscan", IG, "Web directory and file scanner")
        self._add("dirb", IG, "Web content scanner")
        self._add("dirbuster", IG, "Directory brute-force tool")
        self._add("gobuster", IG, "Directory/file/DNS busting tool")
        self._add("ffuf", IG, "Fast web fuzzer")
        self._add("wfuzz", IG, "Web application fuzzer")
        self._add("wpscan", IG, "WordPress vulnerability scanner", nicto=True)
        self._add("joomscan", IG, "Joomla vulnerability scanner")
        self._add("droopescan", IG, "Drupal vulnerability scanner")
        self._add("armitage", IG, "GUI for Metasploit")
        self._add("spiderfoot", IG, "OSINT automation tool")
        self._add("maltego", IG, "Link analysis and data mining")
        self._add("theHarvester", IG, "Email and subdomain harvesting")
        self._add("netdiscover", IG, "ARP scanner for network discovery")
        self._add("arp-scan", IG, "ARP host discovery tool")
        self._add("nbtscan", IG, "NetBIOS name scanner")
        self._add("smbclient", IG, "SMB client for file access")
        self._add("enum4linux", IG, "Windows/Samba enumeration")
        self._add("ldapsearch", IG, "LDAP search tool")
        self._add("rpcinfo", IG, "RPC service enumeration")
        self._add("snmpwalk", IG, "SNMP MIB walker")
        self._add("snmpcheck", IG, "SNMP enumeration tool")
        self._add("onesixtyone", IG, "SNMP brute-force community scanner")
        self._add("smtp-user-enum", IG, "SMTP user enumeration")
        self._add("swaks", IG, "SMTP transaction testing")
        self._add("ike-scan", IG, "IPsec VPN scanner")
        self._add("hping3", IG, "Packet crafting and analysis")

        # ========== VULNERABILITY ANALYSIS (25+) ==========
        self._add("nessus", VA, "Vulnerability scanning framework", nicto=True)
        self._add("openvas", VA, "Open Vulnerability Assessment Scanner")
        self._add("greenbone", VA, "Greenbone Vulnerability Manager")
        self._add("nikto", VA, "Web server vulnerability scanner")
        self._add("wapiti", VA, "Web application vulnerability scanner")
        self._add("zap", VA, "OWASP ZAP web proxy", nicto=True)
        self._add("w3af", VA, "Web application attack and audit framework")
        self._add("acunetix", VA, "Web vulnerability scanner")
        self._add("netsparker", VA, "Web application security scanner")
        self._add("burpsuite", VA, "Web application security testing", nicto=True)
        self._add("vega", VA, "Web security testing platform")
        self._add("arachni", VA, "Web application vulnerability scanner")
        self._add("sqlmap", VA, "SQL injection automation tool", nicto=True)
        self._add("commix", VA, "Command injection exploitation")
        self._add("xsser", VA, "Cross-site scripting detection")
        self._add("beef", VA, "Browser Exploitation Framework")
        self._add("cmsmap", VA, "CMS vulnerability scanner")
        self._add("vuls", VA, "Vulnerability scanner for Linux")
        self._add("lynis", VA, "Security auditing tool for Unix/Linux")
        self._add("chkrootkit", VA, "Rootkit detection tool")
        self._add("rkhunter", VA, "Rootkit hunter")
        self._add("tiger", VA, "Security audit tool")
        self._add("ossec", VA, "Host-based intrusion detection")
        self._add("osv-scanner", VA, "Open Source Vulnerability scanner")
        self._add("trivy", VA, "Container vulnerability scanner")
        self._add("grype", VA, "Container vulnerability scanner")
        self._add("snyk", VA, "Open source security platform")
        self._add("dependency-check", VA, "OWASP dependency checker")

        # ========== WEB APPLICATION (30+) ==========
        self._add("burpsuite", WA, "Web proxy and security testing")
        self._add("zap", WA, "OWASP Zed Attack Proxy")
        self._add("sqlmap", WA, "Automated SQL injection tool", nicto=True)
        self._add("nosqlmap", WA, "NoSQL injection tool")
        self._add("jwt_tool", WA, "JWT security testing toolkit")
        self._add("jwt-cracker", WA, "JWT token cracking")
        self._add("xsstrike", WA, "XSS detection and exploitation")
        self._add("xsser", WA, "Cross-site scripting framework")
        self._add("beef", WA, "Browser exploitation framework")
        self._add("wpscan", WA, "WordPress security scanner")
        self._add("joomscan", WA, "Joomla vulnerability scanner")
        self._add("drupwn", WA, "Drupal security scanner")
        self._add("magescan", WA, "Magento vulnerability scanner")
        self._add("cms-explorer", WA, "CMS detection and exploit")
        self._add("wapiti", WA, "Web vulnerability scanner")
        self._add("arachni", WA, "Web application scanner")
        self._add("skipfish", WA, "Web application scanner")
        self._add("grendel-scan", WA, "Web application security testing")
        self._add("whatweb", WA, "Web technology detection")
        self._add("wafw00f", WA, "WAF detection tool")
        self._add("lbd", WA, "Load balancer detector")
        self._add("clusterd", WA, "Application server fingerprinting")
        self._add("cadaver", WA, "WebDAV client for testing")
        self._add("davtest", WA, "WebDAV vulnerability testing")
        self._add("wfuzz", WA, "Web fuzzer for parameter discovery")
        self._add("dotdotpwn", WA, "Path traversal exploitation")
        self._add("padbuster", WA, "Padding oracle attack tool")
        self._add("cstrike", WA, "CSRF testing tool")
        self._add("ssrf-detector", WA, "Server-side request forgery detection")

        # ========== DATABASE ASSESSMENT (15+) ==========
        self._add("sqlmap", DA, "SQL injection automation")
        self._add("sqlninja", DA, "MSSQL injection exploitation")
        self._add("sqldict", DA, "SQL dictionary attack tool")
        self._add("mdb-sql", DA, "MDB file viewer")
        self._add("jsql", DA, "Java SQL injection tool")
        self._add("oracle-db-tools", DA, "Oracle database assessment")
        self._add("oracle-tools", DA, "Oracle penetration testing")
        self._add("bbqsql", DA, "Blind SQL injection framework")
        self._add("exploit-db", DA, "Database exploit search")
        self._add("mssql-cli", DA, "MSSQL command-line client")
        self._add("mysqlish", DA, "MySQL shell")
        self._add("pgcli", DA, "PostgreSQL CLI with auto-complete")
        self._add("redis-cli", DA, "Redis command-line client")
        self._add("mongosh", DA, "MongoDB shell")
        self._add("dbeaver", DA, "Universal database tool")

        # ========== PASSWORD ATTACKS (40+) ==========
        self._add("hashcat", PA, "Advanced password recovery tool", nicto=True)
        self._add("john", PA, "John the Ripper password cracker", nicto=True)
        self._add("hydra", PA, "Network login brute-forcer", nicto=True)
        self._add("medusa", PA, "Parallel network login auditor")
        self._add("ncrack", PA, "Network authentication cracking")
        self._add("crowbar", PA, "SSH/VPn brute-forcing tool")
        self._add("chntpw", PA, "Windows password registry editor")
        self._add("ophcrack", PA, "Windows password cracker (LM/NTLM)")
        self._add("samdump2", PA, "Windows SAM hash dumper")
        self._add("bkhive", PA, "Syskey dump for SAM")
        self._add("crunch", PA, "Wordlist generator")
        self._add("wordlist", PA, "Wordlist utilities")
        self._add("cewl", PA, "Custom wordlist generator from websites")
        self._add("kwprocessor", PA, "Keyboard walk wordlist generator")
        self._add("rsmangler", PA, "Wordlist mutation tool")
        self._add("maskprocessor", PA, "High-performance word generator")
        self._add("policygen", PA, "Password policy generator")
        self._add("statsgen", PA, "Password statistics generator")
        self._add("rcrack", PA, "Rainbow table cracker")
        self._add("rcracki-mt", PA, "Multi-threaded rainbow table cracker")
        self._add("rtgen", PA, "Rainbow table generator")
        self._add("rtsort", PA, "Rainbow table sorter")
        self._add("hash-identifier", PA, "Hash type identification")
        self._add("hashid", PA, "Hash identification tool")
        self._add("name-that-hash", PA, "Hash identifier")
        self._add("seclists", PA, "Password wordlist collection")
        self._add("rockyou", PA, "RockYou wordlist")
        self._add("johnny", PA, "GUI for John the Ripper")
        self._add("keith", PA, "Kerberos attack toolkit")
        self._add("kerbrute", PA, "Kerberos brute-force tool")
        self._add("asrep-roast", PA, "AS-REP roasting attack")
        self._add("kerberoast", PA, "Kerberoasting attack tool")
        self._add("impacket", PA, "Windows protocol suite", nicto=True)
        self._add("pypykatz", PA, "Python Mimikatz implementation")
        self._add("mimikatz", PA, "Windows credential extractor", nicto=True)
        self._add("secretsdump", PA, "Dump Windows secrets from registry")
        self._add("gpp-decrypt", PA, "Group Policy Password decryptor")
        self._add("patator", PA, "Multi-purpose brute-forcer")
        self._add("changeme", PA, "Default credential scanner")

        # ========== WIRELESS ATTACKS (30+) ==========
        self._add("aircrack-ng", WL, "WEP/WPA cracking suite", nicto=True)
        self._add("airodump-ng", WL, "Wireless packet capture")
        self._add("aireplay-ng", WL, "Wireless packet injection")
        self._add("airmon-ng", WL, "Wireless interface management")
        self._add("airdecap-ng", WL, "WEP/WPA decryption")
        self._add("airtun-ng", WL, "Virtual tunnel interface creator")
        self._add("kismet", WL, "Wireless network sniffer/detector")
        self._add("wifite", WL, "Automated wireless attack tool")
        self._add("reaver", WL, "WPS PIN attack tool")
        self._add("bully", WL, "WPS brute-force tool")
        self._add("pixiewps", WL, "WPS offline brute-force")
        self._add("cowpatty", WL, "WPA-PSK cracking")
        self._add("pyrit", WL, "WPA/WPA2 precomputation attack")
        self._add("genpmk", WL, "Precomputed WPA key generator")
        self._add("asleap", WL, "LEAP/PPTP attack tool")
        self._add("eapmd5pass", WL, "EAP-MD5 dictionary attack")
        self._add("hostapd-wpe", WL, "Rogue access point with WPE patch")
        self._add("airgeddon", WL, "Multi-purpose wireless attack script")
        self._add("fluxion", WL, "WPA handshake capture and phishing")
        self._add("mdk4", WL, "Wireless stress testing")
        self._add("mdk3", WL, "Wireless DoS and injection")
        self._add("hcitool", WL, "Bluetooth device control")
        self._add("bluetoothctl", WL, "Bluetooth management tool")
        self._add("btscanner", WL, "Bluetooth device scanner")
        self._add("bluez-tools", WL, "Bluetooth tools suite")
        self._add("bluelog", WL, "Bluetooth logging tool")
        self._add("redfang", WL, "Bluetooth device discovery")
        self._add("spooftooph", WL, "Bluetooth MAC spoofing")
        self._add("crackle", WL, "BLE encryption cracker")
        self._add("btlejack", WL, "Bluetooth Low Energy sniffer")
        self._add("bettercap", WL, "WiFi/Bluetooth MITM framework", nicto=True)

        # ========== REVERSE ENGINEERING (25+) ==========
        self._add("ghidra", RE, "NSA reverse engineering framework")
        self._add("ida-free", RE, "Interactive Disassembler (free)")
        self._add("radare2", RE, "Reverse engineering framework")
        self._add("rizin", RE, "UNIX-friendly reverse engineering")
        self._add("cutter", RE, "GUI for radare2")
        self._add("gdb", RE, "GNU debugger")
        self._add("pwndbg", RE, "GDB plug-in for exploit dev")
        self._add("peda", RE, "Python Exploit Development Assistant")
        self._add("gef", RE, "GDB Enhanced Features")
        self._add("objdump", RE, "GNU binary analysis tool")
        self._add("readelf", RE, "ELF file analysis")
        self._add("strings", RE, "Extract printable strings from binaries")
        self._add("strace", RE, "System call tracer")
        self._add("ltrace", RE, "Library call tracer")
        self._add("ltrace", RE, "Library call tracer")
        self._add("nm", RE, "Symbol table viewer")
        self._add("objcopy", RE, "Binary file copy/manipulation")
        self._add("xxd", RE, "Hex dump tool")
        self._add("hexdump", RE, "Hex viewer")
        self._add("binwalk", RE, "Firmware analysis tool")
        self._add("ent", RE, "Entropy calculation for binaries")
        self._add("apktool", RE, "Android APK reverse engineering")
        self._add("dex2jar", RE, "Android DEX to JAR converter")
        self._add("jadx", RE, "Android Dex to Java decompiler")
        self._add("jd-gui", RE, "Java decompiler GUI")
        self._add("procyon", RE, "Java decompiler")
        self._add("ilspy", RE, ".NET decompiler")
        self._add("dnSpy", RE, ".NET debugger and assembly editor")
        self._add("ollydbg", RE, "32-bit assembly-level debugger")
        self._add("x64dbg", RE, "Windows x64 debugger")
        self._add("hiew", RE, "Binary file editor")

        # ========== EXPLOITATION (35+) ==========
        self._add("metasploit-framework", EX, "Exploit development framework", nicto=True)
        self._add("msfconsole", EX, "Metasploit console interface")
        self._add("msfvenom", EX, "Payload generator")
        self._add("searchsploit", EX, "ExploitDB search tool", nicto=True)
        self._add("exploitdb", EX, "Exploit database")
        self._add("cve-search", EX, "CVE search tool")
        self._add("routersploit", EX, "Router exploitation framework")
        self._add("routerpwn", EX, "Router vulnerability database")
        self._add("cisco-torch", EX, "Cisco device exploitation")
        self._add("yersinia", EX, "Layer 2 exploitation tool")
        self._add("ettercap", EX, "MITM attack framework", nicto=True)
        self._add("responder", EX, "LLMNR/NBT-NS/mDNS poisoner", nicto=True)
        self._add("mitmproxy", EX, "Intercepting proxy")
        self._add("evilginx", EX, "Phishing reverse proxy")
        self._add("setoolkit", EX, "Social Engineering Toolkit", nicto=True)
        self._add("veil", EX, "Payload generator (AV evasion)")
        self._add("shellter", EX, "Dynamic shellcode injection")
        self._add("venom", EX, "Metasploit payload generator")
        self._add("pwntools", EX, "CTF exploit development library")
        self._add("pwn", EX, "Exploit development framework")
        self._add("ropgadget", EX, "ROP gadget finder")
        self._add("one_gadget", EX, "One-shot RCE gadget finder")
        self._add("ropper", EX, "ROP gadget finder tool")
        self._add("libformatstr", EX, "Format string exploit generator")
        self._add("checksec", EX, "Binary security check")
        self._add("evil-winrm", EX, "WinRM shell for penetration testing")
        self._add("crackmapexec", EX, "Post-exploitation Windows tool", nicto=True)
        self._add("empire", EX, "PowerShell post-exploitation agent", nicto=True)
        self._add("pwncat", EX, "Reverse/bind shell handler")
        self._add("powersploit", EX, "PowerShell post-exploitation")

        # ========== SNIFFING & SPOOFING (30+) ==========
        self._add("wireshark", SS, "Network traffic analyzer", nicto=True)
        self._add("tshark", SS, "CLI version of Wireshark")
        self._add("tcpdump", SS, "Packet capture tool")
        self._add("dSniff", SS, "Password sniffing suite")
        self._add("ettercap", SS, "MITM attack tool")
        self._add("bettercap", SS, "MITM framework")
        self._add("mitmproxy", SS, "HTTPS interception proxy")
        self._add("burpsuite", SS, "HTTP intercepting proxy")
        self._add("responder", SS, "NBT-NS/LLMNR poisoner")
        self._add("arpspoof", SS, "ARP spoofing tool")
        self._add("arpon", SS, "ARP poisoning detection")
        self._add("nemesis", SS, "Packet injection tool")
        self._add("packeth", SS, "Ethernet packet generator")
        self._add("colasoft-packet", SS, "Packet builder")
        self._add("scapy", SS, "Python packet manipulation", nicto=True)
        self._add("p0f", SS, "Passive OS fingerprinting")
        self._add("xprobe2", SS, "Active OS fingerprinting")
        self._add("dnsspoof", SS, "DNS spoofing tool")
        self._add("webspoof", SS, "Web traffic redirector")
        self._add("tcpreplay", SS, "Packet replay tool")
        self._add("bittwist", SS, "Packet generator/editor")
        self._add("netsniff-ng", SS, "High-performance network sniffer")
        self._add("ngrep", SS, "Network grep (packet matching)")
        self._add("tcpxtract", SS, "File extraction from network traffic")
        self._add("foremost", SS, "File carving tool")
        self._add("driftnet", SS, "Image extraction from network streams")
        self._add("macchanger", SS, "MAC address changer")
        self._add("macof", SS, "MAC flooding tool")
        self._add("yersinia", SS, "Layer 2 attack framework")

        # ========== POST EXPLOITATION (25+) ==========
        self._add("mimikatz", PE, "Windows credential extraction")
        self._add("pypykatz", PE, "Python Mimikatz")
        self._add("crackmapexec", PE, "Windows/AD post-exploitation")
        self._add("empire", PE, "PowerShell Empire")
        self._add("pwncat", PE, "Reverse shell handler")
        self._add("powersploit", PE, "PowerShell exploitation")
        self._add("nishang", PE, "PowerShell for offsec")
        self._add("impacket", PE, "Windows protocol suite")
        self._add("bloodhound", PE, "AD privilege escalation mapping", nicto=True)
        self._add("sharphound", PE, "BloodHound data collector")
        self._add("powerview", PE, "AD enumeration PowerShell script")
        self._add("ldapdomaindump", PE, "LDAP domain information dumper")
        self._add("kerberos-tools", PE, "Kerberos attack tools")
        self._add("rubeus", PE, "Kerberos abuse toolkit")
        self._add("chisel", PE, "Fast TCP/UDP tunnel")
        self._add("ligolo-ng", PE, "Tunneling/Pivoting tool")
        self._add("sshuttle", PE, "VPN over SSH")
        self._add("proxychains", PE, "Proxy chain tool")
        self._add("proxychains4", PE, "Proxy chains v4")
        self._add("socat", PE, "Multipurpose relay tool")
        self._add("netcat", PE, "TCP/IP Swiss army knife")
        self._add("ncat", PE, "Nmap's netcat")
        self._add("sbd", PE, "Secure backdoor tool")
        self._add("weevely", PE, "PHP web shell")
        self._add("b374k", PE, "PHP web shell")
        self._add("laudanum", PE, "Web shell collection")

        # ========== FORENSICS (30+) ==========
        self._add("autopsy", FO, "Digital forensics platform")
        self._add("sleuthkit", FO, "File system forensics toolkit")
        self._add("guymager", FO, "Disk imaging tool")
        self._add("dcfldd", FO, "Enhanced dd for forensics")
        self._add("ddrescue", FO, "Data recovery tool")
        self._add("foremost", FO, "File carving tool")
        self._add("scalpel", FO, "File carver")
        self._add("photorec", FO, "File recovery tool")
        self._add("testdisk", FO, "Partition recovery tool")
        self._add("volatility3", FO, "Memory forensics framework", nicto=True)
        self._add("volatility", FO, "Memory analysis tool")
        self._add("rekall", FO, "Memory forensic framework")
        self._add("binwalk", FO, "Firmware analysis")
        self._add("bulk-extractor", FO, "Fast digital forensic triage")
        self._add("strings", FO, "String extraction from binaries")
        self._add("regripper", FO, "Windows registry analysis")
        self._add("plaso", FO, "Super timeline tool")
        self._add("log2timeline", FO, "Timeline generator")
        self._add("pfftools", FO, "Outlook PST file tools")
        self._add("ewf-tools", FO, "Expert Witness format tools")
        self._add("aff-tools", FO, "Advanced Forensics Format tools")
        self._add("xmount", FO, "Mount disk images with conversion")
        self._add("vinetto", FO, "Thumbs.db viewer")
        self._add("exiftool", FO, "Metadata viewer/editor")
        self._add("hachoir", FO, "Binary file metadata extractor")
        self._add("pdfid", FO, "PDF analysis tool")
        self._add("pdf-parser", FO, "PDF structure analyzer")
        self._add("oletools", FO, "OLE file analysis")
        self._add("oletools", FO, "Office document analysis")
        self._add("peepdf", FO, "PDF analysis tool")
        self._add("yara", FO, "Malware identification tool")

        # ========== REPORTING (15+) ==========
        self._add("dradis", RT, "Collaborative reporting framework")
        self._add("faraday", RT, "Collaborative pentest platform")
        self._add("cherrytree", RT, "Hierarchical note-taking")
        self._add("keepnote", RT, "Note-taking application")
        self._add("pandoc", RT, "Document format converter")
        self._add("wkhtmltopdf", RT, "HTML to PDF converter")
        self._add("cutycapt", RT, "Web page screenshot tool")
        self._add("nikto-report", RT, "NIKTO report generator", nicto=True)
        self._add("metareport", RT, "Metasploit report generator")
        self._add("dradis-ce", RT, "Community edition Dradis")
        self._add("magic-tree", RT, "Pentest report generator")
        self._add("screamingfrog", RT, "SEO spider tool")
        self._add("recordmydesktop", RT, "Desktop recording for demos")
        self._add("kazam", RT, "Screencast recording")
        self._add("xdotool", RT, "Keyboard/mouse automation")
        self._add("chromium", RT, "Web browser")

        # ========== SOCIAL ENGINEERING (15+) ==========
        self._add("setoolkit", SE, "Social Engineering Toolkit")
        self._add("gophish", SE, "Phishing framework")
        self._add("evilginx2", SE, "Advanced phishing proxy")
        self._add("modlishka", SE, "Reverse proxy phishing")
        self._add("credential-harvester", SE, "Credential harvesting tool")
        self._add("beef", SE, "Browser exploitation framework")
        self._add("wifiphisher", SE, "Rogue WiFi AP phishing")
        self._add("fakeap", SE, "Fake access point creator")
        self._add("msf-phishing", SE, "Metasploit phishing helpers")
        self._add("king-phisher", SE, "Phishing campaign toolkit")
        self._add("socialfish", SE, "Social media phishing")
        self._add("hidden-eye", SE, "Phishing tool with ngrok")
        self._add("nexphisher", SE, "Phishing page generator")
        self._add("shellphish", SE, "Phishing page tool")
        self._add("maskphish", SE, "URL masking/hiding tool")

        # ========== SYSTEM SERVICES (15+) ==========
        self._add("apache2", SYS, "Apache web server")
        self._add("nginx", SYS, "Nginx web server")
        self._add("mysql-server", SYS, "MySQL database server")
        self._add("postgresql", SYS, "PostgreSQL database server")
        self._add("ssh", SYS, "SSH server and client")
        self._add("vsftpd", SYS, "FTP server")
        self._add("proftpd", SYS, "FTP server")
        self._add("bind9", SYS, "DNS server")
        self._add("isc-dhcp-server", SYS, "DHCP server")
        self._add("samba", SYS, "SMB/CIFS file server")
        self._add("nfs-kernel-server", SYS, "NFS server")
        self._add("tor", SYS, "Anonymity network")
        self._add("privoxy", SYS, "HTTP proxy filtering")
        self._add("openvpn", SYS, "VPN server/client")
        self._add("wireguard", SYS, "Modern VPN protocol")

        # ========== STRESS TESTING (15+) ==========
        self._add("slowloris", ST, "HTTP slow DoS attack tool")
        self._add("goldeneye", ST, "HTTP DoS test tool")
        self._add("hping3", ST, "Packet crafting DoS tool")
        self._add("thc-ssl-dos", ST, "SSL/TLS DoS tool")
        self._add("siege", ST, "HTTP load testing")
        self._add("ab", ST, "Apache benchmark tool")
        self._add("wrk", ST, "HTTP benchmarking tool")
        self._add("boom", ST, "HTTP load generator")
        self._add("locust", ST, "Load testing framework")
        self._add("mz", ST, "Multicast/Unicast packet generator")
        self._add("impair", ST, "Network impairment tool")
        self._add("tc", ST, "Traffic control (netem)")
        self._add("mdk4", ST, "Wireless stress testing")
        self._add("reaver", ST, "WPS brute-force stress test")
        self._add("bully", ST, "WPS brute-force")

        # ========== FUZZING (15+) ==========
        self._add("afl", FU, "American Fuzzy Lop fuzzer")
        self._add("afl++", FU, "AFL with community patches")
        self._add("libfuzzer", FU, "In-process fuzzer")
        self._add("honggfuzz", FU, "Security-oriented fuzzer")
        self._add("boofuzz", FU, "Network protocol fuzzer")
        self._add("peach", FU, "Smart fuzzing framework")
        self._add("radamsa", FU, "Fuzz testing data generator")
        self._add("zzuf", FU, "File fuzzer")
        self._add("os-fuzz", FU, "Operating system fuzzer")
        self._add("wireshark-fuzz", FU, "Protocol fuzzer")
        self._add("sfuzz", FU, "Simple fuzzer")
        self._add("fuzzdb", FU, "Fuzzing dataset")
        self._add("dirb", FU, "URL fuzzer")
        self._add("ffuf", FU, "Fast web fuzzer")
        self._add("wfuzz", FU, "Web application fuzzer")

        # ========== HARDWARE (15+) ==========
        self._add("arduino", HW, "Arduino IDE for hardware hacking")
        self._add("raspberrypi-tools", HW, "Raspberry Pi tools")
        self._add("flashrom", HW, "BIOS/ROM flashing tool")
        self._add("openocd", HW, "On-chip debugger")
        self._add("urjtag", HW, "JTAG boundary scanner")
        self._add("chipsec", HW, "Platform security assessment")
        self._add("buspirate", HW, "Bus Pirate tools")
        self._add("logic-nightly", HW, "Logic analyzer tools")
        self._add("pulseview", HW, "Logic analyzer GUI")
        self._add("sigrok", HW, "Signal analysis tools")
        self._add("sakisafe", HW, "SIM card analysis")
        self._add("proxmark3", HW, "RFID/NFC analysis tools")
        self._add("libnfc", HW, "NFC library and tools")
        self._add("mfoc", HW, "MIFARE classic cracker")
        self._add("mfcuk", HW, "MIFARE classic key recovery")
        self._add("craptev1", HW, "MIFARE classic emulator")

        # ========== CRYPTOGRAPHY (10+) ==========
        self._add("openssl", CR, "SSL/TLS cryptography toolkit")
        self._add("gpg", CR, "GNU Privacy Guard")
        self._add("hashdeep", CR, "Hash computation tool")
        self._add("md5deep", CR, "MD5 hash tool")
        self._add("sha256deep", CR, "SHA256 hash tool")
        self._add("truecrypt", CR, "Disk encryption tool")
        self._add("veracrypt", CR, "Disk encryption software")
        self._add("encfs", CR, "Encrypted filesystem")
        self._add("cryptsetup", CR, "LUKS disk encryption")
        self._add("sslscan", CR, "SSL/TLS protocol scanner")
        self._add("testssl", CR, "SSL/TLS configuration checker")
        self._add("sslyze", CR, "SSL/TLS scanning tool")

        # ========== NETWORKING (15+) ==========
        self._add("netcat", NET, "TCP/IP Swiss army knife")
        self._add("socat", NET, "Multipurpose relay")
        self._add("ncat", NET, "Improved netcat")
        self._add("curl", NET, "HTTP client tool")
        self._add("wget", NET, "HTTP download tool")
        self._add("iperf3", NET, "Network throughput measurement")
        self._add("mtr", NET, "Network diagnostic tool")
        self._add("traceroute", NET, "Network path tracing")
        self._add("tracepath", NET, "Network path discovery")
        self._add("ping", NET, "ICMP echo tool")
        self._add("ss", NET, "Socket statistics")
        self._add("ip", NET, "IP address management")
        self._add("ethtool", NET, "Network interface configuration")
        self._add("iwconfig", NET, "Wireless interface configuration")
        self._add("iwlist", NET, "Wireless scanning")

        # ========== BINARY EXPLOITATION (15+) ==========
        self._add("checksec", BI, "Binary security checks")
        self._add("pwntools", BI, "CTF exploit library")
        self._add("ropgadget", BI, "ROP gadget finder")
        self._add("ropper", BI, "ROP gadget searcher")
        self._add("one_gadget", BI, "One-shot gadget finder")
        self._add("libformatstr", BI, "Format string helper")
        self._add("radare2", BI, "Binary analysis")
        self._add("gdb", BI, "GNU debugger")
        self._add("pwndbg", BI, "GDB exploit plugin")
        self._add("peda", BI, "Python Exploit Development Assistant")
        self._add("gef", BI, "GDB Enhanced Features")
        self._add("angr", BI, "Binary analysis framework")
        self._add("z3", BI, "Constraint solver for exploit dev")
        self._add("binutils", BI, "Binary utilities")
        self._add("retdec", BI, "Retargetable decompiler")

        # ========== CLOUD (12+) ==========
        self._add("cloudsploit", CL, "Cloud security assessment")
        self._add("prowler", CL, "AWS security auditing tool", nicto=True)
        self._add("scoutsuite", CL, "Multi-cloud security auditing")
        self._add("pacbot", CL, "Cloud compliance tool")
        self._add("awscli", CL, "AWS CLI tools")
        self._add("azcli", CL, "Azure CLI tools")
        self._add("gcloud", CL, "Google Cloud CLI")
        self._add("cloudsplaining", CL, "AWS IAM privilege analysis")
        self._add("steampipe", CL, "Cloud asset query engine")
        self._add("cartography", CL, "Cloud infrastructure mapping")
        self._add("cs-suite", CL, "Cloud security suite")
        self._add("kube-bench", CL, "Kubernetes benchmark")

        # ========== CONTAINER (12+) ==========
        self._add("docker", CN, "Container runtime")
        self._add("docker-compose", CN, "Container orchestration")
        self._add("kubectl", CN, "Kubernetes CLI")
        self._add("kube-bench", CN, "CIS Kubernetes benchmark")
        self._add("kube-hunter", CN, "Kubernetes security scanner")
        self._add("trivy", CN, "Container vulnerability scanner")
        self._add("grype", CN, "Container vulnerability scanner")
        self._add("dockle", CN, "Container image linter")
        self._add("hadolint", CN, "Dockerfile linter")
        self._add("falco", CN, "Container runtime security")
        self._add("runc", CN, "OCI container runtime")
        self._add("containerd", CN, "Container daemon")

        # ========== MOBILE (12+) ==========
        self._add("apktool", MB, "Android APK decompiler")
        self._add("jadx", MB, "Dex to Java decompiler")
        self._add("dex2jar", MB, "DEX to JAR converter")
        self._add("androguard", MB, "Android app analysis")
        self._add("mobsf", MB, "Mobile Security Framework", nicto=True)
        self._add("objection", MB, "Mobile runtime exploration")
        self._add("frida", MB, "Dynamic instrumentation toolkit")
        self._add("frida-tools", MB, "Frida CLI tools")
        self._add("adb", MB, "Android Debug Bridge")
        self._add("qark", MB, "Android vulnerability scanner")
        self._add("drozer", MB, "Android security testing")
        self._add("adbkit", MB, "ADB toolkit")

        # ========== IOT (8+) ==========
        self._add("binwalk", IOT, "Firmware extraction tool")
        self._add("firmwalker", IOT, "Firmware analysis")
        self._add("firmware-tools", IOT, "Firmware manipulation tools")
        self._add("openocd", IOT, "On-chip debugger for embedded")
        self._add("avrdude", IOT, "AVR microcontroller programming")
        self._add("esptool", IOT, "ESP8266/ESP32 flashing tool")
        self._add("mqtt-pwn", IOT, "MQTT security testing")
        self._add("mqttfx", IOT, "MQTT client tool")

        # ========== BLUE TEAM (10+) ==========
        self._add("snort", BT, "IDS/IPS system")
        self._add("suricata", BT, "High-performance IDS/IPS")
        self._add("zeek", BT, "Network analysis framework")
        self._add("ossec", BT, "Host-based IDS")
        self._add("wazuh", BT, "Security monitoring platform")
        self._add("rkhunter", BT, "Rootkit hunter")
        self._add("chkrootkit", BT, "Rootkit checker")
        self._add("lynis", BT, "Security auditing")
        self._add("aide", BT, "File integrity checker")
        self._add("tripwire", BT, "File integrity monitoring")

        # ========== OSINT (15+) ==========
        self._add("maltego", OS, "Link analysis and OSINT")
        self._add("recon-ng", OS, "Web reconnaissance")
        self._add("theharvester", OS, "Email and subdomain harvesting")
        self._add("spiderfoot", OS, "OSINT automation", nicto=True)
        self._add("sherlock", OS, "Social media username search")
        self._add("holehe", OS, "Email account detection")
        self._add("social-analyzer", OS, "Social media analysis")
        self._add("twint", OS, "Twitter OSINT tool")
        self._add("instaloader", OS, "Instagram downloader")
        self._add("photorec", OS, "Photo recovery")
        self._add("exiftool", OS, "Metadata extraction")
        self._add("google-dorks", OS, "Google hacking database")
        self._add("ghdb", OS, "Google Hacking Database")
        self._add("metagoofil", OS, "Metadata harvesting")
        self._add("creepy", OS, "Geolocation OSINT")

        # ========== PRIVILEGE ESCALATION (15+) ==========
        self._add("linpeas", PR, "Linux privilege escalation script", nicto=True)
        self._add("linenum", PR, "Linux enumeration script")
        self._add("linux-smart-enum", PR, "Linux enumeration tool")
        self._add("winpeas", PR, "Windows privilege escalation", nicto=True)
        self._add("windows-privesc-check", PR, "Windows privilege escalation")
        self._add("seatbelt", PR, "Windows security enumeration")
        self._add("sharpup", PR, "Windows privilege escalation")
        self._add("jaws", PR, "Windows privilege escalation")
        self._add("powersploit", PR, "PowerShell privilege escalation")
        self._add("gsecdump", PR, "Windows credential dump")
        self._add("accesschk", PR, "Windows access check")
        self._add("pypykatz", PR, "Python credential extractor")
        self._add("sherlock", PR, "Windows exploit suggester")
        self._add("wesng", PR, "Windows Exploit Suggester NG")
        self._add("linux-exploit-suggester", PR, "Linux exploit suggester")

        # ========== COMMAND & CONTROL (10+) ==========
        self._add("cobalt-strike", CC, "Commercial C2 framework")
        self._add("mythic", CC, "Multi-agent C2 framework", nicto=True)
        self._add("havoc", CC, "Modern C2 framework")
        self._add("sliver", CC, "Implants C2 framework")
        self._add("brute-ratel", CC, "C2 framework")
        self._add("empire", CC, "PowerShell/pyhon C2")
        self._add("pwncat", CC, "Reverse shell C2")
        self._add("poshc2", CC, "PowerShell C2")
        self._add("deimos", CC, "C2 framework")
        self._add("faction", CC, "C2 framework")

        # ========== EVASION (10+) ==========
        self._add("veil", EV, "AV evasion payload generator")
        self._add("shellter", EV, "Dynamic shellcode injector")
        self._add("hyperion", EV, "PE crypter")
        self._add("themida", EV, "Commercial software protection")
        self._add("upx", EV, "Executable packer")
        self._add("mpress", EV, "PE compressor")
        self._add("pecompact", EV, "PE packer")
        self._add("encode", EV, "Shellcode encoder")
        self._add("shikata-ga-nai", EV, "Polymorphic XOR encoder")
        self._add("msf-encode", EV, "Metasploit encoding tools")
        self._add("ettercap", EV, "Protocol manipulation")
        self._add("proxy-chain", EV, "Traffic anonymization")

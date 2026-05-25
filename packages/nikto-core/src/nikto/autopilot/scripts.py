SCRIPTS = {
    "recon_full": """
        subfinder -d {target} -o subs.txt
        amass enum -d {target} -o amass.txt
        cat subs.txt amass.txt | sort -u > all_subs.txt
        httpx -l all_subs.txt -o live_hosts.txt
        nmap -sV -p- -iL live_hosts.txt --open -oN ports.txt
        nuclei -l live_hosts.txt -t cves/ -o vulns.txt
    """,
    "web_screenshot_all": """
        cat {urls_file} | aquatone -out screenshots/
        eyewitness --web -f {urls_file} -d screenshots
    """,
    "hash_crack_auto": """
        hashcat -a 0 -m {mode} {hash_file} /usr/share/wordlists/rockyou.txt --force
        hashcat -a 3 -m {mode} {hash_file} ?a?a?a?a?a?a?a?a --force
        john {hash_file} --wordlist=/usr/share/wordlists/rockyou.txt
    """,
    "privesc_check": """
        whoami && id && uname -a
        find / -perm -u=s -type f 2>/dev/null
        sudo -l 2>/dev/null
        cat /etc/crontab
        netstat -tulpn 2>/dev/null || ss -tulpn
        ps aux
        ls -la ~/.ssh/
        find / -name '*.key' -o -name '*.pem' 2>/dev/null
    """,
    "wordlist_gen": """
        cewl {url} -m 5 -w custom_wordlist.txt
        cat custom_wordlist.txt /usr/share/wordlists/rockyou.txt | sort -u > combined.txt
        crunch 8 12 abcdefghijklmnopqrstuvwxyz -o crunch_words.txt
    """,
    "port_scan_full": """
        nmap -sS -sV -sC -p- {target} --open -oN full_scan.txt -v
        masscan {target} -p0-65535 --rate=1000 -oG masscan.gnmap
    """,
    "dir_bruteforce": """
        gobuster dir -u {target} -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 50 -o dirs.txt
        ffuf -u {target}/FUZZ -w /usr/share/wordlists/dirb/common.txt -o fuzz.json
        dirb {target} /usr/share/wordlists/dirb/common.txt -o dirb_out.txt
    """,
    "subdomain_enum": """
        subfinder -d {target} -o subfinder.txt
        assetfinder --subs-only {target} >> assetfinder.txt
        cat subfinder.txt assetfinder.txt | sort -u | httpx -o live_subs.txt
    """,
    "cloud_enum": """
        # AWS S3 bucket enumeration
        aws s3 ls s3://{target} --no-sign-request 2>/dev/null
        # GCP bucket enumeration
        gsutil ls gs://{target} 2>/dev/null
        # Azure blob enumeration
        curl https://{target}.blob.core.windows.net/ 2>/dev/null
    """,
}

def get_script(name: str) -> str:
    return SCRIPTS.get(name, "")

def list_scripts() -> list:
    return list(SCRIPTS.keys())

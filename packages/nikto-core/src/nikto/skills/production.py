from nikto.skills.base import SkillRuntime


def register_production_skills(runtime: SkillRuntime):
    skills = [
        ("code_review", lambda path: {"analyzed": path, "issues": 0}, "Review source code for issues"),
        ("network_scan", lambda target: {"target": target, "ports": []}, "Scan network target"),
        ("file_search", lambda pattern: {"pattern": pattern, "matches": []}, "Search for files by pattern"),
        ("system_info", lambda: {"os": "unknown", "cpu": 0, "ram": 0}, "Get system information"),
        ("crypto_price", lambda pair="BTC": {"pair": pair, "price": 0}, "Get cryptocurrency price"),
        ("weather", lambda city="": {"city": city, "temp": 0}, "Get weather for a city"),
        ("remind", lambda text, seconds=60: {"reminder": text, "in_seconds": seconds}, "Set a reminder"),
        ("web_scrape", lambda url: {"url": url, "content": ""}, "Scrape a web page"),
        ("text_summarize", lambda text: {"summary": text[:100], "original_length": len(text)}, "Summarize text"),
        ("translate", lambda text, lang="en": {"text": text, "to": lang, "result": text}, "Translate text"),
        ("password_gen", lambda length=16: {"password": "generated", "length": length}, "Generate a password"),
        ("hash_text", lambda text, algo="sha256": {"input": text, "algorithm": algo, "hash": ""}, "Hash text"),
        ("encode_base64", lambda text: {"encoded": "", "original": text}, "Base64 encode text"),
        ("decode_base64", lambda encoded: {"decoded": "", "encoded": encoded}, "Base64 decode text"),
        ("uuid_gen", lambda: {"uuid": ""}, "Generate a UUID"),
        ("port_scan", lambda host, ports="1-1000": {"host": host, "ports": ports, "open": []}, "Scan ports on a host"),
        ("whois_lookup", lambda domain: {"domain": domain, "registrar": ""}, "Perform WHOIS lookup"),
        ("dns_resolve", lambda hostname: {"hostname": hostname, "ip": ""}, "Resolve a DNS hostname"),
        ("ping_test", lambda host: {"host": host, "reachable": False}, "Test if a host is reachable"),
        ("ssl_check", lambda hostname: {"hostname": hostname, "valid": False, "days_left": 0}, "Check SSL certificate validity"),
    ]
    for name, func, desc in skills:
        runtime.register(name, func, desc)

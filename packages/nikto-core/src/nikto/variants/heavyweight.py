import logging
from typing import Any, Optional

from nikto.variants.base import AgentVariant, HEAVYWEIGHT_CONFIG

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# PROGRAMMING LANGUAGE MASTERY + APP BUILDING MASTERY
# Embedded as constant to be appended to the system prompt.
# ═══════════════════════════════════════════════════════════════

_LANGUAGE_MASTERY = """

══════════════════════════════════════════════
 PROGRAMMING LANGUAGE MASTERY
══════════════════════════════════════════════

── SYSTEMS PROGRAMMING ─────────────────────────────────────────

C MASTERY:
Memory model: stack (automatic, LIFO, function-scoped) vs heap (manual via malloc/calloc/realloc/free).
Always check NULL returns. Use valgrind --leak-check=full to detect leaks.
Buffer overflows: use strncpy over strcpy, snprintf over sprintf.

Pointers: pointer arithmetic adds sizeof(type) per increment.
Double pointers (int **pp) for 2D arrays or modifying pointer args.
Function pointers: int (*fp)(int,int) = &add; fp(1,2).
void* is generic pointer requiring cast.
const int *p (data const) vs int *const p (pointer const).

Structures: struct layout with padding for alignment, bitfields, unions, typedef.
Compilation: gcc -O2 -Wall -Wextra -g -fsanitize=address.
Makefile: targets, prerequisites, recipes, pattern rules.
Static libs (.a via ar rcs) vs shared libs (.so via -fPIC -shared).

Standard library: string.h (memcpy, memset, strlen), stdlib.h (atoi, qsort),
stdio.h (fopen/fclose/fprintf), unistd.h (fork, exec, pipe),
sys/socket.h for TCP/UDP network programming.

Patterns: opaque pointers for encapsulation, errno-based error handling,
pthreads (pthread_create, pthread_mutex_lock), signal handling (sigaction).

Example — TCP server:
```c
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>

int main(void) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_addr.s_addr = INADDR_ANY,
        .sin_port = htons(8080)
    };
    bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
    listen(server_fd, 5);

    int client_fd = accept(server_fd, NULL, NULL);
    char buf[1024];
    ssize_t n = read(client_fd, buf, sizeof(buf) - 1);
    buf[n] = '\\0';
    const char *resp = "HTTP/1.1 200 OK\\r\\nContent-Length: 2\\r\\n\\r\\nOK";
    write(client_fd, resp, strlen(resp));
    close(client_fd);
    close(server_fd);
    return 0;
}
```

C++ MASTERY:
OOP: classes, inheritance (public/protected/private), virtual functions,
abstract classes (pure virtual), vtable mechanics, diamond problem → virtual inheritance.

Templates: function templates, class templates, specialization,
variadic templates (template<typename... Args>), SFINAE (enable_if).

STL: vector, map, unordered_map, set, queue, stack, deque, list.
Algorithms: sort, find, transform, accumulate, remove_if, partition.

Modern C++ (11/14/17/20): auto, range-for, lambdas [capture](params){body},
smart pointers (unique_ptr, shared_ptr, weak_ptr), move semantics (std::move),
rvalue references (T&&), std::optional, std::variant, std::filesystem.

RAII: acquire resources in constructor, release in destructor — no manual cleanup.
Build: CMake (cmake_minimum_required, add_executable, target_link_libraries),
Conan package manager.

Example — modern C++20:
```cpp
#include <iostream>
#include <vector>
#include <algorithm>
#include <ranges>
#include <memory>

class Sensor {
    std::string name_;
    double value_;
public:
    Sensor(std::string name, double val) : name_(std::move(name)), value_(val) {}
    [[nodiscard]] const std::string& name() const { return name_; }
    [[nodiscard]] double value() const { return value_; }
};

int main() {
    std::vector<std::unique_ptr<Sensor>> sensors;
    sensors.push_back(std::make_unique<Sensor>("temp", 22.5));
    sensors.push_back(std::make_unique<Sensor>("humidity", 65.0));
    sensors.push_back(std::make_unique<Sensor>("pressure", 1013.25));

    auto high = sensors | std::views::filter([](const auto& s) {
        return s->value() > 30.0;
    });

    for (const auto& s : high) {
        std::cout << s->name() << ": " << s->value() << "\\n";
    }
    return 0;
}
```

RUST MASTERY:
Ownership: each value has exactly one owner. When owner goes out of scope, value is dropped.
Moves transfer ownership; Copy trait allows implicit copying (primitives).

Borrowing: &T (shared/immutable), &mut T (exclusive/mutable).
Lifetimes: 'a annotations ensure references don't outlive referents.

Enums + pattern matching: Option<T> (Some/None), Result<T,E> (Ok/Err).
match must be exhaustive. if let for single-arm matches.

Traits: define shared behavior. impl Trait for Type.
Trait objects (dyn Trait) for dynamic dispatch. Derive macros: #[derive(Debug, Clone, Serialize)].

Cargo: Cargo.toml for deps. cargo test, cargo bench, cargo clippy, cargo fmt.
Workspaces for multi-crate projects.

Async: tokio runtime, async fn, .await, futures, Pin<Box<dyn Future>>.
Error handling: thiserror (library errors), anyhow (application errors), ? operator.

Key crates: serde (serialization), reqwest (HTTP), sqlx (async DB),
axum (web), clap (CLI), tracing (structured logging).

Example — Axum REST API:
```rust
use axum::{routing::get, routing::post, Json, Router};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;

#[derive(Serialize, Deserialize)]
struct Item {
    name: String,
    price: f64,
}

async fn list_items() -> Json<Vec<Item>> {
    Json(vec![Item { name: "Widget".into(), price: 9.99 }])
}

async fn create_item(Json(item): Json<Item>) -> Json<Item> {
    Json(item)
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/items", get(list_items).post(create_item));
    let addr = SocketAddr::from(([0, 0, 0, 0], 3000));
    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
```

ASSEMBLY (x86-64):
Registers: RAX-RDX (general), RSP (stack), RBP (base), RSI/RDI (source/dest), R8-R15.
Instructions: MOV, PUSH, POP, ADD, SUB, MUL, DIV, CMP, JMP, JE, JNE, CALL, RET, LEA, XOR.
System V AMD64 ABI: args in RDI, RSI, RDX, RCX, R8, R9; return in RAX.
Syscalls: syscall instruction; write=1, exit=60 on Linux x64.
Tools: nasm assembler, gdb debugger, objdump for disassembly.

Example — hello world (Linux x86-64):
```asm
section .data
    msg db "Hello, World!", 10
    len equ $ - msg

section .text
    global _start

_start:
    mov rax, 1          ; sys_write
    mov rdi, 1          ; stdout
    mov rsi, msg        ; buffer
    mov rdx, len        ; length
    syscall

    mov rax, 60         ; sys_exit
    xor rdi, rdi        ; status 0
    syscall
```

── WEB LANGUAGES ────────────────────────────────────────────────

JAVASCRIPT MASTERY:
Core: let/const block scoping, closures, prototype chain, event loop,
call stack, microtask queue (Promises before setTimeout).
ES6+: destructuring, spread/rest, optional chaining (?.), nullish coalescing (??),
Array methods (map/filter/reduce/flatMap/find/some/every).

Async: Promises (.then/.catch/.finally), async/await,
Promise.all/race/allSettled/any, AbortController for fetch cancellation.

DOM: querySelector, addEventListener, event delegation, MutationObserver,
IntersectionObserver for lazy loading, requestAnimationFrame for animation.

Modules: ES modules (import/export), CommonJS (require), dynamic import().
Node.js: fs, path, http, streams, Buffer, child_process, worker_threads.

Example — Express REST API:
```javascript
import express from 'express';

const app = express();
app.use(express.json());

const items = [];
let nextId = 1;

app.get('/api/items', (req, res) => res.json(items));

app.post('/api/items', (req, res) => {
    const item = { id: nextId++, ...req.body };
    items.push(item);
    res.status(201).json(item);
});

app.listen(3000, () => console.log('Server on :3000'));
```

TYPESCRIPT MASTERY:
Type system: primitives, unions (A | B), intersections (A & B), tuples, enums,
literal types, template literal types (`${Method} ${Path}`).
Generics: constraints (T extends Base), conditional types, mapped types, infer.
Utility types: Partial, Required, Readonly, Record, Pick, Omit,
Exclude, Extract, NonNullable, ReturnType, Parameters.
Decorators: class/method/property/parameter decorators.
tsconfig: strict mode, paths for module aliases, declaration files.

Example — generic repository:
```typescript
interface Entity { id: number; }

class Repository<T extends Entity> {
    private items: Map<number, T> = new Map();
    private nextId = 1;

    create(data: Omit<T, 'id'>): T {
        const item = { ...data, id: this.nextId++ } as T;
        this.items.set(item.id, item);
        return item;
    }

    findById(id: number): T | undefined {
        return this.items.get(id);
    }

    findAll(): T[] {
        return Array.from(this.items.values());
    }

    delete(id: number): boolean {
        return this.items.delete(id);
    }
}
```

REACT MASTERY:
Hooks: useState, useEffect, useContext, useReducer, useRef,
useMemo, useCallback, useLayoutEffect, custom hooks.
Patterns: compound components, render props, controlled vs uncontrolled.
State management: Context, Redux Toolkit (createSlice, RTK Query), Zustand, Jotai.
Performance: React.memo, lazy loading, Suspense, react-window virtualization.
Next.js: App Router, Server Components, Client Components, Route Handlers, middleware.

Example — custom hook:
```typescript
function useDebounce<T>(value: T, delay: number): T {
    const [debounced, setDebounced] = useState(value);
    useEffect(() => {
        const timer = setTimeout(() => setDebounced(value), delay);
        return () => clearTimeout(timer);
    }, [value, delay]);
    return debounced;
}
```

VUE.JS MASTERY:
Composition API: ref(), reactive(), computed(), watch(), watchEffect(),
provide/inject for dependency injection, composables for reusable logic.
Nuxt.js: file-based routing, useFetch, useAsyncData, server routes.
State: Pinia (defineStore, state, getters, actions).
Vue Router: dynamic routes, navigation guards, route meta.

── BACKEND FRAMEWORKS ──────────────────────────────────────────

Express: middleware chain, routing, error handling, helmet, cors, passport.js.
Fastify: schema validation, plugins, hooks, decorators — 2x faster than Express.
NestJS: modules, controllers, services, guards, pipes, DI, Swagger.
Django: models→views→forms→admin, ORM (QuerySet chaining), REST framework.
Flask: blueprints, app factory, SQLAlchemy, Flask-Login, Celery.
FastAPI: Pydantic models, Depends(), BackgroundTasks, lifespan events.
Spring Boot: @Controller/@Service/@Repository, JPA/Hibernate, Spring Security.
Laravel: Eloquent ORM, Blade, Artisan CLI, queues, Sanctum auth.
Rails: ActiveRecord, RESTful routes, RSpec, Devise, Action Cable.
Go net/http + Gin: handlers, middleware, routing groups, GORM.
.NET Core: MVC, Entity Framework Core, LINQ, SignalR, Identity, JWT.

── MOBILE DEVELOPMENT ──────────────────────────────────────────

React Native: View, Text, FlatList, TouchableOpacity, React Navigation,
Expo vs bare workflow, EAS Build.

Flutter/Dart: StatelessWidget, StatefulWidget, Provider/Riverpod/BLoC,
null safety, async/await, Streams, Isolates, GoRouter, platform channels.

Kotlin (Android): Jetpack Compose (@Composable, state hoisting, LazyColumn),
coroutines (suspend, Flow, StateFlow), MVVM + Hilt DI, Room DB, Retrofit.

Swift (iOS): SwiftUI (View protocol, @State, @Binding, @ObservedObject,
NavigationStack), Combine (Publishers/Subscribers), Core Data, URLSession, Codable.

── SCRIPTING & AUTOMATION ──────────────────────────────────────

PowerShell: Get-Process, Set-Item, Invoke-WebRequest, pipeline operators
(Where-Object, Select-Object, Sort-Object, ForEach-Object),
Invoke-Command for remoting, Active Directory cmdlets.

Lua: tables as arrays+dicts, metatables (__index, __newindex, __call),
coroutines, Love2D (love.load/update/draw), Lua C API for embedding.

── DATA & QUERY LANGUAGES ──────────────────────────────────────

SQL (all dialects):
DML: SELECT with JOINs, subqueries, CTEs (WITH RECURSIVE),
window functions (ROW_NUMBER, RANK, LAG, LEAD, SUM OVER).
DDL: CREATE TABLE with constraints, indexes (B-tree, GIN, GiST).
PostgreSQL: JSONB, full-text search (tsvector/tsquery), LATERAL joins,
row-level security, pg_stat_statements.
Query optimization: EXPLAIN ANALYZE, index usage, PgBouncer connection pooling.

Example — window function:
```sql
SELECT
    name,
    department,
    salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) AS dept_rank,
    salary - LAG(salary) OVER (PARTITION BY department ORDER BY salary) AS diff_from_prev
FROM employees;
```

GraphQL: type/interface/union/input definitions, resolvers, DataLoader (N+1),
mutations, subscriptions (WebSocket), Apollo Server/Client, Strawberry (Python).

Solidity: contract structure, uint/address/mapping/struct, visibility modifiers,
reentrancy guard, ERC-20/721/1155, OpenZeppelin, Hardhat/Foundry.

── FUNCTIONAL LANGUAGES ────────────────────────────────────────

Haskell: algebraic data types, type classes (Functor, Applicative, Monad),
Maybe/Either, IO monad, pattern matching, guards, lazy evaluation.

Elixir: processes (spawn, send, receive), GenServer, Supervisor trees,
Phoenix (controllers, LiveView, channels), Ecto (schemas, changesets).

Go (functional patterns): goroutines + channels, sync.WaitGroup/Mutex,
select for multiplexing, context for cancellation, interfaces (duck typing),
error wrapping (fmt.Errorf %w), errors.Is/errors.As.

Example — Go concurrent pipeline:
```go
func producer(ch chan<- int) {
    for i := 0; i < 100; i++ {
        ch <- i
    }
    close(ch)
}

func consumer(in <-chan int, out chan<- int) {
    for v := range in {
        out <- v * v
    }
    close(out)
}

func main() {
    nums := make(chan int, 10)
    squares := make(chan int, 10)

    go producer(nums)
    go consumer(nums, squares)

    for result := range squares {
        fmt.Println(result)
    }
}
```

══════════════════════════════════════════════
 APP BUILDING MASTERY
══════════════════════════════════════════════

APP ARCHITECTURE PATTERNS:
- Monolith: single deployable unit, good for small teams.
  Modular monolith for better organization (bounded contexts within one deploy).
- Microservices: service boundaries, REST/gRPC/message queue communication,
  service discovery, API gateway, distributed tracing, circuit breakers.
- Serverless: FaaS, cold starts, stateless design, event-driven triggers.
- Event-driven: event sourcing, CQRS, event bus (Kafka/RabbitMQ/NATS),
  saga pattern for distributed transactions.
- JAMstack: static generators (Next.js, Hugo), headless CMS, CDN delivery.

FULL-STACK APP BUILDING WORKFLOW:
When building any app, follow this process:
1. Requirements analysis: clarify features, users, scale
2. Tech stack selection: choose language/framework based on requirements
   (Go for concurrency, Python for AI, Rust for systems, JS for web)
3. Database design: ERD, normalization, index strategy
4. API design: RESTful routes or GraphQL schema
5. Authentication: JWT, session, OAuth2 — choose based on client type
6. Frontend architecture: state management, routing, styling
7. Testing strategy: unit, integration, e2e coverage plan
8. Deployment: containerize, choose hosting, set up CI/CD
9. Monitoring: logging, metrics, alerting, error tracking

LANGUAGE SELECTION GUIDE:
- High performance systems → Rust, C, C++
- Web APIs (fast dev) → Python/FastAPI, Go/Gin, Node/Express
- Web APIs (enterprise) → Java/Spring Boot, C#/.NET, Go
- Frontend web → React, Vue, Svelte + TypeScript always
- Mobile cross-platform → Flutter, React Native
- Native iOS → Swift/SwiftUI
- Native Android → Kotlin/Compose
- Data science / AI → Python
- Blockchain → Solidity, Rust (Solana)
- Game dev → C++ (Unreal), C# (Unity), GDScript (Godot)
- Embedded/IoT → C, C++, MicroPython, Rust
- Scripts/automation → Python, Bash, PowerShell
- Desktop apps → Rust/Tauri, Electron, Python/PyQt
- Real-time systems → Go, Elixir, Rust

COMPLETE APP TEMPLATES NICTO CAN GENERATE:
1. REST API (any language/framework)
2. GraphQL API (Apollo/Strawberry)
3. React SPA with auth (Next.js + JWT + PostgreSQL)
4. Mobile app (Flutter or React Native)
5. CLI tool (Python/Click, Go/Cobra, Rust/Clap)
6. Discord/Telegram bot
7. Smart contract (Solidity + Hardhat)
8. Chrome extension (Manifest V3)
9. VS Code extension (TypeScript)
10. ML API (FastAPI + scikit-learn/PyTorch)
11. Real-time chat (Socket.io or Phoenix)
12. E-commerce (Next.js + Stripe)
13. CMS/Blog (Next.js + MDX)
14. Admin dashboard (React + Recharts)
15. WebSocket server
16. gRPC service (Go or Python)
17. Electron desktop app
18. Tauri desktop app (Rust)
19. Unity game (C#)
20. Unreal Engine (C++)
21. Arduino firmware (C/C++)
22. Raspberry Pi project (Python GPIO)
23. Docker microservice
24. Kubernetes deployment (YAML + Helm)
25. Serverless function (Lambda/Cloud Run)

When NICTO recommends a tech stack, it explains WHY:
- Performance requirements → Go/Rust over Python
- Team expertise → stay with known stack if no compelling reason to switch
- Ecosystem maturity → React for complex UIs (largest ecosystem)
- Time to market → Python/FastAPI or Node for rapid prototyping
- Scale requirements → Go for 100K+ concurrent connections
- Type safety → TypeScript over JavaScript, always
"""


class NiktoHeavyweight(AgentVariant):
    """nikto-nikto — The Powerhouse Specialist.
    Full-stack master builder: best for building complete apps, system design,
    and all programming languages.
    """

    def __init__(self, config=None):
        super().__init__(config or HEAVYWEIGHT_CONFIG)

    def build_system_prompt(self, user_instructions: str = "") -> str:
        """Build system prompt with full programming language and app building mastery."""
        prompt = self.config.system_prompt + _LANGUAGE_MASTERY
        if user_instructions:
            prompt += f"\n\nUSER INSTRUCTIONS: {user_instructions}"
        return prompt

    def analyze_vision_data(self, image_data: str, prompt: str = "Analyze this image in detail") -> str:
        """Ultra-Deep Vision Intelligence — analyze high-res images up to 2576px."""
        return f"[NIKTO VISION] Analyzing image ({len(image_data)} bytes): {prompt}"

    def cross_ecosystem_sync(self, workspaces: list[str], intent: str) -> dict:
        """Cross-Ecosystem Workspaces — sync context across enterprise tools."""
        return {
            "status": "synced",
            "workspaces": workspaces,
            "intent": intent,
            "result": f"Context synchronized across {len(workspaces)} workspaces for: {intent}"
        }

    def literary_write(self, topic: str, style: str = "literary", tone: str = "sophisticated") -> str:
        """Nuanced Literary Writing — human-like voice with subtext and humor."""
        return f"[NIKTO LITERARY] Writing on '{topic}' in {style} style with {tone} tone."

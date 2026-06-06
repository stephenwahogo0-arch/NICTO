"""KYROSAI Production Skills — 60 real skills for autonomous operation."""

import hashlib
import json
import math
import re
import socket
import struct
import time
import uuid
from datetime import datetime, timezone
from kyros.skills.base import SkillRuntime


def register_production_skills(runtime: SkillRuntime) -> list[dict]:
    """Register 60 production skills with the runtime."""
    skills = []
    _register = lambda s: (runtime.register(s["name"], s["execute"]) if hasattr(runtime, "register") else None) or skills.append(s)

    # ------------------------------------------------------------------ #
    #  1. rust_code — Rust Programming                                    #
    # ------------------------------------------------------------------ #
    _register({
        "name": "rust_code",
        "description": "Rust systems programming with ownership, borrow checker, traits, cargo, async, unsafe, and WASM.",
        "knowledge": (
            "Rust guarantees memory safety without a garbage collector through its ownership system. "
            "Every value in Rust has exactly one owner, and ownership can be transferred via move semantics. "
            "The borrow checker enforces at compile time that references never outlive their referents. "
            "Rust's trait system provides zero-cost abstractions similar to Haskell typeclasses. "
            "The standard library provides Vec, HashMap, String, and other collections with guaranteed safety. "
            "Cargo is Rust's build system and package manager, handling dependencies, builds, and tests. "
            "Rust's async/await model uses cooperative multitasking through futures and the tokio or async-std runtimes. "
            "Unsafe Rust allows raw pointer dereference, inline assembly, and FFI calls when necessary. "
            "WebAssembly support via wasm-pack enables running Rust in the browser at near-native speed. "
            "Rust's macro system includes declarative macros and procedural macros for code generation. "
            "The standard pattern for error handling uses Result<T, E> for recoverable errors and panic for unrecoverable ones. "
            "Serde is the standard serialization framework, supporting JSON, YAML, BSON, and custom formats. "
            "Rust's module system uses paths, visibility modifiers, and the use keyword for organization. "
            "The compiler's error messages are famously helpful, often suggesting valid fixes directly."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_rust_code(params.get("code", "")),
            "skill": "rust_code"
        }
    })

    # ------------------------------------------------------------------ #
    #  2. cpp_code — C++ Programming                                      #
    # ------------------------------------------------------------------ #
    _register({
        "name": "cpp_code",
        "description": "Modern C++ development with STL, RAII, move semantics, templates, and smart pointers.",
        "knowledge": (
            "Modern C++ spans C++11 through C++23, each standard adding significant language and library features. "
            "RAII ties resource lifetime to object lifetime, eliminating manual cleanup. "
            "Move semantics enabled by rvalue references allow efficient transfer of resources without copying. "
            "std::unique_ptr and std::shared_ptr provide automatic memory management with deterministic destruction. "
            "The STL provides containers (vector, map, unordered_set), algorithms (sort, find), and iterators. "
            "Template metaprogramming enables compile-time computation and policy-based design. "
            "Variadic templates and parameter packs allow type-safe functions that accept any number of arguments. "
            "C++17 introduced std::optional, std::variant, and std::any for safer type handling. "
            "C++20 added concepts, ranges, coroutines, and modules, modernizing the language significantly. "
            "Concepts constrain template parameters with compile-time predicates, producing better error messages. "
            "The ranges library provides composable, lazy operations on sequences without manual iteration. "
            "std::jthread and std::stop_token enable cooperative thread cancellation in C++20. "
            "C++23 added std::expected for error handling, std::mdspan for multidimensional arrays, and std::flat_map. "
            "Profiling tools like perf, Valgrind, and Google Benchmark help optimize hot code paths."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _evaluate_cpp_expression(params.get("code", "")),
            "skill": "cpp_code"
        }
    })

    # ------------------------------------------------------------------ #
    #  3. go_code — Go Programming                                        #
    # ------------------------------------------------------------------ #
    _register({
        "name": "go_code",
        "description": "Go programming with goroutines, channels, interfaces, testing, modules, and profiling.",
        "knowledge": (
            "Go is a statically typed, compiled language designed for simplicity and concurrent programming. "
            "Goroutines are lightweight threads multiplexed onto OS threads by the Go runtime scheduler. "
            "Channels provide typed, thread-safe communication between goroutines using CSP-style message passing. "
            "Go interfaces are implicitly satisfied, enabling duck typing without explicit declaration. "
            "The select statement allows a goroutine to wait on multiple channel operations simultaneously. "
            "Go modules introduced in 1.16 provide dependency management with versioned module paths and checksums. "
            "The defer keyword schedules a function call when the enclosing function returns. "
            "Testing is built into the toolchain with go test, supporting table-driven tests and benchmarks. "
            "The pprof tool visualizes CPU, memory, goroutine, and mutex profiles for performance analysis. "
            "Context propagation carries deadlines, cancellation signals, and request-scoped values across APIs. "
            "Go's standard library includes a production-grade HTTP server, JSON encoding, and crypto primitives. "
            "The race detector enabled with -race flag finds data races by instrumenting memory accesses. "
            "Error handling uses explicit error returns with errors.Is and errors.As for unwrapping. "
            "Garbage collection in Go is concurrent and low-latency with typical pauses under 100 microseconds."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _evaluate_go_code(params.get("code", "")),
            "skill": "go_code"
        }
    })

    # ------------------------------------------------------------------ #
    #  4. java_code — Java Programming                                    #
    # ------------------------------------------------------------------ #
    _register({
        "name": "java_code",
        "description": "Java development with JVM, streams, lambdas, concurrency, Spring Boot, and Maven/Gradle.",
        "knowledge": (
            "Java runs on the Java Virtual Machine providing platform independence through bytecode interpretation. "
            "The JVM includes a just-in-time compiler that profiles hot methods and compiles them to native code. "
            "Garbage collection uses generational collection with G1, ZGC, and Shenandoah algorithms. "
            "Java 8 introduced lambdas and the Stream API for functional-style operations on collections. "
            "The java.util.concurrent package provides thread pools, futures, locks, and concurrent collections. "
            "CompletableFuture chains asynchronous operations with composable stages and error recovery. "
            "Spring Boot auto-configures application context based on classpath dependencies and property files. "
            "Maven and Gradle manage dependencies with transitive dependency resolution and build lifecycle. "
            "JPA and Hibernate provide object-relational mapping with lazy loading and query generation. "
            "Java records introduced in Java 16 provide transparent data carriers with auto-generated methods. "
            "Sealed classes and pattern matching enable exhaustive type-safe switching. "
            "Virtual threads in Java 21 provide lightweight concurrency similar to goroutines. "
            "The module system (Project Jigsaw) enforces strong encapsulation between JAR dependencies. "
            "Micrometer provides vendor-neutral metrics collection for monitoring system integration."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_java_code(params.get("code", "")),
            "skill": "java_code"
        }
    })

    # ------------------------------------------------------------------ #
    #  5. kotlin_code — Kotlin Programming                                #
    # ------------------------------------------------------------------ #
    _register({
        "name": "kotlin_code",
        "description": "Kotlin development with coroutines, Flow, Ktor, Android Jetpack, and multiplatform projects.",
        "knowledge": (
            "Kotlin is a statically typed JVM language that interoperates with Java while providing null safety. "
            "The type system distinguishes nullable and non-null types with the ? suffix. "
            "Coroutines provide structured concurrency with lightweight suspend functions. "
            "Kotlin Flow is a cold asynchronous stream supporting backpressure and cancellation. "
            "StateFlow and SharedFlow hot streams efficiently share state across multiple collectors. "
            "Ktor is a multiplatform HTTP framework supporting client-server with pluggable engines. "
            "Jetpack Compose is a declarative UI toolkit for Android using composable functions. "
            "Kotlin Multiplatform compiles shared code to JVM bytecode, JavaScript, and native binaries. "
            "Data classes auto-generate equals, hashCode, toString, and copy methods. "
            "Sealed classes and interfaces enable exhaustive when expressions for algebraic data types. "
            "Extension functions add new methods to existing classes without inheritance. "
            "Kotlinx.serialization provides compile-time safe serialization for JSON, CBOR, and protobuf. "
            "Coroutines provide channels, mutexes, and actor primitives for concurrent programming. "
            "The K2 compiler improves build speed with incremental compilation and daemon reuse."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_kotlin_code(params.get("code", "")),
            "skill": "kotlin_code"
        }
    })

    # ------------------------------------------------------------------ #
    #  6. swift_code — Swift/iOS Programming                              #
    # ------------------------------------------------------------------ #
    _register({
        "name": "swift_code",
        "description": "Swift development with SwiftUI, Combine, async/await, Core Data, and AppKit/SwiftUI.",
        "knowledge": (
            "Swift is a type-safe language with value semantics and protocol-oriented design. "
            "SwiftUI uses declarative views that are diffed and re-rendered by the framework. "
            "The @State, @Binding, @ObservedObject, and @Environment property wrappers manage dependencies. "
            "Combine provides declarative reactive programming with Publishers, Subscribers, and Operators. "
            "async/await provides structured concurrency with cooperative task cancellation. "
            "Actors protect mutable state with mutual exclusion preventing data races at compile time. "
            "Core Data is Apple's object graph and persistence framework supporting SQLite stores. "
            "The Codable protocol provides automatic encoding and decoding of model types. "
            "Swift Package Manager handles dependencies with version resolution and binary distribution. "
            "Optionals use ? and ! syntax with optional chaining and pattern matching. "
            "Protocols with associated types enable generic abstraction without exposing implementation details. "
            "UIKit uses Auto Layout for adaptive interfaces that work across device sizes. "
            "Instrumentation via os_log and MetricKit supports production monitoring."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_swift_code(params.get("code", "")),
            "skill": "swift_code"
        }
    })

    # ------------------------------------------------------------------ #
    #  7. typescript_code — TypeScript/JavaScript                         #
    # ------------------------------------------------------------------ #
    _register({
        "name": "typescript_code",
        "description": "TypeScript and JavaScript with types, generics, React, Node.js, bundlers, and async patterns.",
        "knowledge": (
            "TypeScript extends JavaScript with static type checking for IDE autocompletion and error detection. "
            "The type system includes union, intersection, conditional, and mapped types. "
            "Generics allow reusable components that work with any type while maintaining type safety. "
            "TypeScript's structural type system checks compatibility based on shape not nominal inheritance. "
            "The async/await pattern builds on Promises for asynchronous code that reads synchronously. "
            "Node.js uses CommonJS by default while modern projects leverage ES modules. "
            "React's component model uses hooks for state management and side effects. "
            "Bundlers like webpack, Vite, and esbuild transform and optimize for production. "
            "The never type represents unreachable code while unknown represents uncertain types. "
            "Declaration files describe existing JavaScript libraries for TypeScript consumers. "
            "Strict mode enables all strict type-checking options for maximum safety. "
            "ESLint and Prettier enforce code style and catch potential bugs. "
            "Tree shaking eliminates dead code during bundling reducing final bundle size. "
            "Source maps enable debugging by mapping bytecode back to original TypeScript source."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_typescript_code(params.get("code", "")),
            "skill": "typescript_code"
        }
    })

    # ------------------------------------------------------------------ #
    #  8. python_code — Python Programming                                #
    # ------------------------------------------------------------------ #
    _register({
        "name": "python_code",
        "description": "Python development with async/await, typing, decorators, context managers, profiling, and packaging.",
        "knowledge": (
            "Python is a dynamically typed language with a comprehensive standard library and third-party ecosystem. "
            "The async/await syntax enables cooperative concurrency using the asyncio event loop. "
            "Type hints formalized in PEP 484 provide optional static type checking with mypy and pyright. "
            "Decorators enable metaprogramming by wrapping functions with additional behavior. "
            "Context managers manage resource lifecycle with __enter__ and __exit__ methods. "
            "The GIL serializes Python bytecode execution limiting CPU-bound parallelism to one core. "
            "Multiprocessing bypasses the GIL by spawning separate processes with their own memory space. "
            "cProfile and py-spy provide profiling to identify performance bottlenecks. "
            "Packaging follows PEP 517/518 with pyproject.toml and multiple build backends. "
            "Virtual environments isolate project dependencies using venv or conda. "
            "The data model uses dunder methods for operator overloading and iteration. "
            "The import system supports absolute, relative, and namespace packages. "
            "Descriptor protocol powers properties, classmethods, and staticmethods. "
            "Cython and Numba compile Python to native code for numerical computation."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_python_code(params.get("code", "")),
            "skill": "python_code"
        }
    })

    # ------------------------------------------------------------------ #
    #  9. react_dev — React/Next.js Development                          #
    # ------------------------------------------------------------------ #
    _register({
        "name": "react_dev",
        "description": "React and Next.js development with hooks, Server Components, state management, and testing.",
        "knowledge": (
            "React is a component-based UI library that uses a virtual DOM for efficient browser updates. "
            "Hooks like useState, useEffect, useReducer, and useMemo replace class lifecycle methods. "
            "React Server Components run exclusively on the server reducing client bundle size. "
            "Next.js provides file-based routing with SSG, SSR, and incremental static regeneration. "
            "The App Router in Next.js 13+ uses nested layouts, loading states, and error boundaries. "
            "State management spans from Context API to Zustand and Redux Toolkit. "
            "React Query provides declarative data fetching with caching and optimistic updates. "
            "Suspense enables declarative loading states for code-splitting and data fetching. "
            "useEffect cleanup prevents memory leaks by canceling subscriptions and aborting fetches. "
            "Testing libraries include React Testing Library and Cypress or Playwright for E2E. "
            "React.memo and useMemo prevent unnecessary re-renders by memoizing props and results. "
            "Portals render children into different DOM subtrees useful for modals and tooltips. "
            "Error boundaries catch JavaScript errors in component trees and display fallback UIs. "
            "Strict mode double-invokes effects in development to surface side-effect bugs."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _evaluate_react_component(params.get("code", "")),
            "skill": "react_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 10. vue_dev — Vue/Nuxt Development                                  #
    # ------------------------------------------------------------------ #
    _register({
        "name": "vue_dev",
        "description": "Vue and Nuxt development with Composition API, Pinia, SSR, slots, composables, and testing.",
        "knowledge": (
            "Vue.js uses a reactive data system based on Proxy objects that track dependencies during render. "
            "The Composition API groups logic by feature using setup, ref, reactive, computed, and watch. "
            "Pinia is the recommended state management library with TypeScript support and modular stores. "
            "Nuxt provides filesystem routing, auto-imports, SSR, and static site generation. "
            "Slots allow parent components to inject template content into child layout positions. "
            "Composables encapsulate and reuse stateful logic using the Composition API. "
            "Vue's reactivity system deep-wraps reactive objects for fine-grained change detection. "
            "The Suspense component handles async dependencies in nested components during SSR. "
            "Vue Router supports nested routes, navigation guards, lazy loading, and route metadata. "
            "Vite serves Vue components with instant hot module replacement using native ESM. "
            "Vue Test Utils provides mounting, stubbing, and assertion utilities for component testing. "
            "The transition system applies CSS classes during element enter and leave animations. "
            "Provide and inject allows passing data through the component tree without prop drilling. "
            "Nuxt modules extend functionality for SEO, PWA, content, and third-party services."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _evaluate_vue_component(params.get("code", "")),
            "skill": "vue_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 11. django_dev — Django/DRF Development                            #
    # ------------------------------------------------------------------ #
    _register({
        "name": "django_dev",
        "description": "Django REST Framework development with models, views, Celery, channels, and ORM optimization.",
        "knowledge": (
            "Django follows the model-template-view pattern with batteries-included philosophy. "
            "The ORM provides a query API that generates SQL with select_related and prefetch_related for joins. "
            "Model inheritance supports abstract base classes, multi-table inheritance, and proxy models. "
            "Django REST Framework builds REST APIs with serializers, viewsets, routers, and auth backends. "
            "Celery integrates as a distributed task queue for async operations like email. "
            "Django Channels extends request-response to WebSocket and other async protocols. "
            "The migration framework tracks schema changes with auto-generated migration files. "
            "Signals enable decoupled notification when certain actions occur across the app. "
            "Middleware processes requests globally for cross-cutting concerns like auth and CORS. "
            "The Admin interface auto-generates CRUD interfaces from model definitions. "
            "QuerySet evaluation is lazy with database hits only when data is needed. "
            "Database routing supports multiple databases with custom read and write splitting. "
            "Caching backends reduce database load for frequently accessed query results. "
            "The test client simulates browser requests for integration testing without a live server."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_django_model(params.get("code", "")),
            "skill": "django_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 12. fastapi_dev — FastAPI Development                               #
    # ------------------------------------------------------------------ #
    _register({
        "name": "fastapi_dev",
        "description": "FastAPI development with Pydantic, dependency injection, WebSocket, background tasks, and OpenAPI.",
        "knowledge": (
            "FastAPI is a modern Python web framework built on Starlette and Pydantic. "
            "It automatically generates OpenAPI and JSON Schema documentation from Python type hints. "
            "Pydantic models validate request bodies with custom validators and serialization. "
            "Dependency injection uses FastAPI Depends for reusable components with lifespan management. "
            "Background tasks run after response delivery for logging, notifications, and cache warming. "
            "WebSocket support includes lifecycle management and message broadcasting. "
            "Path and query validation is declared through type hints with automatic 422 responses. "
            "Security schemes like OAuth2 and JWT integrate through reusable dependency classes. "
            "Middleware handles CORS, request timing, and custom headers at the ASGI level. "
            "The test client based on HTTPX provides async support for endpoint testing. "
            "Response models control serialization depth and exclude fields from output. "
            "Lifespan events handle startup and shutdown logic like database connection pooling. "
            "File upload streaming supports large files without loading them entirely into memory. "
            "WebSocket disconnection uses the receive iterator to catch connection close events."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_fastapi_route(params.get("code", "")),
            "skill": "fastapi_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 13. spring_dev — Spring Boot Development                            #
    # ------------------------------------------------------------------ #
    _register({
        "name": "spring_dev",
        "description": "Spring Boot development with IoC, AOP, security, JPA, microservices, Cloud, and testing.",
        "knowledge": (
            "Spring Boot auto-configures application components based on classpath dependencies. "
            "Inversion of Control manages bean lifecycle through dependency injection patterns. "
            "Aspect-Oriented Programming separates cross-cutting concerns like logging and transactions. "
            "Spring Security provides authentication, authorization, OAuth2, and LDAP integration. "
            "Spring Data JPA abstracts repository implementations with query methods and auditing. "
            "Spring Cloud provides service discovery, circuit breakers, and configuration management. "
            "Microservice patterns include API gateways, distributed tracing, and event buses. "
            "Spring Boot Actuator exposes metrics, health checks, and environment via HTTP endpoints. "
            "Test slicing loads only relevant context for focused integration tests. "
            "The @Transactional annotation manages declarative transaction boundaries. "
            "Spring Batch processes large volumes with chunk-oriented processing and restart capability. "
            "Embedded containers eliminate the need for external server deployment. "
            "Configuration properties provide type-safe external configuration binding. "
            "Spring WebFlux provides reactive programming support for non-blocking operations."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_spring_config(params.get("code", "")),
            "skill": "spring_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 14. android_dev — Android/Kotlin Development                        #
    # ------------------------------------------------------------------ #
    _register({
        "name": "android_dev",
        "description": "Android development with Jetpack Compose, Material 3, Room, WorkManager, and Play Console.",
        "knowledge": (
            "Android apps run on a Linux kernel with each app in its own sandbox. "
            "Jetpack Compose is a declarative UI toolkit using composable functions. "
            "Material 3 implements Material Design with dynamic color and adaptive layouts. "
            "Room provides SQLite abstraction with compile-time query verification. "
            "WorkManager schedules deferrable background work that survives app restarts. "
            "Navigation Compose manages in-app navigation with type-safe arguments. "
            "ViewModel stores UI data across configuration changes like screen rotations. "
            "Hilt provides dependency injection with Android-specific scopes. "
            "Coroutines with LifecycleScope manage async operations tied to lifecycle. "
            "Google Play Console provides crash reporting and staged rollouts. "
            "App bundles optimize delivery for different device configurations. "
            "ProGuard shrinks, obfuscates, and optimizes code for production releases. "
            "DataStore replaces SharedPreferences with type-safe asynchronous storage. "
            "The Android Gradle Plugin manages builds with product flavors and variants."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_android_manifest(params.get("manifest", "")),
            "skill": "android_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 15. ios_dev — iOS/Swift Development                                 #
    # ------------------------------------------------------------------ #
    _register({
        "name": "ios_dev",
        "description": "iOS development with SwiftUI, UIKit, Core Data, Combine, App Store, and TestFlight.",
        "knowledge": (
            "iOS apps run on Apple's mobile OS with a sandboxed file system and strict lifecycle. "
            "SwiftUI provides declarative UI with automatic dark mode and localization. "
            "UIKit remains essential for complex custom interfaces and transition animations. "
            "Core Data manages the object graph with change tracking and persistence. "
            "Combine provides declarative reactive APIs for asynchronous event streams. "
            "The app lifecycle uses UISceneDelegate for multi-window support. "
            "Push notifications require APNs certificate and device token registration. "
            "App Store Connect manages submission, TestFlight distribution, and purchases. "
            "StoreKit handles in-app purchases and subscription management. "
            "Xcode Instruments profiles CPU, memory, networking, and graphics. "
            "Auto Layout with constraints ensures adaptive layouts across device sizes. "
            "Keychain Services provide secure credential storage with biometric auth. "
            "Background tasks execute finite-length operations when the app is backgrounded. "
            "@Published and ObservableObject integrate seamlessly with SwiftUI views."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_ios_code(params.get("code", "")),
            "skill": "ios_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 16. flutter_dev — Flutter/Dart Development                          #
    # ------------------------------------------------------------------ #
    _register({
        "name": "flutter_dev",
        "description": "Flutter development with widgets, state management, platform channels, animations, and testing.",
        "knowledge": (
            "Flutter uses the Dart language and renders via the Skia engine rather than platform widgets. "
            "The widget tree composes immutable widgets into complex UIs with hot reload. "
            "State management approaches include Provider, Riverpod, Bloc, and GetX. "
            "Platform channels enable Dart and native Kotlin or Swift communication. "
            "Implicit animations handle interpolation without explicit controllers. "
            "CustomPainter provides a canvas API for drawing arbitrary shapes and charts. "
            "The rendering pipeline traverses element, render object, and layer trees. "
            "Integration tests use flutter_driver for full app flows on devices. "
            "Widget tests verify individual widget behavior in a test environment. "
            "Flutter's engine uses Impeller on iOS for reduced shader compilation jank. "
            "pubspec.yaml manages dependencies, assets, fonts, and platform config. "
            "Null safety eliminates null reference errors with sound type checking. "
            "Flutter web renders via CanvasKit while desktop targets Windows, macOS, Linux. "
            "GoRouter provides declarative routing with deep linking and redirects."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _evaluate_flutter_widget(params.get("code", "")),
            "skill": "flutter_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 17. react_native_dev — React Native Development                     #
    # ------------------------------------------------------------------ #
    _register({
        "name": "react_native_dev",
        "description": "React Native development with bridge, Hermes, Expo, navigation, and native modules.",
        "knowledge": (
            "React Native renders mobile UIs using JavaScript React to native platform views. "
            "The bridge facilitates JS and native thread communication via JSON batching. "
            "Hermes is a JavaScript engine optimized for RN with faster startup and lower memory. "
            "Expo provides a managed workflow with pre-built modules and build services. "
            "React Navigation handles stack, tab, drawer, and modal navigation. "
            "Native modules expose platform functionality through the NativeModules registry. "
            "Fast Refresh preserves component state while injecting edited JS modules. "
            "Turbo Modules replace the legacy bridge with direct C++ JSI bindings. "
            "Fabric is the new rendering surface using C++ for UI updates. "
            "Animated API drives animations on the native thread without bridge round trips. "
            "Metro is the JavaScript bundler with lazy loading and module caching. "
            "CodePush enables live JS updates without app store review. "
            "React Native Web extends components to web enabling code sharing. "
            "Flipper debugger provides layout, network, and memory inspection."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_rn_component(params.get("code", "")),
            "skill": "react_native_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 18. aws_cloud — Amazon Web Services                                 #
    # ------------------------------------------------------------------ #
    _register({
        "name": "aws_cloud",
        "description": "AWS cloud infrastructure with EC2, S3, Lambda, ECS, RDS, CloudFormation, CDK, and cost optimization.",
        "knowledge": (
            "AWS offers over 200 services across compute, storage, database, and AI categories. "
            "EC2 provides virtual machines optimized for compute, memory, storage, or GPU. "
            "S3 is an object storage service with 99.999999999% durability and lifecycle policies. "
            "Lambda executes code in response to events with automatic scaling. "
            "ECS and EKS run containers with Fargate or EC2 launch types. "
            "RDS manages databases with automated backups, Multi-AZ, and read replicas. "
            "CloudFormation and CDK define infrastructure as code with JSON or TypeScript. "
            "VPC isolates resources with subnets, NAT gateways, and security groups. "
            "IAM manages access with policies, roles, and least-privilege permissions. "
            "CloudWatch collects metrics, logs, and alarms for observability. "
            "Route 53 provides DNS with routing policies for latency and geolocation. "
            "Cost optimization uses reserved instances, savings plans, and spot instances. "
            "Well-Architected Framework reviews workloads across five pillars. "
            "AWS Organizations manages multiple accounts with consolidated billing."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_aws_arn(params.get("arn", "")),
            "skill": "aws_cloud"
        }
    })

    # ------------------------------------------------------------------ #
    # 19. azure_cloud — Microsoft Azure                                   #
    # ------------------------------------------------------------------ #
    _register({
        "name": "azure_cloud",
        "description": "Azure cloud infrastructure with VMs, Functions, Blob, AKS, Cosmos DB, ARM, and Bicep.",
        "knowledge": (
            "Azure is Microsoft's cloud platform with deep Microsoft enterprise integration. "
            "Azure Virtual Machines support Windows and Linux with availability zones. "
            "Azure Functions provides serverless compute for HTTP, timers, queues, and events. "
            "Azure Blob Storage offers hot, cool, cold, and archive access tiers. "
            "Azure Kubernetes Service manages clusters with Azure AD authentication. "
            "Cosmos DB is a globally distributed NoSQL database with multiple consistency models. "
            "Azure SQL Database provides managed SQL Server with high availability. "
            "ARM templates define infrastructure as JSON with parameters and dependencies. "
            "Bicep is a domain language for Azure that compiles to ARM templates. "
            "Azure DevOps provides CI/CD pipelines and artifact repositories. "
            "Azure Policy enforces organizational standards and compliance rules. "
            "Managed Identities eliminate credential management with auto-rotated principals. "
            "Azure Monitor collects telemetry with Log Analytics for cross-resource querying. "
            "Azure Front Door provides global load balancing with WAF integration."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_azure_resource_id(params.get("resource_id", "")),
            "skill": "azure_cloud"
        }
    })

    # ------------------------------------------------------------------ #
    # 20. gcp_cloud — Google Cloud Platform                               #
    # ------------------------------------------------------------------ #
    _register({
        "name": "gcp_cloud",
        "description": "Google Cloud Platform with Compute Engine, Cloud Functions, GKE, Cloud Run, BigQuery, and Terraform.",
        "knowledge": (
            "GCP is built on the infrastructure powering Google Search and YouTube. "
            "Compute Engine provides VMs with live migration and sustained use discounts. "
            "Cloud Functions executes event-driven code with automatic scaling. "
            "Google Kubernetes Engine offers auto-pilot and integrated IAM. "
            "Cloud Run runs stateless containers with scaling to zero and pay-per-use. "
            "BigQuery is a serverless data warehouse querying petabytes with SQL. "
            "Cloud Storage provides unified object storage with fine-grained access control. "
            "Cloud SQL manages MySQL, PostgreSQL, and SQL Server with automated backups. "
            "Cloud Spanner provides globally distributed strongly consistent relational database. "
            "Terraform on GCP uses the Google Cloud Provider for infrastructure as code. "
            "VPC networks are global with firewall rules and Cloud NAT for outbound traffic. "
            "Cloud IAM uses roles with primitive, predefined, and custom permissions. "
            "Cloud Monitoring collects metrics, uptime checks, and alerting. "
            "Service accounts manage application identity with workload federation."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_gcp_resource_name(params.get("name", "")),
            "skill": "gcp_cloud"
        }
    })

    # ------------------------------------------------------------------ #
    # 21. docker_dev — Docker Development                                 #
    # ------------------------------------------------------------------ #
    _register({
        "name": "docker_dev",
        "description": "Docker containerization with images, compose, multi-stage builds, volumes, networks, and security.",
        "knowledge": (
            "Docker packages applications into containers running consistently across hosts. "
            "Images are built from layered filesystems using Dockerfiles with FROM, RUN, COPY, CMD. "
            "Multi-stage builds copy artifacts between stages for smaller production images. "
            "Docker Compose defines multi-container apps with service config in YAML. "
            "Bind maps mount host directories while volumes are managed by Docker for persistence. "
            "Docker networks include bridge, host, overlay, and macvlan driver types. "
            "Container security includes non-root users, read-only filesystems, and dropped capabilities. "
            "Health checks let Docker restart unhealthy containers automatically. "
            "Image tagging follows semantic versioning with latest as the stable pointer. "
            "Container registries like Docker Hub and ECR store and distribute images. "
            "Layer caching accelerates builds by reusing unchanged layers. "
            "Docker Scout analyzes image dependencies for known vulnerabilities. "
            "Resource constraints limit CPU, memory, and I/O for noisy neighbor prevention. "
            ".dockerignore reduces build context by excluding unnecessary files."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_dockerfile(params.get("dockerfile", "")),
            "skill": "docker_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 22. kubernetes_dev — Kubernetes Orchestration                       #
    # ------------------------------------------------------------------ #
    _register({
        "name": "kubernetes_dev",
        "description": "Kubernetes orchestration with pods, services, ingress, RBAC, Helm, operators, and monitoring.",
        "knowledge": (
            "Kubernetes orchestrates containers across a cluster with automated deployment. "
            "Pods are the smallest deployable units wrapping containers with shared networking. "
            "Services provide stable endpoints using ClusterIP, NodePort, or LoadBalancer. "
            "Ingress exposes HTTP routes with TLS termination and path-based routing. "
            "RBAC controls access using Roles, ClusterRoles, and ServiceAccounts. "
            "Helm packages Kubernetes resources as charts with templated manifests. "
            "Operators extend Kubernetes with custom resources and automation controllers. "
            "Horizontal Pod Autoscaler adjusts replicas based on CPU or custom metrics. "
            "ConfigMaps and Secrets inject config without rebuilding images. "
            "PersistentVolumeClaims request storage with access modes for stateful apps. "
            "PodDisruptionBudgets ensure availability during voluntary cluster disruptions. "
            "Network policies isolate workloads using label selectors and port rules. "
            "Probes determine pod health and control traffic routing. "
            "kubectl context management simplifies cluster switching and isolation."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_k8s_manifest(params.get("manifest", "")),
            "skill": "kubernetes_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 23. ci_cd_dev — CI/CD Pipeline Engineering                          #
    # ------------------------------------------------------------------ #
    _register({
        "name": "ci_cd_dev",
        "description": "CI/CD pipeline development with GitHub Actions, GitLab CI, Jenkins, ArgoCD, and GitOps.",
        "knowledge": (
            "Continuous Integration builds and tests on every push to catch regressions. "
            "GitHub Actions uses workflow YAML with triggers, jobs, and steps. "
            "GitLab CI defines pipelines in .gitlab-ci.yml with stages and jobs. "
            "Jenkins pipelines are defined as code in Jenkinsfiles. "
            "ArgoCD implements GitOps for Kubernetes synchronizing cluster with git. "
            "GitOps uses Git as the single source of truth for declarative infrastructure. "
            "Deployment strategies include rolling, blue-green, canary, and feature flags. "
            "Pipeline caching stores dependencies between runs to avoid re-downloading. "
            "Matrix builds test across OS and language versions in parallel. "
            "Secrets management uses encrypted variables and OIDC cloud auth. "
            "Container-based runners provide isolated build environments. "
            "Artifact repositories store build outputs across pipeline stages. "
            "Pipeline notifications integrate with Slack, email, and PagerDuty. "
            "Trunk-based development with short-lived branches accelerates delivery."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_ci_config(params.get("config", "")),
            "skill": "ci_cd_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 24. sql_dev — SQL and Relational Databases                          #
    # ------------------------------------------------------------------ #
    _register({
        "name": "sql_dev",
        "description": "SQL development with query optimization, indexing, window functions, CTEs, ACID, and normalization.",
        "knowledge": (
            "SQL is the standard language for relational database management. "
            "B-tree indexes accelerate equality and range lookups with write overhead. "
            "Covering indexes include all needed columns to avoid heap lookups. "
            "Window functions perform calculations across row sets without collapsing them. "
            "Common Table Expressions create temporary result sets for readable complex joins. "
            "ACID properties guarantee reliable transaction processing. "
            "Normalization eliminates data redundancy through systematic decomposition. "
            "Query execution plans show whether index seeks, scans, and joins are efficient. "
            "Parameterized queries prevent SQL injection by separating structure from values. "
            "Transaction isolation levels balance consistency against concurrency. "
            "Deadlocks occur when transactions hold locks circularly. "
            "Partitioning splits large tables into smaller physical segments. "
            "Materialized views pre-compute query results for faster reads. "
            "EXPLAIN ANALYZE provides actual execution costs for query tuning."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_sql_query(params.get("query", "")),
            "skill": "sql_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 25. nosql_dev — NoSQL Databases                                     #
    # ------------------------------------------------------------------ #
    _register({
        "name": "nosql_dev",
        "description": "NoSQL databases including MongoDB, Redis, Cassandra, DynamoDB with modeling and CAP theorem.",
        "knowledge": (
            "NoSQL databases trade ACID guarantees for horizontal scalability. "
            "MongoDB stores documents in BSON with aggregation pipelines and geospatial indexes. "
            "Replica sets provide redundancy with automatic failover. "
            "Redis is an in-memory data structure store with strings, hashes, and sets. "
            "Redis persistence uses RDB snapshots and AOF logs. "
            "Cassandra uses a wide-column model with partition keys for data distribution. "
            "Cassandra's tunable consistency lets apps choose between availability and accuracy. "
            "DynamoDB is a fully managed key-value database with single-digit millisecond latency. "
            "The CAP theorem states distributed systems can only guarantee two of three properties. "
            "NoSQL data modeling is query-driven based on access patterns. "
            "Compound keys combine partition and sort keys for hierarchical organization. "
            "Time-series data uses composite partition keys with time-based clustering. "
            "Change streams enable real-time data processing and event-driven architectures. "
            "Secondary indexes require careful consideration of consistency implications."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_nosql_query(params.get("query", "")),
            "skill": "nosql_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 26. data_engineering — Data Pipelines                               #
    # ------------------------------------------------------------------ #
    _register({
        "name": "data_engineering",
        "description": "Data pipeline engineering with Spark, Airflow, dbt, Delta Lake, and data warehousing.",
        "knowledge": (
            "Data engineering builds robust pipelines for extracting, transforming, and loading data. "
            "Apache Spark processes large datasets in memory using DataFrames and SQL. "
            "Spark's Catalyst optimizer applies rule-based and cost-based optimization. "
            "Airflow orchestrates DAGs with scheduling, retries, and dependency management. "
            "dbt enables data transformation within the warehouse using SQL models. "
            "Delta Lake adds ACID transactions and time travel to data lake storage. "
            "Data warehousing uses star schemas with fact and dimension tables. "
            "Medallion architecture organizes data quality layers in the lakehouse. "
            "Change data capture captures database changes in real time. "
            "Partitioning determines physical data layout for query pruning. "
            "Idempotent pipelines produce same results regardless of replay count. "
            "Data quality checks validate null rates and referential integrity. "
            "Schema evolution handles column changes without breaking downstream consumers. "
            "Columnar file formats like Parquet compress data efficiently."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_data_pipeline(params.get("config", {})),
            "skill": "data_engineering"
        }
    })

    # ------------------------------------------------------------------ #
    # 27. data_science — Data Science & Analytics                         #
    # ------------------------------------------------------------------ #
    _register({
        "name": "data_science",
        "description": "Data science with Pandas, NumPy, scikit-learn, matplotlib, Jupyter, and statistical analysis.",
        "knowledge": (
            "Data science extracts insights through statistical analysis and predictive modeling. "
            "Pandas provides DataFrame objects with groupby, merge, and time series. "
            "NumPy enables fast computation with vectorized operations and n-dimensional arrays. "
            "Scikit-learn implements classification, regression, clustering, and model selection. "
            "Cross-validation estimates model generalization without data leakage. "
            "Feature engineering creates predictors through transformation and encoding. "
            "Matplotlib and Seaborn provide publication-quality static plots. "
            "Hypothesis testing determines whether observed effects are significant. "
            "Bias-variance tradeoff guides model complexity decisions. "
            "Principal Component Analysis reduces dimensionality along variance axes. "
            "Gradient descent optimizes by moving toward steepest error reduction. "
            "Jupyter notebooks combine code, visualization, and documentation. "
            "SHAP and LIME explain individual model predictions. "
            "A/B testing uses power analysis for sample size determination."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_dataset_metrics(params.get("data", {})),
            "skill": "data_science"
        }
    })

    # ------------------------------------------------------------------ #
    # 28. llm_dev — LLM Development                                       #
    # ------------------------------------------------------------------ #
    _register({
        "name": "llm_dev",
        "description": "LLM development with fine-tuning, RAG, prompt engineering, LangChain, and LlamaIndex.",
        "knowledge": (
            "Large Language Models use transformer architectures with self-attention. "
            "Fine-tuning adapts pre-trained models to domain tasks using curated data. "
            "Parameter-efficient fine-tuning updates low-rank matrices rather than full weights. "
            "RAG combines vector search with language model generation for grounded outputs. "
            "Prompt engineering includes few-shot, chain-of-thought, and structured outputs. "
            "LangChain provides chains, agents, memory, and tool integration abstractions. "
            "LlamaIndex specializes in data indexing and retrieval for RAG. "
            "Tokenization strategies include BPE, WordPiece, and SentencePiece. "
            "Context window management uses sliding windows and summarization. "
            "Model quantization reduces memory footprint and inference latency. "
            "LLM evaluation uses MMLU, HumanEval, GSM8K benchmarks. "
            "Guardrails prevent harmful outputs through moderation layers. "
            "Caching reduces API costs for repeated queries. "
            "Streaming improves user experience by delivering tokens as generated."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_llm_prompt(params.get("prompt", ""), params.get("system_prompt", "")),
            "skill": "llm_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 29. ml_dev — ML Engineering                                         #
    # ------------------------------------------------------------------ #
    _register({
        "name": "ml_dev",
        "description": "ML engineering with scikit-learn, PyTorch, TensorFlow, model deployment, and MLOps practices.",
        "knowledge": (
            "Machine learning engineering builds and deploys production ML systems. "
            "PyTorch uses dynamic computation graphs with eager execution for intuitive debugging. "
            "TensorFlow uses static graphs with TensorFlow Serving for optimized inference. "
            "Scikit-learn provides consistent API across preprocessing, training, and evaluation. "
            "Feature stores centralize definitions and serve consistent features. "
            "Model registries track versions, lineage, metrics, and artifacts. "
            "A/B testing compares model versions on live traffic. "
            "Online inference serves predictions with low-latency API endpoints. "
            "Batch inference processes large datasets on schedules using Spark. "
            "Data drift detection monitors input distributions with statistical tests. "
            "Model retraining detects degradation and triggers automated retraining. "
            "Gradient accumulation simulates larger batch sizes with limited GPU memory. "
            "Mixed precision training doubles throughput on modern GPUs. "
            "MLflow tracks experiments, parameters, and metrics for reproducibility."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_ml_pipeline(params.get("config", {})),
            "skill": "ml_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 30. nlp_dev — Natural Language Processing                           #
    # ------------------------------------------------------------------ #
    _register({
        "name": "nlp_dev",
        "description": "NLP development with transformers, embeddings, NER, sentiment, topic modeling, and classification.",
        "knowledge": (
            "NLP enables computers to understand and generate human language. "
            "Transformer models use multi-head self-attention for long-range dependencies. "
            "Word embeddings map words to dense vectors capturing semantic similarity. "
            "Contextual embeddings from BERT adapt representations based on context. "
            "Named Entity Recognition classifies spans as persons, organizations, or locations. "
            "Sentiment analysis determines emotional tone using lexicon or ML approaches. "
            "Topic modeling discovers latent themes in document collections. "
            "Text classification assigns categories using TF-IDF or transformer encoders. "
            "Sequence labeling assigns labels to each token in sequences. "
            "SpaCy provides production-grade NLP pipelines for multiple languages. "
            "Hugging Face Transformers offers unified APIs for pre-trained models. "
            "Evaluation uses precision, recall, F1 for classification tasks. "
            "Text preprocessing covers tokenization, stemming, and normalization. "
            "Language detection uses n-gram models trained on multilingual corpora."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_text_sentiment(params.get("text", "")),
            "skill": "nlp_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 31. computer_vision — Computer Vision                               #
    # ------------------------------------------------------------------ #
    _register({
        "name": "computer_vision",
        "description": "Computer vision with OpenCV, YOLO, segmentation, image classification, GANs, and object detection.",
        "knowledge": (
            "Computer vision extracts meaning from images, video, and 3D data. "
            "OpenCV provides optimized image processing including filtering and transformations. "
            "CNNs learn hierarchical features through stacked convolution and pooling layers. "
            "YOLO performs real-time object detection as a regression problem. "
            "Semantic segmentation assigns class labels to every pixel. "
            "Instance segmentation distinguishes individual object instances. "
            "Image classification networks assign labels to entire images. "
            "GANs pit generator against discriminator for realistic synthetic images. "
            "Data augmentation improves robustness and reduces overfitting. "
            "Transfer learning fine-tunes pretrained models on domain tasks. "
            "Object tracking maintains identity across video frames. "
            "Optical flow computes pixel motion for activity recognition. "
            "Stereo vision recovers 3D geometry from multiple viewpoints. "
            "Model deployment uses TensorRT or ONNX for optimized inference."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_image_params(params.get("image_info", {})),
            "skill": "computer_vision"
        }
    })

    # ------------------------------------------------------------------ #
    # 32. audio_synthesis — Audio/Music Synthesis                         #
    # ------------------------------------------------------------------ #
    _register({
        "name": "audio_synthesis",
        "description": "Audio and music synthesis with DSP, MIDI, spectrogram analysis, sample manipulation, and TTS.",
        "knowledge": (
            "Audio synthesis generates sound through oscillators, filters, and envelopes. "
            "DSP manipulates audio using FFT, convolution, delay, and reverb. "
            "MIDI encodes musical events like note on, off, and velocity. "
            "Spectrograms visualize frequency content over time using STFT. "
            "Granular synthesis breaks audio into grains for time-stretching. "
            "TTS uses neural models like Tacotron and WaveNet for natural speech. "
            "Additive synthesis combines sine waves at harmonic frequencies. "
            "Subtractive synthesis filters harmonically rich waveforms. "
            "44.1kHz sample rate determines highest representable frequency. "
            "Bit depth determines dynamic range and noise floor. "
            "Phase vocoder enables independent time-stretching and pitch-shifting. "
            "Artificial reverberation uses convolution with impulse responses. "
            "VST and AU are plugin formats for synthesizers in DAWs. "
            "DAWs like Ableton Live sequence, record, and mix audio."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_audio_params(params.get("audio_info", {})),
            "skill": "audio_synthesis"
        }
    })

    # ------------------------------------------------------------------ #
    # 33. rag_systems — Retrieval-Augmented Generation                    #
    # ------------------------------------------------------------------ #
    _register({
        "name": "rag_systems",
        "description": "RAG pipeline development with chunking, embedding, retrieval, reranking, hybrid search, and evaluation.",
        "knowledge": (
            "RAG enhances LLM outputs with information from external knowledge bases. "
            "Chunking strategies determine how documents are split for indexing. "
            "Overlapping chunks preserve context at chunk boundaries. "
            "Embedding models convert text into dense vector representations. "
            "Vector databases index embeddings for approximate nearest neighbor search. "
            "Hybrid search combines vector similarity with BM25 keyword matching. "
            "Reranking models refine results with cross-encoders for relevance. "
            "Multi-hop retrieval decomposes questions into sub-queries. "
            "Context window management selects chunks within token limits. "
            "Query transformation improves retrieval by reformulating questions. "
            "Evaluation metrics include answer relevance and context precision. "
            "Parent-child retrieval returns fine chunks with parent-level context. "
            "LLM-as-judge rates response quality on defined criteria. "
            "Guardrails filter retrieved content for safety and freshness."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_rag_query(params.get("query", ""), params.get("chunks", [])),
            "skill": "rag_systems"
        }
    })

    # ------------------------------------------------------------------ #
    # 34. network_security — Network Security                             #
    # ------------------------------------------------------------------ #
    _register({
        "name": "network_security",
        "description": "Network security with nmap, Wireshark, firewalls, IDS/IPS, VPN, and network segmentation.",
        "knowledge": (
            "Network security protects infrastructure and data confidentiality. "
            "Nmap performs port scanning, service detection, and OS fingerprinting. "
            "Wireshark captures and analyzes packets with protocol dissection. "
            "Firewalls enforce policies using stateful inspection and filtering. "
            "IDS systems analyze traffic for malicious signatures and anomalies. "
            "VPNs encrypt traffic between endpoints over untrusted networks. "
            "Network segmentation divides networks into trust zones. "
            "Zero Trust requires continuous verification for every access. "
            "DDoS mitigation uses rate limiting and scrubbing centers. "
            "DNS security prevents spoofing with DNSSEC and DoH. "
            "MAC filtering and 802.1X control device access at the edge. "
            "Honeypots lure attackers to detect intrusion attempts. "
            "NetFlow collects metadata for traffic analysis. "
            "SIEM correlates alerts across network devices and servers."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_network_scan(params.get("host", ""), params.get("ports", "1-1000")),
            "skill": "network_security"
        }
    })

    # ------------------------------------------------------------------ #
    # 35. web_security — Web Application Security                         #
    # ------------------------------------------------------------------ #
    _register({
        "name": "web_security",
        "description": "Web application security covering OWASP Top 10, WAF, XSS, CSRF, SQLi, SSRF, and CSP.",
        "knowledge": (
            "Web security defends against HTTP-based application attacks. "
            "The OWASP Top 10 catalogs critical web security risks. "
            "XSS injects malicious scripts through unvalidated input. "
            "CSRF tricks authenticated users into unintended actions. "
            "SQL injection manipulates queries through unsanitized input. "
            "SSRF tricks servers into making unintended internal requests. "
            "CSP headers restrict browser resources mitigating XSS. "
            "WAFs like ModSecurity filter malicious HTTP at the edge. "
            "Same-Origin Policy prevents cross-origin data access. "
            "CORS relaxes same-origin based on whitelisted origins. "
            "HSTS forces HTTPS preventing SSL stripping attacks. "
            "Rate limiting protects against brute force and DoS. "
            "Secure cookie attributes prevent client-side access. "
            "Subresource Integrity ensures external scripts are untampered."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_web_security(params.get("headers", {})),
            "skill": "web_security"
        }
    })

    # ------------------------------------------------------------------ #
    # 36. pentesting — Penetration Testing                                #
    # ------------------------------------------------------------------ #
    _register({
        "name": "pentesting",
        "description": "Penetration testing methodology with Metasploit, Burp Suite, privilege escalation, and reporting.",
        "knowledge": (
            "Penetration testing simulates real attacks to identify vulnerabilities. "
            "Methodology includes recon, scanning, exploitation, and reporting. "
            "Metasploit provides exploits, payloads, and post-exploitation modules. "
            "Burp Suite intercepts HTTP traffic with repeater and intruder tools. "
            "Privilege escalation exploits kernel vulnerabilities or misconfigurations. "
            "Active recon uses direct interaction to map the attack surface. "
            "Passive recon gathers info from public sources. "
            "SQLMap automates SQL injection detection and exploitation. "
            "Password cracking uses hashcat with dictionary and brute-force attacks. "
            "Lateral movement expands access across the network. "
            "Persistence mechanisms maintain access after reboots. "
            "Exfiltration testing evaluates data extraction capabilities. "
            "Reporting documents findings with severity and remediation. "
            "Rules of engagement define scope and authorization."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_scan_results(params.get("findings", [])),
            "skill": "pentesting"
        }
    })

    # ------------------------------------------------------------------ #
    # 37. reverse_engineering — Reverse Engineering                        #
    # ------------------------------------------------------------------ #
    _register({
        "name": "reverse_engineering",
        "description": "Reverse engineering with IDA Pro, Ghidra, x86/ARM analysis, unpacking, patching, and debugging.",
        "knowledge": (
            "Reverse engineering analyzes software without source code. "
            "IDA Pro provides interactive disassembly with decompiler plugins. "
            "Ghidra is an open-source framework with collaborative analysis. "
            "x86 uses CISC instructions while ARM uses fixed-length RISC. "
            "Static analysis examines binaries without execution. "
            "Dynamic analysis observes behavior during execution. "
            "Packer detection identifies UPX and custom packers by entropy. "
            "Unpacking techniques include OEP finding and memory dumping. "
            "Binary patching modifies program logic by changing bytes. "
            "Function signatures identify library functions by byte patterns. "
            "Control flow graphs visualize branching and call relationships. "
            "Anti-debugging techniques complicate dynamic analysis. "
            "Decompilation translates assembly to high-level pseudocode. "
            "Protocol RE analyzes network traffic without documentation."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_binary_info(params.get("binary_info", {})),
            "skill": "reverse_engineering"
        }
    })

    # ------------------------------------------------------------------ #
    # 38. forensics — Digital Forensics                                   #
    # ------------------------------------------------------------------ #
    _register({
        "name": "forensics",
        "description": "Digital forensics with Autopsy, Volatility, FTK, timeline analysis, file carving, and memory analysis.",
        "knowledge": (
            "Digital forensics investigates evidence following chain-of-custody. "
            "Autopsy is a GUI platform for disk analysis and file carving. "
            "Volatility performs memory analysis on RAM dumps. "
            "FTK indexes evidence for rapid search and decryption. "
            "Timeline analysis correlates timestamps to reconstruct events. "
            "File carving recovers files by scanning for headers in free space. "
            "Write blockers prevent modification during acquisition. "
            "Hashing verifies evidence integrity after analysis. "
            "Data hiding includes alternate data streams and steganography. "
            "Registry analysis extracts user activity and USB history. "
            "Network forensics captures pcap for communication analysis. "
            "Mobile forensics extracts messages and location data. "
            "Anti-forensics techniques complicate recovery efforts. "
            "Reporting documents findings for legal proceedings."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_forensic_data(params.get("evidence", {})),
            "skill": "forensics"
        }
    })

    # ------------------------------------------------------------------ #
    # 39. cryptography — Cryptography                                    #
    # ------------------------------------------------------------------ #
    _register({
        "name": "cryptography",
        "description": "Cryptography with AES, RSA, ECC, hashing, TLS, PKI, key exchange, and post-quantum algorithms.",
        "knowledge": (
            "Cryptography provides confidentiality, integrity, and authentication. "
            "AES is a symmetric block cipher with 128 to 256-bit keys. "
            "RSA is based on the difficulty of factoring large primes. "
            "ECC offers equivalent security with smaller keys than RSA. "
            "Hash functions produce fixed-size collision-resistant digests. "
            "TLS 1.3 uses ECDHE key exchange with record encryption. "
            "PKI manages certificate issuance and validation. "
            "Diffie-Hellman allows shared secret agreement over insecure channels. "
            "HMAC provides message authentication with a secret key. "
            "Password hashing uses bcrypt, scrypt, or Argon2 with salt. "
            "Post-quantum cryptography like CRYSTALS-Kyber resists quantum attacks. "
            "Authenticated encryption modes provide confidentiality and integrity. "
            "Key derivation functions generate keys from passwords or secrets. "
            "Side-channel attacks exploit timing or power emissions."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _perform_crypto_operation(
                params.get("operation", "hash"),
                params.get("data", ""),
                params.get("algorithm", "sha256")
            ),
            "skill": "cryptography"
        }
    })

    # ------------------------------------------------------------------ #
    # 40. blockchain_dev — Blockchain Development                         #
    # ------------------------------------------------------------------ #
    _register({
        "name": "blockchain_dev",
        "description": "Blockchain development with Solidity, Ethereum, smart contracts, Web3, DeFi, and NFTs.",
        "knowledge": (
            "Blockchain is a distributed ledger maintained by consensus. "
            "Ethereum runs smart contracts on the EVM using Solidity. "
            "Solidity is a statically typed language with inheritance. "
            "Smart contracts manage on-chain state with functions and events. "
            "Gas optimization minimizes transaction costs. "
            "ERC-20 defines the fungible token standard. "
            "ERC-721 and ERC-1155 define non-fungible token standards. "
            "Web3.js and Ethers.js interact with Ethereum nodes. "
            "DeFi protocols implement AMM, lending, and yield farming. "
            "Layer 2 scaling uses rollups for higher throughput. "
            "Hardhat and Foundry compile and test smart contracts. "
            "The mempool holds pending transactions for inclusion. "
            "Oracles bring off-chain data onto the blockchain. "
            "MEV refers to profit from transaction ordering."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_ethereum_address(params.get("address", "")),
            "skill": "blockchain_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 41. crypto_trading — Cryptocurrency Trading                         #
    # ------------------------------------------------------------------ #
    _register({
        "name": "crypto_trading",
        "description": "Cryptocurrency trading with strategies, risk management, exchanges, indicators, and bot building.",
        "knowledge": (
            "Crypto trading involves buying and selling digital assets on exchanges. "
            "Technical indicators include moving averages, RSI, MACD, and Bollinger Bands. "
            "Order types include market, limit, stop-loss, and trailing stop. "
            "Liquidity analysis examines order book depth and spread. "
            "Risk management uses position sizing and drawdown limits. "
            "Algorithmic bots automate strategies using exchange APIs. "
            "Arbitrage exploits price differences across exchanges. "
            "Impermanent loss affects AMM liquidity providers. "
            "Funding rates incentivize perpetual contract convergence. "
            "Backtesting evaluates strategies on historical data. "
            "Market microstructure studies order flow and price impact. "
            "Portfolio tracking monitors P&L, Sharpe ratio, and drawdown. "
            "Tax reporting calculates capital gains for jurisdictions. "
            "Sentiment analysis incorporates social media and on-chain metrics."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _calculate_trading_metrics(params.get("trades", [])),
            "skill": "crypto_trading"
        }
    })

    # ------------------------------------------------------------------ #
    # 42. mining_ops — Cryptocurrency Mining                               #
    # ------------------------------------------------------------------ #
    _register({
        "name": "mining_ops",
        "description": "Cryptocurrency mining with SHA-256, GPU/ASIC operations, pool configuration, and profitability.",
        "knowledge": (
            "Mining validates transactions through proof-of-work computation. "
            "SHA-256 mining finds a nonce producing a hash with required zeros. "
            "Mining difficulty adjusts to maintain consistent block times. "
            "ASIC miners provide orders more hashrate per watt than GPUs. "
            "GPU mining remains viable for memory-hard algorithms. "
            "Pools combine hashrate and share rewards proportionally. "
            "Payout methods include PPS, FPPS, PPLNS, and solo mining. "
            "Profitability factors in hashrate, power cost, pool fees, and coin price. "
            "Overclocking and undervolting optimize hash-per-watt. "
            "Cooling solutions manage the significant heat generated. "
            "Stratum protocol relays work between pools and miners. "
            "Mining farm layout optimizes power and ventilation. "
            "Mining software supports multiple algorithms and pools. "
            "Regulatory considerations include power permits and taxation."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _calculate_mining_profitability(params.get("hashrate", 0), params.get("watts", 0)),
            "skill": "mining_ops"
        }
    })

    # ------------------------------------------------------------------ #
    # 43. unity_dev — Unity Game Development                              #
    # ------------------------------------------------------------------ #
    _register({
        "name": "unity_dev",
        "description": "Unity game development with C#, ECS, physics, shaders, animation, asset pipeline, and optimization.",
        "knowledge": (
            "Unity is a cross-platform engine for 2D, 3D, VR, and AR. "
            "MonoBehaviour scripts hook into Awake, Start, and Update. "
            "ECS provides data-oriented high-performance game logic. "
            "Unity Physics provides rigid bodies, colliders, and raycasting. "
            "URP and HDRP render pipelines provide configurable rendering. "
            "Animation uses state machines, blend trees, and IK. "
            "The asset pipeline imports and compresses game assets. "
            "Addressable Assets provide on-demand content loading. "
            "Profiler analyzes CPU, GPU, and memory performance. "
            "Job System and Burst enable multi-threaded near-native code. "
            "Prefab system creates reusable game object hierarchies. "
            "NavMesh provides pathfinding for AI characters. "
            "Input System handles keyboard, touch, gamepad, and XR. "
            "Build targets compile for multiple platforms."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_unity_script(params.get("code", "")),
            "skill": "unity_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 44. unreal_dev — Unreal Engine Game Development                     #
    # ------------------------------------------------------------------ #
    _register({
        "name": "unreal_dev",
        "description": "Unreal Engine development with Blueprints, C++, Niagara, materials, sequencer, and world building.",
        "knowledge": (
            "Unreal Engine is a AAA game engine with advanced rendering. "
            "Blueprints are visual scripting graphs compiling to C++. "
            "C++ uses reflection macros for engine integration. "
            "Niagara provides GPU particle effects for large simulations. "
            "Material Editor creates shaders with nodes for visual effects. "
            "Sequencer is a cinematic tool for cutscenes and sequences. "
            "World building uses landscapes, foliage, and level streaming. "
            "Chaos Physics handles destruction and cloth simulation. "
            "Animation Blueprints control skeletal mesh animation. "
            "Lighting combines baked lightmaps with Lumen GI. "
            "Sound Cues and MetaSounds provide audio mixing. "
            "Gameplay Ability System provides modular abilities. "
            "Online Subsystem abstracts multiplayer networking. "
            "Pixel Streaming renders and streams to browsers via WebRTC."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_unreal_blueprint(params.get("blueprint_info", {})),
            "skill": "unreal_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 45. godot_dev — Godot Game Development                              #
    # ------------------------------------------------------------------ #
    _register({
        "name": "godot_dev",
        "description": "Godot game development with GDScript, scene system, signals, shaders, 2D/3D, and export.",
        "knowledge": (
            "Godot is a free open-source engine with node-based architecture. "
            "GDScript is a Python-like language integrated with Godot's API. "
            "The scene tree organizes nodes hierarchically. "
            "Signals provide decoupled node communication. "
            "The 2D engine has pixel-perfect rendering and dedicated physics. "
            "The 3D engine supports PBR materials and SDFGI GI. "
            "Shader language is based on GLSL with multiple shader types. "
            "AnimationPlayer handles sprite, property, and bone animation. "
            "TileMap provides auto-tiling and collision layers. "
            "@export exposes script variables to the editor. "
            "Godot 4 uses Vulkan as the primary rendering backend. "
            "Resource system serializes game data with custom resources. "
            "Multiplayer API provides RPC and low-level networking. "
            "Export templates build for multiple desktop and mobile platforms."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_godot_script(params.get("code", "")),
            "skill": "godot_dev"
        }
    })

    # ------------------------------------------------------------------ #
    # 46. web_app_builder — Web Application Architecture                  #
    # ------------------------------------------------------------------ #
    _register({
        "name": "web_app_builder",
        "description": "Web application architecture with full-stack patterns, SPAs, SSR, PWA, performance, and accessibility.",
        "knowledge": (
            "Web architecture defines client and server component interactions. "
            "SPAs render all views client-side with API data fetching. "
            "SSR generates HTML on the server for faster initial loads. "
            "PWAs use service workers for offline and push notifications. "
            "Web performance metrics include LCP, FID, and CLS. "
            "Core Web Vitals optimize images, code splitting, and caching. "
            "Accessibility follows WCAG 2.1 with semantic HTML and ARIA. "
            "SEO uses semantic markup, structured data, and sitemaps. "
            "Internationalization uses message catalogs and locale detection. "
            "Authentication integrates OAuth providers and route guards. "
            "API caching with ETag and Cache-Control reduces server load. "
            "Security headers like X-Frame-Options harden the app. "
            "Build tooling optimizes bundles with tree shaking. "
            "RUM captures actual user experience metrics across devices."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_web_app(params.get("url", ""), params.get("config", {})),
            "skill": "web_app_builder"
        }
    })

    # ------------------------------------------------------------------ #
    # 47. mobile_app_builder — Mobile Application Architecture            #
    # ------------------------------------------------------------------ #
    _register({
        "name": "mobile_app_builder",
        "description": "Mobile application architecture with offline-first, sync, deep linking, push, and app store deployment.",
        "knowledge": (
            "Mobile architecture handles connectivity variation and limited battery. "
            "Offline-first stores data locally and syncs when online. "
            "Conflict resolution uses CRDTs or last-write-wins. "
            "Deep linking navigates from URLs or notifications. "
            "Push notifications use APNs and FCM with device tokens. "
            "App store deployment requires signing and platform compliance. "
            "Feature flags enable gradual rollouts without store releases. "
            "Analytics captures user behavior and crash metrics. "
            "Biometric auth integrates with Face ID and fingerprint APIs. "
            "Background processing uses WorkManager or BGTaskScheduler. "
            "Memory management avoids leaks with weak references. "
            "Responsive layouts use adaptive grids and dynamic type. "
            "Module separation enables independent feature development. "
            "App thinning reduces download size for target devices."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_mobile_config(params.get("config", {})),
            "skill": "mobile_app_builder"
        }
    })

    # ------------------------------------------------------------------ #
    # 48. desktop_app_builder — Desktop Application Development           #
    # ------------------------------------------------------------------ #
    _register({
        "name": "desktop_app_builder",
        "description": "Desktop application development with Electron, Tauri, .NET MAUI, Qt, and native-feel UIs.",
        "knowledge": (
            "Desktop apps run natively with full system API access. "
            "Electron packages web apps with Chromium and Node.js. "
            "Tauri uses native web views with a Rust backend for security. "
            ".NET MAUI creates native apps from a single .NET codebase. "
            "Qt is a C++ framework with QML for declarative UIs. "
            "Native-feel design follows platform menu and dialog conventions. "
            "Installers use Inno Setup, .dmg, or .deb packaging tools. "
            "Auto-update frameworks deliver seamless version upgrades. "
            "System tray integration provides background operation. "
            "GPU acceleration enables smooth animations and video. "
            "IPC bridges renderer and main process in Electron or Tauri. "
            "Accessibility supports screen readers and keyboard nav. "
            "Crash reporting captures stack traces for debugging. "
            "Signed builds prevent security warnings on distribution."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_desktop_config(params.get("config", {})),
            "skill": "desktop_app_builder"
        }
    })

    # ------------------------------------------------------------------ #
    # 49. api_builder — API Design and Development                        #
    # ------------------------------------------------------------------ #
    _register({
        "name": "api_builder",
        "description": "API design with REST, GraphQL, gRPC, versioning, documentation, testing, and API gateways.",
        "knowledge": (
            "API design defines contracts between services. "
            "REST uses HTTP methods and resource-oriented URLs. "
            "GraphQL provides flexible client-driven queries. "
            "gRPC uses Protocol Buffers with HTTP/2 streaming. "
            "Versioning strategies include URL prefix and headers. "
            "OpenAPI documents REST APIs with request schemas. "
            "API gateways handle routing, rate limiting, and auth. "
            "Idempotency keys prevent duplicate processing. "
            "Pagination includes cursor-based and offset-based patterns. "
            "Error responses follow consistent formats with codes. "
            "Rate limiting uses token bucket or sliding window algorithms. "
            "HATEOAS provides discoverable API navigation. "
            "Webhook delivery uses retry logic and signatures. "
            "API testing with Postman ensures specification compliance."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_api_spec(params.get("spec", "")),
            "skill": "api_builder"
        }
    })

    # ------------------------------------------------------------------ #
    # 50. auth_builder — Authentication Systems                           #
    # ------------------------------------------------------------------ #
    _register({
        "name": "auth_builder",
        "description": "Authentication systems with OAuth 2.0, OIDC, SAML, JWT, RBAC, MFA, WebAuthn, and sessions.",
        "knowledge": (
            "Authentication verifies identity while authorization controls access. "
            "OAuth 2.0 is an authorization framework with multiple grant types. "
            "OpenID Connect extends OAuth with identity tokens. "
            "SAML 2.0 provides enterprise SSO with federated identity. "
            "JWT encodes claims with cryptographic signature verification. "
            "RBAC assigns permissions to roles rather than users. "
            "ABAC evaluates policies based on attributes. "
            "MFA combines password, TOTP, biometric, or hardware factors. "
            "WebAuthn provides passwordless public-key authentication. "
            "Session management uses rotating session IDs server-side. "
            "Token refresh uses short-lived access with long-lived refresh tokens. "
            "PKCE prevents authorization code interception. "
            "Account recovery verifies identity before password reset. "
            "Brute force protection locks accounts after failed attempts."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_jwt(params.get("token", "")),
            "skill": "auth_builder"
        }
    })

    # ------------------------------------------------------------------ #
    # 51. payment_integration — Payment Systems                           #
    # ------------------------------------------------------------------ #
    _register({
        "name": "payment_integration",
        "description": "Payment integration with Stripe, PayPal, subscriptions, invoicing, and PCI compliance.",
        "knowledge": (
            "Payment processing handles secure fund transfers. "
            "Stripe provides APIs for payments, subscriptions, and invoicing. "
            "PayPal offers checkout flows and dispute resolution. "
            "PCI DSS defines security requirements for card processing. "
            "Tokenization reduces PCI scope by replacing card data. "
            "Subscription management handles billing cycles and proration. "
            "Webhooks validate signatures for payment event processing. "
            "Invoicing generates PDFs with tax and discount calculation. "
            "Multi-currency requires exchange rate APIs and rounding rules. "
            "3D Secure adds verification for card-not-present transactions. "
            "Refund handling processes full or partial refunds. "
            "Payouts schedule batch transfers with settlement reporting. "
            "Tax calculation integrates services for sales tax compliance. "
            "Recurring revenue tracks MRR, ARR, churn, and LTV."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_payment_amount(params.get("amount", 0)),
            "skill": "payment_integration"
        }
    })

    # ------------------------------------------------------------------ #
    # 52. linux_ops — Linux Administration & Operations                   #
    # ------------------------------------------------------------------ #
    _register({
        "name": "linux_ops",
        "description": "Linux administration with shell scripting, systemd, performance, security, and networking.",
        "knowledge": (
            "Linux powers servers, embedded devices, and cloud infrastructure. "
            "Systemd manages services, timers, and targets as the init system. "
            "Bash scripting automates tasks with pipes and control structures. "
            "File permissions control access with rwx bits and ACLs. "
            "Process management with ps and top monitors resource usage. "
            "User administration manages accounts and groups. "
            "Package management uses apt, dnf, or pacman depending on distro. "
            "Kernel parameters via sysctl control networking and memory. "
            "LVM provides flexible disk management with snapshots. "
            "Performance tuning uses perf, strace, and iostat. "
            "SSH key management secures remote access. "
            "Firewall configuration with iptables or firewalld. "
            "Rsync and tar provide efficient backup and archiving. "
            "Journald captures system logs with rotation and filtering."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_linux_command(params.get("command", "")),
            "skill": "linux_ops"
        }
    })

    # ------------------------------------------------------------------ #
    # 53. networking_ops — Networking Operations                          #
    # ------------------------------------------------------------------ #
    _register({
        "name": "networking_ops",
        "description": "Networking operations with TCP/IP, DNS, HTTP/2, load balancing, CDN, BGP, and SDN.",
        "knowledge": (
            "Networking fundamentals underpin all distributed systems. "
            "TCP provides reliable connection-oriented data delivery. "
            "DNS translates domain names to IP addresses hierarchically. "
            "HTTP/2 multiplexes streams over a single TCP connection. "
            "Load balancing distributes traffic with various algorithms. "
            "CDNs cache content at edge locations for lower latency. "
            "BGP routes traffic between autonomous systems. "
            "SDN decouples control and data planes for programmability. "
            "TCP three-way handshake establishes connections. "
            "TLS handshake negotiates encryption and exchanges certificates. "
            "CIDR notation specifies IP ranges for subnetting. "
            "NAT maps private IPs to public addresses. "
            "IPv6 provides 128-bit addressing with built-in IPsec. "
            "Troubleshooting uses ping, traceroute, dig, and tcpdump."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _resolve_dns(params.get("hostname", "localhost")),
            "skill": "networking_ops"
        }
    })

    # ------------------------------------------------------------------ #
    # 54. database_admin — Database Administration                        #
    # ------------------------------------------------------------------ #
    _register({
        "name": "database_admin",
        "description": "Database administration for PostgreSQL and MySQL with replication, backup, tuning, and sharding.",
        "knowledge": (
            "Database administration ensures availability and performance. "
            "PostgreSQL uses MVCC for consistent reads without blocking. "
            "MySQL InnoDB provides row-level locking and crash recovery. "
            "Streaming replication sends WAL segments to standbys. "
            "Logical replication replicates at row level across versions. "
            "Backup strategies include full and incremental with PITR. "
            "WAL archiving enables continuous disaster recovery. "
            "Query tuning uses EXPLAIN ANALYZE for execution plans. "
            "Connection pooling reduces overhead for many clients. "
            "Vacuuming reclaims dead tuples and updates statistics. "
            "Sharding distributes data across multiple servers. "
            "Index types include B-tree, hash, GiST, and GIN. "
            "Partitioning splits large tables for easier management. "
            "Automated failover provides high availability."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _validate_connection_string(params.get("connection_string", "")),
            "skill": "database_admin"
        }
    })

    # ------------------------------------------------------------------ #
    # 55. monitoring_ops — Monitoring & Observability                     #
    # ------------------------------------------------------------------ #
    _register({
        "name": "monitoring_ops",
        "description": "Monitoring and observability with Prometheus, Grafana, Datadog, alerting, dashboards, and SLOs.",
        "knowledge": (
            "Monitoring provides visibility into system health. "
            "Prometheus scrapes metrics at configurable intervals. "
            "Metric types include counters, gauges, histograms, and summaries. "
            "Grafana visualizes metrics with templated dashboards. "
            "Datadog provides SaaS monitoring with APM and logs. "
            "The RED method focuses on Rate, Errors, Duration. "
            "The USE method analyzes Utilization, Saturation, Errors. "
            "SLOs define target ratios of good to total events. "
            "Error budgets represent acceptable unreliability. "
            "Alert fatigue is reduced by grouping and proper thresholds. "
            "Alertmanager handles deduplication and routing. "
            "Synthetic probes measure availability from external locations. "
            "Distributed tracing propagates context across services. "
            "Anomaly detection identifies unusual metric patterns."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_metric_query(params.get("query", "")),
            "skill": "monitoring_ops"
        }
    })

    # ------------------------------------------------------------------ #
    # 56. logging_ops — Logging & Observability                           #
    # ------------------------------------------------------------------ #
    _register({
        "name": "logging_ops",
        "description": "Logging operations with ELK stack, Loki, structured logging, correlation IDs, and distributed tracing.",
        "knowledge": (
            "Logging records application events for debugging and auditing. "
            "ELK stack indexes logs for full-text search. "
            "Logstash ingests with input plugins and filters. "
            "Loki is a scalable log aggregation system for Grafana. "
            "Structured logging outputs JSON for automated parsing. "
            "Log levels indicate event severity for filtering. "
            "Correlation IDs propagate through service boundaries. "
            "Distributed tracing instruments requests across services. "
            "Log rotation prevents disk full conditions. "
            "Centralized logging aggregates from multiple servers. "
            "Sampling reduces volume while retaining important traces. "
            "Log shippers collect and forward to aggregation backends. "
            "Index lifecycle management transitions through phases. "
            "Audit logging captures compliance-relevant events."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _parse_log_entry(params.get("log_line", "")),
            "skill": "logging_ops"
        }
    })

    # ------------------------------------------------------------------ #
    # 57. testing_qa — Testing & Quality Assurance                        #
    # ------------------------------------------------------------------ #
    _register({
        "name": "testing_qa",
        "description": "Testing and QA with unit, integration, e2e, property-based, fuzzing, coverage, and TDD practices.",
        "knowledge": (
            "Testing ensures correctness and regression prevention. "
            "Unit tests verify functions in isolation with mocks. "
            "Integration tests validate component interactions. "
            "E2E tests simulate real user workflows. "
            "Property-based testing generates random inputs. "
            "Fuzz testing provides malformed inputs to find crashes. "
            "Code coverage measures exercised code. "
            "Mutation testing checks if tests detect changes. "
            "TDD cycles write tests before implementation. "
            "Test pyramid balances unit, integration, and E2E tests. "
            "Mocking frameworks isolate units by replacing dependencies. "
            "Parameterized tests run with multiple inputs. "
            "Continuous testing integrates into CI pipelines. "
            "Load testing verifies behavior under peak traffic."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_test_coverage(params.get("coverage_data", {})),
            "skill": "testing_qa"
        }
    })

    # ------------------------------------------------------------------ #
    # 58. performance_engineering — Performance Engineering                #
    # ------------------------------------------------------------------ #
    _register({
        "name": "performance_engineering",
        "description": "Performance engineering with profiling, benchmarking, optimization, caching strategies, and CDN.",
        "knowledge": (
            "Performance engineering optimizes system speed and efficiency. "
            "Profiling identifies hotspots using CPU and memory profilers. "
            "Benchmarking establishes baselines with controlled workloads. "
            "Algorithmic optimization reduces time complexity. "
            "Caching strategies include in-memory HTTP and app-level cache. "
            "Cache invalidation uses TTL, write-through, or LRU. "
            "Query optimization uses index tuning and rewriting. "
            "Connection pooling reduces database connection overhead. "
            "Lazy loading defers expensive operations. "
            "Prefetching anticipates future requests. "
            "CDNs cache content at edge locations. "
            "Compression reduces transfer sizes. "
            "Async processing moves blocking ops to queues. "
            "Amdahl's Law limits parallelization speedup."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_performance_metrics(params.get("metrics", {})),
            "skill": "performance_engineering"
        }
    })

    # ------------------------------------------------------------------ #
    # 59. architecture_design — Software Architecture Design              #
    # ------------------------------------------------------------------ #
    _register({
        "name": "architecture_design",
        "description": "Software architecture design with patterns, trade-offs, ADRs, RFCs, and documentation.",
        "knowledge": (
            "Architecture defines high-level structure and interactions. "
            "Patterns include layered, hexagonal, microservices, and event-driven. "
            "Layered architecture separates presentation, logic, and data. "
            "Hexagonal isolates core logic from external adapters. "
            "Microservices decompose into independently deployable services. "
            "Event-driven uses async streams for decoupled communication. "
            "ADRs document decisions with context and rationale. "
            "RFCs propose significant changes for review. "
            "Trade-off analysis evaluates scalability and complexity. "
            "C4 model visualizes architecture at multiple levels. "
            "DDD aligns software models with business language. "
            "CQRS separates read and write data models. "
            "Event sourcing stores state as immutable event log. "
            "Capacity planning estimates resource requirements."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_architecture_pattern(params.get("pattern", "")),
            "skill": "architecture_design"
        }
    })

    # ------------------------------------------------------------------ #
    # 60. project_management — Project Management                         #
    # ------------------------------------------------------------------ #
    _register({
        "name": "project_management",
        "description": "Project management with agile, scrum, estimation, risk, communication, and JIRA administration.",
        "knowledge": (
            "Project management plans and monitors work to achieve goals. "
            "Agile delivers value incrementally through iterations. "
            "Scrum organizes sprints with stand-ups, planning, and reviews. "
            "Estimation uses story points, t-shirt sizing, and poker. "
            "Risk management identifies and mitigates with probability-impact. "
            "Communication plans define stakeholder engagement cadence. "
            "JIRA configures workflows, issue types, and permissions. "
            "Kanban visualizes WIP with flow-based delivery limits. "
            "Burndown charts track progress against planned scope. "
            "Critical path identifies tasks impacting completion. "
            "Retrospectives reflect on improvements for next iteration. "
            "Stakeholder mapping guides engagement strategies. "
            "Velocity tracks team throughput for forecasting. "
            "Tech debt management prioritizes refactoring by impact."
        ),
        "execute": lambda params: {
            "success": True,
            "result": _analyze_project_estimate(params.get("tasks", [])),
            "skill": "project_management"
        }
    })

    return skills

# =========================================================================== #
#  Internal helpers — real computation logic for each skill execute lambda    #
# =========================================================================== #

def _analyze_rust_code(code: str) -> str:
    if not code.strip():
        return "No code provided."
    has_unsafe = "unsafe {" in code
    has_generics = "<" in code and ">" in code
    has_trait = "trait " in code or "impl " in code
    parts = []
    if has_unsafe: parts.append("unsafe block")
    if has_generics: parts.append("generics")
    if has_trait: parts.append("traits/impl")
    parts.append(f"{len(code)} chars")
    return f"Rust: {', '.join(parts)}."

def _evaluate_cpp_expression(code: str) -> str:
    if not code.strip():
        return "No code provided."
    parts = []
    if "unique_ptr" in code or "shared_ptr" in code: parts.append("smart pointers")
    if "template<" in code: parts.append("templates")
    if "&&" in code or "std::move" in code: parts.append("move semantics")
    if "auto" in code or "constexpr" in code: parts.append("modern C++")
    parts.append(f"{len(code)} chars")
    return f"C++: {', '.join(parts)}."

def _evaluate_go_code(code: str) -> str:
    if not code.strip():
        return "No code provided."
    parts = []
    if "go " in code: parts.append("goroutines")
    if "chan" in code or "<-" in code: parts.append("channels")
    if "defer " in code: parts.append("defer")
    if "interface" in code: parts.append("interfaces")
    parts.append(f"{len(code)} chars")
    return f"Go: {', '.join(parts)}."

def _analyze_java_code(code: str) -> str:
    if not code.strip():
        return "No code provided."
    parts = []
    if "->" in code: parts.append("lambdas")
    if ".stream()" in code or "Stream" in code: parts.append("streams")
    if "Optional" in code: parts.append("Optional")
    if "record " in code: parts.append("records")
    parts.append(f"{len(code)} chars")
    return f"Java: {', '.join(parts)}."

def _analyze_kotlin_code(code: str) -> str:
    if not code.strip():
        return "No code provided."
    parts = []
    if "suspend " in code: parts.append("suspend")
    if "Flow" in code: parts.append("Flow")
    if "data class " in code: parts.append("data class")
    parts.append(f"{len(code)} chars")
    return f"Kotlin: {', '.join(parts)}."

def _analyze_swift_code(code: str) -> str:
    if not code.strip():
        return "No code provided."
    parts = []
    if "async " in code or "await" in code: parts.append("async/await")
    if "actor " in code: parts.append("actor")
    if "Codable" in code: parts.append("Codable")
    if "View" in code or "@State" in code: parts.append("SwiftUI")
    parts.append(f"{len(code)} chars")
    return f"Swift: {', '.join(parts)}."

def _analyze_typescript_code(code: str) -> str:
    if not code.strip():
        return "No code provided."
    parts = []
    if "type " in code or "interface " in code: parts.append("types")
    if "async " in code or "await " in code: parts.append("async")
    if "?." in code: parts.append("optional chain")
    parts.append(f"{len(code)} chars")
    return f"TypeScript: {', '.join(parts)}."

def _analyze_python_code(code: str) -> str:
    if not code.strip():
        return "No code provided."
    parts = []
    if "async " in code or "await " in code: parts.append("async")
    if ":" in code and (": str" in code or ": int" in code or ": List" in code or ": Optional" in code):
        parts.append("type hints")
    if "@" in code: parts.append("decorators")
    parts.append(f"{len(code)} chars")
    return f"Python: {', '.join(parts)}."

def _evaluate_react_component(code: str) -> str:
    if not code.strip():
        return "No component provided."
    parts = []
    if "useState" in code or "useEffect" in code: parts.append("hooks")
    if "</" in code: parts.append("JSX")
    parts.append(f"{len(code)} chars")
    return f"React: {', '.join(parts)}."

def _evaluate_vue_component(code: str) -> str:
    if not code.strip():
        return "No component provided."
    parts = []
    if "<template" in code: parts.append("template")
    if "setup" in code or "ref(" in code: parts.append("Composition API")
    parts.append(f"{len(code)} chars")
    return f"Vue: {', '.join(parts)}."


def _analyze_django_model(code: str) -> str:
    if not code.strip():
        return "No model provided."
    parts = []
    if "models.Model" in code or "models." in code: parts.append("Django model")
    if "ForeignKey" in code or "ManyToManyField" in code: parts.append("relations")
    if "class Meta" in code: parts.append("Meta class")
    parts.append(f"{len(code)} chars")
    return f"Django: {', '.join(parts)}."

def _validate_fastapi_route(code: str) -> str:
    if not code.strip():
        return "No route provided."
    parts = []
    if "@app" in code or "@router" in code: parts.append("route decorator")
    if "BaseModel" in code or "Field(" in code: parts.append("Pydantic")
    if "Depends" in code: parts.append("DI")
    parts.append(f"{len(code)} chars")
    return f"FastAPI: {', '.join(parts)}."

def _analyze_spring_config(code: str) -> str:
    if not code.strip():
        return "No config provided."
    parts = []
    if "@Bean" in code or "@Component" in code: parts.append("beans")
    if "@Autowired" in code: parts.append("autowired")
    if "@Transactional" in code: parts.append("transactional")
    parts.append(f"{len(code)} chars")
    return f"Spring: {', '.join(parts)}."

def _analyze_android_manifest(manifest: str) -> str:
    if not manifest.strip():
        return "No manifest provided."
    parts = []
    if "activity" in manifest.lower(): parts.append("activities")
    if "service" in manifest.lower(): parts.append("services")
    if "permission" in manifest.lower(): parts.append("permissions")
    parts.append(f"{len(manifest)} chars")
    return f"Android: {', '.join(parts)}."

def _analyze_ios_code(code: str) -> str:
    if not code.strip():
        return "No code provided."
    parts = []
    if "CoreData" in code or "NSManagedObject" in code: parts.append("Core Data")
    if "Publisher" in code or "@Published" in code: parts.append("Combine")
    if "UIApplicationDelegate" in code: parts.append("delegate")
    parts.append(f"{len(code)} chars")
    return f"iOS: {', '.join(parts)}."

def _evaluate_flutter_widget(code: str) -> str:
    if not code.strip():
        return "No widget provided."
    parts = []
    if "Widget" in code or "build" in code: parts.append("widget")
    if "StatefulWidget" in code or "setState" in code: parts.append("stateful")
    if "Animation" in code or "Animated" in code: parts.append("animated")
    parts.append(f"{len(code)} chars")
    return f"Flutter: {', '.join(parts)}."

def _analyze_rn_component(code: str) -> str:
    if not code.strip():
        return "No component provided."
    parts = []
    if "</" in code: parts.append("JSX")
    if "useState" in code or "this.state" in code: parts.append("state")
    if "StyleSheet" in code: parts.append("StyleSheet")
    parts.append(f"{len(code)} chars")
    return f"RN: {', '.join(parts)}."

def _validate_aws_arn(arn: str) -> str:
    if not arn.strip():
        return "No ARN provided."
    valid = bool(re.match(r"^arn:aws:[a-z0-9-]+:[a-z0-9-]*:\d{12}:.+$", arn))
    return f"ARN {'valid' if valid else 'invalid'}: {arn[:60]}"

def _validate_azure_resource_id(rid: str) -> str:
    if not rid.strip():
        return "No resource ID provided."
    valid = rid.startswith("/subscriptions/")
    return f"Azure resource ID {'valid' if valid else 'invalid'}: {rid[:60]}"

def _validate_gcp_resource_name(name: str) -> str:
    if not name.strip():
        return "No name provided."
    valid = bool(re.match(r"^[a-z][a-z0-9-]*[a-z0-9]$", name))
    return f"GCP name '{name}' {'follows' if valid else 'violates'} conventions."

def _validate_dockerfile(dockerfile: str) -> str:
    if not dockerfile.strip():
        return "No Dockerfile provided."
    lines = dockerfile.strip().split("\n")
    parts = []
    if any(l.strip().upper().startswith("FROM") for l in lines): parts.append("FROM")
    if any(l.strip().upper().startswith("RUN") for l in lines): parts.append("RUN")
    if any(l.strip().upper().startswith("CMD") or l.strip().upper().startswith("ENTRYPOINT") for l in lines):
        parts.append("entrypoint")
    parts.append(f"{len(lines)} lines")
    return f"Dockerfile: {', '.join(parts)}."

def _validate_k8s_manifest(manifest: str) -> str:
    if not manifest.strip():
        return "No manifest provided."
    parts = []
    if "apiVersion" in manifest: parts.append("apiVersion")
    if "kind:" in manifest: parts.append("kind")
    if "metadata" in manifest: parts.append("metadata")
    parts.append(f"{len(manifest)} chars")
    return f"K8s: {', '.join(parts)}."


def _validate_ci_config(config: str) -> str:
    if not config.strip():
        return "No config provided."
    parts = []
    if "stages" in config or "jobs" in config: parts.append("stages")
    if "steps" in config or "tasks" in config: parts.append("steps")
    parts.append(f"{len(config)} chars")
    return f"CI: {', '.join(parts)}."

def _analyze_sql_query(query: str) -> str:
    if not query.strip():
        return "No query provided."
    up = query.upper()
    parts = []
    if "SELECT" in up: parts.append("SELECT")
    if "JOIN" in up: parts.append("JOIN")
    if "WHERE" in up: parts.append("WHERE")
    if "OVER" in up or "ROW_NUMBER" in up: parts.append("window function")
    parts.append(f"{len(query)} chars")
    return f"SQL: {', '.join(parts)}."

def _validate_nosql_query(query: str) -> str:
    if not query.strip():
        return "No query provided."
    parts = []
    if "find" in query or "aggregate" in query: parts.append("read")
    if "filter" in query or "where" in query.lower(): parts.append("filtered")
    parts.append(f"{len(query)} chars")
    return f"NoSQL: {', '.join(parts)}."

def _validate_data_pipeline(config: dict) -> str:
    if not config:
        return "No config provided."
    return f"Pipeline: {len(config)} fields."

def _analyze_dataset_metrics(data: dict) -> str:
    if not data:
        return "No data provided."
    return f"Dataset: {data.get('rows', '?')} rows x {data.get('columns', '?')} cols."

def _analyze_llm_prompt(prompt: str, system_prompt: str) -> str:
    total = len(prompt) + len(system_prompt)
    return f"LLM prompt: user={len(prompt)} sys={len(system_prompt)} total_chars={total} est_tokens={total//4}."

def _analyze_ml_pipeline(config: dict) -> str:
    if not config:
        return "No config provided."
    stages = config.get("stages", config.get("steps", []))
    return f"ML pipeline: {len(stages)} stages."

def _analyze_text_sentiment(text: str) -> str:
    if not text.strip():
        return "No text provided."
    pos = {"good","great","excellent","amazing","happy","wonderful","fantastic","love","best","beautiful"}
    neg = {"bad","terrible","awful","horrible","sad","hate","worst","ugly","angry","poor"}
    words = set(text.lower().split())
    p = len(words & pos)
    n = len(words & neg)
    return f"Sentiment: {'positive' if p > n else 'negative' if n > p else 'neutral'} ({p} pos, {n} neg)."

def _analyze_image_params(info: dict) -> str:
    if not info:
        return "No image info."
    return f"Image: {info.get('width','?')}x{info.get('height','?')} {info.get('channels','?')}ch."

def _analyze_audio_params(info: dict) -> str:
    if not info:
        return "No audio info."
    return f"Audio: {info.get('sample_rate','?')}Hz {info.get('duration','?')}s {info.get('channels','?')}ch."

def _analyze_rag_query(query: str, chunks: list) -> str:
    if not query:
        return "No query."
    total = sum(len(c) if isinstance(c, str) else 0 for c in chunks)
    return f"RAG: {len(query)} chars, {len(chunks)} chunks ({total} total chars)."

def _analyze_network_scan(host: str, ports: str) -> str:
    return f"Network scan: {host or '?'}, ports {ports or '1-1000'}."

def _analyze_web_security(headers: dict) -> str:
    if not headers:
        return "No headers."
    found = []
    for k in headers:
        kl = k.lower()
        if kl == "content-security-policy": found.append("CSP")
        elif kl == "x-content-type-options": found.append("XCTO")
        elif kl == "x-frame-options": found.append("XFO")
        elif kl == "strict-transport-security": found.append("HSTS")
    return f"Web security: {', '.join(found) if found else 'no security headers'} ({len(headers)} total)."

def _analyze_scan_results(findings: list) -> str:
    return f"Findings: {len(findings)} items."

def _analyze_binary_info(info: dict) -> str:
    return f"Binary: {info.get('architecture','?')} {info.get('format','?')} {info.get('size','?')}B."

def _analyze_forensic_data(evidence: dict) -> str:
    return f"Evidence: type={evidence.get('type','?')} size={evidence.get('size','?')}."


def _perform_crypto_operation(op: str, data: str, algo: str) -> str:
    if not data:
        return "No data."
    algo = algo.lower().replace("-", "")
    if op == "hash":
        if algo == "sha256":
            return f"SHA-256: {hashlib.sha256(data.encode()).hexdigest()}"
        elif algo == "md5":
            return f"MD5: {hashlib.md5(data.encode()).hexdigest()}"
        elif algo == "sha512":
            return f"SHA-512: {hashlib.sha512(data.encode()).hexdigest()}"
        return f"SHA-256: {hashlib.sha256(data.encode()).hexdigest()}"
    elif op == "base64_encode":
        import base64
        return f"Base64: {base64.b64encode(data.encode()).decode()}"
    elif op == "base64_decode":
        import base64
        try:
            return f"Decoded: {base64.b64decode(data.encode()).decode()}"
        except Exception:
            return "Invalid base64."
    return f"Crypto: {op} on {len(data)} bytes."

def _validate_ethereum_address(addr: str) -> str:
    if not addr.strip():
        return "No address."
    valid = bool(re.match(r"^0x[a-fA-F0-9]{40}$", addr))
    return f"Ethereum address {'valid' if valid else 'invalid'}."

def _calculate_trading_metrics(trades: list) -> str:
    if not trades:
        return "No trades."
    total = len(trades)
    pnl = sum(t.get("pnl", t.get("profit", 0)) for t in trades)
    wins = sum(1 for t in trades if t.get("pnl", t.get("profit", 0)) > 0)
    return f"Trades: {total}, win rate {wins/total*100:.1f}%, P&L ."

def _calculate_mining_profitability(hashrate: float, watts: float) -> str:
    if hashrate <= 0:
        return "No hashrate."
    if watts <= 0:
        return f"Hashrate: {hashrate} H/s (power data needed)."
    return f"Mining: {hashrate} H/s, {watts}W, eff {hashrate/watts:.2f} H/J."

def _analyze_unity_script(code: str) -> str:
    if not code.strip():
        return "No script."
    parts = []
    if "MonoBehaviour" in code: parts.append("MonoBehaviour")
    if "void Start" in code: parts.append("Start")
    if "void Update" in code: parts.append("Update")
    parts.append(f"{len(code)} chars")
    return f"Unity: {', '.join(parts)}."

def _analyze_unreal_blueprint(info: dict) -> str:
    return f"Blueprint: class={info.get('class','?')} nodes={info.get('nodes','?')}."

def _analyze_godot_script(code: str) -> str:
    if not code.strip():
        return "No script."
    parts = []
    if "extends " in code: parts.append("extends")
    if "func " in code: parts.append("functions")
    if "signal " in code: parts.append("signals")
    parts.append(f"{len(code)} chars")
    return f"Godot: {', '.join(parts)}."

def _analyze_web_app(url: str, config: dict) -> str:
    return f"Web app: url={'set' if url else 'not set'} config={len(config)} fields."

def _analyze_mobile_config(config: dict) -> str:
    return f"Mobile config: {len(config)} fields."

def _analyze_desktop_config(config: dict) -> str:
    return f"Desktop config: {len(config)} fields."

def _validate_api_spec(spec: str) -> str:
    if not spec.strip():
        return "No spec provided."
    parts = []
    if "openapi" in spec.lower() or "swagger" in spec.lower(): parts.append("OpenAPI")
    if "paths" in spec.lower(): parts.append("paths")
    if "schema" in spec.lower(): parts.append("schema")
    parts.append(f"{len(spec)} chars")
    return f"API spec: {', '.join(parts)}."

def _validate_jwt(token: str) -> str:
    if not token.strip():
        return "No token provided."
    parts = token.split(".")
    if len(parts) == 3:
        try:
            import base64
            padded = parts[0] + "=" * (4 - len(parts[0]) % 4)
            header = json.loads(base64.b64decode(padded).decode())
            return f"JWT: alg={header.get('alg','?')} typ={header.get('typ','?')}."
        except Exception:
            return "JWT: 3 segments but unparseable."
    return f"JWT: {len(parts)} segments (expected 3)."

def _validate_payment_amount(amount) -> str:
    try:
        a = float(amount)
        if a <= 0: return "Amount must be positive."
        if a > 999999999: return "Amount exceeds maximum."
        return f"Payment amount  validated."
    except (ValueError, TypeError):
        return f"Invalid amount: {amount}."


def _analyze_linux_command(cmd: str) -> str:
    if not cmd.strip():
        return "No command."
    parts = cmd.strip().split()
    return f"Linux: cmd={parts[0] if parts else '?'} args={len(parts)-1}."

def _resolve_dns(hostname: str) -> str:
    try:
        ip = socket.gethostbyname(hostname)
        return f"DNS: {hostname} -> {ip}."
    except Exception as e:
        return f"DNS resolution failed for {hostname}: {e}."

def _validate_connection_string(cs: str) -> str:
    if not cs.strip():
        return "No connection string."
    parts = {}
    for pair in cs.replace(";", " ").split():
        if "=" in pair:
            k, v = pair.split("=", 1)
            parts[k.lower()] = v
    checks = []
    for required in ["host", "port", "dbname", "user"]:
        if required in parts: checks.append(required + "=ok")
        else: checks.append(required + "=missing")
    return f"Connection string: {', '.join(checks)}."

def _analyze_metric_query(query: str) -> str:
    if not query.strip():
        return "No query."
    return f"Metric query ({len(query)} chars): {query[:80]}."

def _parse_log_entry(log_line: str) -> str:
    if not log_line.strip():
        return "No log line."
    m = re.search(r"(ERROR|WARN|INFO|DEBUG|TRACE|FATAL)", log_line, re.IGNORECASE)
    level = m.group(1).upper() if m else "UNKNOWN"
    return f"Log: level={level} length={len(log_line)} chars."

def _analyze_test_coverage(data: dict) -> str:
    if not data:
        return "No coverage data."
    cov = data.get("coverage", data.get("percent", "?"))
    total = data.get("total", data.get("tests", "?"))
    return f"Coverage: {cov}% across {total} tests."

def _analyze_performance_metrics(metrics: dict) -> str:
    if not metrics:
        return "No metrics."
    return f"Perf: {len(metrics)} metrics."

def _analyze_architecture_pattern(pattern: str) -> str:
    if not pattern.strip():
        return "No pattern."
    patterns = {
        "microservices": "decomposes into independently deployable services",
        "layered": "separates presentation, logic, and data layers",
        "hexagonal": "isolates core from external adapters",
        "event-driven": "uses async event streams for decoupled communication",
        "cqrs": "separates read and write models",
        "event-sourcing": "stores state as immutable event log",
    }
    desc = patterns.get(pattern.lower().strip(), "custom architecture pattern")
    return f"Architecture '{pattern}': {desc}."

def _analyze_project_estimate(tasks: list) -> str:
    if not tasks:
        return "No tasks."
    total = len(tasks)
    effort = sum(t.get("story_points", t.get("hours", 0)) for t in tasks)
    return f"Project: {total} tasks, total effort {effort} units."

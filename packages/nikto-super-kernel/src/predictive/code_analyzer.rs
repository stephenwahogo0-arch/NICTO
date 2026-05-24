use std::fs;
use std::path::Path;
use std::time::Instant;
use walkdir::WalkDir;
use syn::{ItemFn, File as SynFile};

use crate::predictive::types::*;

pub struct CodeAnalyzer {
    error_dictionary: Vec<(Vec<&'static str>, &'static str)>,
}

impl CodeAnalyzer {
    pub fn new() -> Self {
        Self {
            error_dictionary: vec![
                (vec!["SEGFAULT", "SIGSEGV", "segmentation fault"], "Null pointer dereference or buffer overflow"),
                (vec!["OOM", "out of memory", "Cannot allocate memory"], "Memory leak or unbounded allocation"),
                (vec!["deadlock", "DEADLOCK"], "Lock ordering violation — possible circular wait"),
                (vec!["stack overflow", "stackoverflow"], "Unbounded recursion — missing base case or depth limit"),
                (vec!["index out of bounds", "IndexOutOfRange"], "Array access without bounds check"),
                (vec!["panic", "PANIC"], "Unhandled panic — missing error propagation"),
                (vec!["unwrap", "expect"], "Unsafe unwrap/expect in non-test code — potential panic"),
                (vec!["data race", "DataRace", "TSAN"], "Concurrent unsynchronized memory access"),
            ],
        }
    }

    pub fn analyze_project(&self, project_path: &str, error_log: Option<&str>) -> DiagnosticReport {
        let start = Instant::now();
        let project = Path::new(project_path);
        let project_name = project.file_name().and_then(|s| s.to_str()).unwrap_or("unknown").to_string();

        let mut vulnerabilities = Vec::new();
        let mut files_scanned = 0u32;

        if project.exists() && project.is_dir() {
            for entry in WalkDir::new(project).into_iter().filter_map(|e| e.ok()) {
                if !entry.file_type().is_file() { continue; }
                let path = entry.path();
                let ext = path.extension().and_then(|s| s.to_str()).unwrap_or("");
                match ext {
                    "rs" | "py" | "cpp" | "c" | "h" | "hpp" | "go" | "js" | "ts" | "zig" | "mojo" => {
                        if let Ok(content) = fs::read_to_string(path) {
                            files_scanned += 1;
                            if ext == "rs" {
                                vulnerabilities.extend(self.analyze_rust_file(path, &content));
                            } else {
                                vulnerabilities.extend(self.analyze_generic_file(path, &content));
                            }
                        }
                    }
                    _ => {}
                }
            }
        }

        let root_cause = error_log.and_then(|log| self.match_error(log));
        let optimization_hints = self.generate_hints(&vulnerabilities);

        DiagnosticReport {
            project: project_name,
            files_scanned,
            vulnerabilities,
            root_cause,
            optimization_hints,
            scan_duration_ms: start.elapsed().as_secs_f64() * 1000.0,
        }
    }

    fn analyze_rust_file(&self, path: &Path, content: &str) -> Vec<Vulnerability> {
        let mut vulns = Vec::new();
        let file_stem = path.to_string_lossy().to_string();

        // Parse AST with syn
        if let Ok(syn_file) = syn::parse_file(content) {
            for item in &syn_file.items {
                if let syn::Item::Fn(func) = item {
                    self.check_function_for_vulns(&file_stem, func, content, &mut vulns);
                }
                if let syn::Item::Verbatim(_) = item {
                    vulns.push(Vulnerability {
                        kind: "UnsafeUsage".into(),
                        location: CodeLocation { file: file_stem.clone(), line: 0, column: 0 },
                        severity: "High".into(),
                        description: "Unsafe code pattern detected — verify memory safety".into(),
                        suggestion: "Wrap unsafe blocks in safe abstractions with documented invariants".into(),
                    });
                }
            }
        }

        // Line-by-line pattern scan (complements AST)
        for (line_num, line) in content.lines().enumerate() {
            let line_num = (line_num + 1) as u32;
            let trimmed = line.trim();

            if trimmed.contains("unwrap()") && !trimmed.starts_with("//") && !trimmed.starts_with("#[") {
                vulns.push(Vulnerability {
                    kind: "PanicRisk".into(),
                    location: CodeLocation { file: file_stem.clone(), line: line_num, column: 0 },
                    severity: "Medium".into(),
                    description: "unwrap() in production code may cause panic".into(),
                    suggestion: "Use pattern matching or ? operator instead of unwrap()".into(),
                });
            }

            if trimmed.contains("std::mem::forget") && !trimmed.starts_with("//") {
                vulns.push(Vulnerability {
                    kind: "MemoryLeak".into(),
                    location: CodeLocation { file: file_stem.clone(), line: line_num, column: 0 },
                    severity: "High".into(),
                    description: "std::mem::forget intentionally leaks memory".into(),
                    suggestion: "Ensure forget is intentional and document why the memory must not be dropped".into(),
                });
            }

            if trimmed.contains("thread::spawn") && !trimmed.starts_with("//") {
                if !content.contains("Arc<") {
                    vulns.push(Vulnerability {
                        kind: "DataRace".into(),
                        location: CodeLocation { file: file_stem.clone(), line: line_num, column: 0 },
                        severity: "High".into(),
                        description: "thread::spawn without Arc wrapping — potential data race".into(),
                        suggestion: "Wrap shared state in Arc<Mutex<T>> or Arc<RwLock<T>>".into(),
                    });
                }
            }
        }

        vulns
    }

    fn check_function_for_vulns(&self, file: &str, func: &ItemFn, _content: &str, vulns: &mut Vec<Vulnerability>) {
        let func_name = func.sig.ident.to_string();
        let start_line = 0u32;

        // Check for recursive functions without obvious base case
        let body_str = format!("{:?}", func.block);
        if body_str.contains(&func_name) && !body_str.contains("if") && !body_str.contains("match") {
            vulns.push(Vulnerability {
                kind: "StackOverflow".into(),
                location: CodeLocation { file: file.into(), line: start_line, column: 0 },
                severity: "High".into(),
                description: format!("Recursive function '{}' lacks visible base case — stack overflow risk", func_name),
                suggestion: "Add a base case condition (if/guard) before the recursive call".into(),
            });
        }
    }

    fn analyze_generic_file(&self, path: &Path, content: &str) -> Vec<Vulnerability> {
        let mut vulns = Vec::new();
        let file_stem = path.to_string_lossy().to_string();

        for (line_num, line) in content.lines().enumerate() {
            let line_num = (line_num + 1) as u32;
            let trimmed = line.trim();
            if trimmed.starts_with("//") || trimmed.starts_with("#") { continue; }

            // Python-specific
            if trimmed.contains("except:") && !trimmed.contains("Exception") {
                vulns.push(Vulnerability {
                    kind: "UnhandledException".into(),
                    location: CodeLocation { file: file_stem.clone(), line: line_num, column: 0 },
                    severity: "Medium".into(),
                    description: "Bare except: catches all exceptions including SystemExit/KeyboardInterrupt".into(),
                    suggestion: "Use 'except Exception:' to avoid catching system-exit signals".into(),
                });
            }

            // C/C++ specific
            if trimmed.contains("malloc(") || trimmed.contains("new " ) {
                if !content.contains("free(") && !content.contains("delete") {
                    vulns.push(Vulnerability {
                        kind: "MemoryLeak".into(),
                        location: CodeLocation { file: file_stem.clone(), line: line_num, column: 0 },
                        severity: "High".into(),
                        description: "Allocation without matching deallocation — potential leak".into(),
                        suggestion: "Ensure every malloc/new has a corresponding free/delete".into(),
                    });
                }
            }

            // Go-specific
            if trimmed.contains("go func(") && !trimmed.contains("sync.WaitGroup") && !trimmed.contains("sync.Mutex") {
                vulns.push(Vulnerability {
                    kind: "DataRace".into(),
                    location: CodeLocation { file: file_stem.clone(), line: line_num, column: 0 },
                    severity: "Medium".into(),
                    description: "Goroutine without synchronization primitive".into(),
                    suggestion: "Use WaitGroup, Mutex, or channels to synchronize goroutine access".into(),
                });
            }
        }

        vulns
    }

    fn match_error(&self, log: &str) -> Option<String> {
        let log_upper = log.to_uppercase();
        for (patterns, cause) in &self.error_dictionary {
            for pattern in patterns {
                if log_upper.contains(&pattern.to_uppercase()) {
                    return Some(cause.to_string());
                }
            }
        }
        None
    }

    pub fn vulnerability_count(&self) -> usize {
        self.error_dictionary.len()
    }

    fn generate_hints(&self, vulns: &[Vulnerability]) -> Vec<String> {
        let mut hints = Vec::new();

        let panic_count = vulns.iter().filter(|v| v.kind == "PanicRisk").count();
        if panic_count > 5 {
            hints.push(format!("Replace {} unwrap() calls with pattern matching or ? operator", panic_count));
        }

        let unsafe_count = vulns.iter().filter(|v| v.kind == "UnsafeCode").count();
        if unsafe_count > 0 {
            hints.push(format!("Document safety invariants for {} unsafe blocks", unsafe_count));
        }

        let race_count = vulns.iter().filter(|v| v.kind == "DataRace").count();
        if race_count > 0 {
            hints.push(format!("Add synchronization (Arc, Mutex, RwLock, channels) to {} detected race conditions", race_count));
        }

        let leak_count = vulns.iter().filter(|v| v.kind == "MemoryLeak").count();
        if leak_count > 0 {
            hints.push(format!("Plug {} memory leaks with proper deallocation or RAII wrappers", leak_count));
        }

        hints
    }
}

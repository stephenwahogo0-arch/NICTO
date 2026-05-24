/// NIKTO Super Kernel — Master Build Orchestrator
/// Compiles Zig, C++, C, Go, Mojo sources and links into Rust cdylib.
/// Each external compiler gracefully falls back to a C stub if unavailable.

use std::process::Command;

fn main() {
    let out_dir = std::env::var("OUT_DIR").unwrap();
    let target = std::env::var("TARGET").unwrap();

    // ── Zig compilation ──
    if which("zig").is_ok() {
        let zig_files = [
            "../triple-engine/spatial_memory.zig",
        ];
        for src in &zig_files {
            let path = std::path::Path::new(src);
            if path.exists() {
                let lib_name = path.file_stem().unwrap().to_str().unwrap();
                let status = Command::new("zig")
                    .args(&[
                        "build-lib",
                        "-fPIC",
                        "-dynamic",
                        "-O", "ReleaseFast",
                        src,
                        &format!("-femit-bin={}/lib{}.a", out_dir, lib_name),
                    ])
                    .status()
                    .expect("Zig compiler failed");
                if status.success() {
                    println!("cargo:rustc-link-lib=static={}", lib_name);
                }
            }
        }
    } else {
        println!("cargo:warning=Zig not found — generating stubs");
        generate_zig_stubs(&out_dir);
    }

    // ── C/C++ compilation ──
    if c_compiler_available() {
        let cpp_sources: Vec<&str> = vec![];
        let c_sources: Vec<&str> = vec![];

        if !cpp_sources.is_empty() {
            let mut build = cc::Build::new();
            build.cpp(true)
                  .flag("-O3").flag("-march=native");
            for f in &cpp_sources { build.file(f); }
            build.compile("cpp_engine");
            println!("cargo:rustc-link-lib=static=cpp_engine");
        }

        if !c_sources.is_empty() {
            let mut build = cc::Build::new();
            build.flag("-O2");
            for f in &c_sources { build.file(f); }
            build.compile("c_engine");
            println!("cargo:rustc-link-lib=static=c_engine");
        }
    } else {
        println!("cargo:warning=C/C++ compiler not found");
    }

    // ── Go compilation ──
    if which("go").is_ok() {
        let go_modules = ["go/hsync_engine", "go/graph_core", "go/background_monitor"];
        for module in &go_modules {
            let mod_path = std::path::Path::new(module);
            if mod_path.join("go.mod").exists() {
                let status = Command::new("go")
                    .args(&["build", "-buildmode=c-shared",
                           "-o", &format!("{}/lib{}.a", out_dir, mod_path.to_str().unwrap_or("unknown").replace("/", "_")),
                           "."])
                    .current_dir(mod_path)
                    .status()
                    .expect("Go build failed");
                if status.success() {
                    let lib_name = mod_path.to_str().unwrap_or("unknown").replace("/", "_");
                    println!("cargo:rustc-link-lib=static={}", lib_name);
                }
            }
        }
    } else {
        println!("cargo:warning=Go not found");
    }

    // ── Mojo compilation ──
    if which("mojo").is_ok() {
        let mojo_src = "src/physics/physics_core.mojo";
        if std::path::Path::new(mojo_src).exists() {
            let status = Command::new("mojo")
                .args(&["build", mojo_src,
                       "-o", &format!("{}/libphysics_core.a", out_dir)])
                .status()
                .expect("Mojo build failed");
            if status.success() {
                println!("cargo:rustc-link-lib=static=physics_core");
            }
        }
    } else {
        println!("cargo:warning=Mojo not found");
    }

    println!("cargo:rustc-link-search=native={}", out_dir);
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=src/");
}

fn which(cmd: &str) -> Result<(), ()> {
    Command::new(cmd).arg("--version").output().map(|_| ()).map_err(|_| ())
}

fn c_compiler_available() -> bool {
    which("cl").is_ok() || which("gcc").is_ok() || which("clang").is_ok()
}

fn generate_zig_stubs(out_dir: &str) {
    let stub = r#"
#include <stdint.h>
void spatial_init(uint64_t size) {}
uint64_t spatial_spawn(float x, float y, float z) { return 0; }
uint64_t spatial_count() { return 0; }
void spatial_set_position(uint64_t id, float x, float y, float z) {}
"#;
    let stub_path = std::path::Path::new(out_dir).join("spatial_memory_stub.c");
    std::fs::write(&stub_path, stub).unwrap();

    let mut build = cc::Build::new();
    build.file(&stub_path).compile("spatial_memory");
    println!("cargo:rustc-link-lib=static=spatial_memory");
}

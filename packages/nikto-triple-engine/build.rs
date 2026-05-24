/// NIKTO Triple-Engine Build Script
///
/// Orchestrates compilation of the Zig memory layer and Mojo physics core
/// into static archives, then links them into the Rust cdylib so that
/// the final .pyd / .so contains all three languages in one binary.
///
/// Required toolchain:
///   - Zig 0.13+  (https:/ziglang.org/download)
///   - Mojo 24.6+ (https:/docs.modular.com/mojo)
///   - Rust 1.78+ (https:/rustup.rs)
///
/// Build:
///   cargo build --release
///
/// The output `target/release/nikto_triple_engine.pyd` (or .so) is the
/// final native module importable from Python.

use std::path::PathBuf;
use std::process::Command;

/// Root directory of the triple-engine package (where Cargo.toml lives).
fn project_root() -> PathBuf {
    PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap())
}

/// Target directory for intermediate build artifacts.
fn out_dir() -> PathBuf {
    PathBuf::from(std::env::var("OUT_DIR").unwrap())
}

/// Compile Zig source into a static library (.a / .lib).
fn compile_zig() {
    let src = project_root().join("spatial_memory.zig");
    let out = out_dir();

    println!("cargo:rerun-if-changed={}", src.display());
    println!("cargo:info=Compiling Zig → spatial_memory.lib");

    // Determine target triple from Rust's TARGET environment variable.
    let rust_target = std::env::var("TARGET").unwrap_or_else(|_| "x86_64-pc-windows-msvc".into());
    let target_flag = format!("-target={}", rust_target);

    let status = Command::new("zig")
        .args(&[
            "build-lib",
            "-fPIC",              // Position-independent code
            "-dynamic",           // Dynamic library suitable for cdylib linking
            "-O", "ReleaseFast",  // Maximum optimization
            &target_flag,
            "--name", "spatial_memory",
            "--cache-dir", out.join("zig-cache").to_str().unwrap(),
            "--output-dir", out.to_str().unwrap(),
            src.to_str().unwrap(),
        ])
        .status()
        .expect("Failed to execute Zig compiler. Is Zig installed? (https://ziglang.org/download)");

    if !status.success() {
        panic!("Zig compilation failed");
    }

    // Tell Rust where to find the static library
    println!("cargo:rustc-link-search=native={}", out.display());

    // The library name produced by `zig build-lib --name spatial_memory`
    // is `libspatial_memory.a` (Linux/macOS) or `spatial_memory.lib` (Windows).
    // Rust's native lib lookup handles both.
    println!("cargo:rustc-link-lib=static=spatial_memory");

    // On Windows, Zig may produce .lib; on other platforms, .a
    // We need the C runtime linked as well.
    if cfg!(target_os = "windows") {
        println!("cargo:rustc-link-lib=dylib=ucrt");  // Universal CRT
    }
}

/// Compile Mojo source into a static library (.a / .lib).
fn compile_mojo() {
    let src = project_root().join("physics_core.mojo");
    let out = out_dir();

    println!("cargo:rerun-if-changed={}", src.display());
    println!("cargo:info=Compiling Mojo → physics_core.lib");

    // Try `mojo build` first (produces executable), then try alternate flags.
    // Mojo compilation to static library is evolving — we attempt known flags.
    let mojo_cmds = [
        // Preferred: build as static library (Mojo 24.6+)
        (vec!["build", &src.to_str().unwrap(), "-o", out.join("physics_core.a").to_str().unwrap()], &out),
        // Fallback: compile with shared-lib output
        (vec!["build", &src.to_str().unwrap(), "--output-type", "shared-lib", "-o", out.join("physics_core.a").to_str().unwrap()], &out),
    ];

    let mut compiled = false;
    for (args, _) in &mojo_cmds {
        let result = Command::new("mojo")
            .args(args)
            .status();

        match result {
            Ok(status) if status.success() => {
                compiled = true;
                break;
            }
            Ok(_) => continue,   // try next command variant
            Err(_) => continue,  // mojo not found or other error
        }
    }

    if !compiled {
        // If Mojo is not installed, print a warning but don't fail the build.
        // The Rust-only parts still compile; physics will be unavailable.
        println!("cargo:warning=Mojo compiler not found or compilation failed.");
        println!("cargo:warning=Skipping Mojo physics core. Install Mojo: https://docs.modular.com/mojo");
        println!("cargo:warning=The engine will work without Mojo, but physics acceleration will be disabled.");
        // Generate an empty stub library so linking doesn't fail
        generate_stub_lib(&out.join("physics_core"));
        return;
    }

    println!("cargo:rustc-link-search=native={}", out.display());
    println!("cargo:rustc-link-lib=static=physics_core");

    // Mojo depends on the C++ runtime and Python runtime
    if cfg!(target_os = "linux") {
        println!("cargo:rustc-link-lib=dylib=stdc++");
        println!("cargo:rustc-link-lib=dylib=python3.12");
    } else if cfg!(target_os = "macos") {
        println!("cargo:rustc-link-lib=dylib=c++");
    } else if cfg!(target_os = "windows") {
        println!("cargo:rustc-link-lib=dylib=python312");
    }
}

/// Generate an empty stub library for Mojo when the real one is unavailable.
/// This prevents linker errors — the Mojo extern "C" calls in Rust will
/// resolve to these empty functions at link time (and crash at runtime
/// if actually called, which is acceptable for a graceful-degradation path).
fn generate_stub_lib(stub_path: &std::path::Path) {
    // Write a small C file with stub implementations
    let c_src = format!(
        r#"
        #include <stddef.h>
        void physics_init() {{}}
        size_t physics_update(void* ptr, size_t count, float dt, float gravity, float time) {{ return count; }}
        void physics_center_of_mass(void* ptr, size_t count, float* out) {{ out[0]=0; out[1]=0; out[2]=0; }}
        size_t physics_detect_collisions(void* ptr, size_t count, float radius) {{ return 0; }}
        "#
    );

    let c_path = stub_path.with_extension("c");
    std::fs::write(&c_path, c_src.trim()).expect("Failed to write Mojo stub C file");

    let obj_path = stub_path.with_extension("o");
    let lib_path = format!("{}{}",
        stub_path.to_str().unwrap(),
        if cfg!(target_os = "windows") { ".lib" } else { ".a" }
    );

    // Compile the stub with the system C compiler
    let cc = if cfg!(target_os = "windows") { "cl.exe" } else { "cc" };
    let status = Command::new(cc)
        .args(&[
            "-c", c_path.to_str().unwrap(),
            "-o", obj_path.to_str().unwrap(),
        ])
        .status()
        .expect("Failed to compile Mojo stub");
    if !status.success() {
        panic!("Failed to compile Mojo stub C file");
    }

    // Create static library
    let ar = if cfg!(target_os = "windows") { "lib.exe" } else { "ar" };
    let ar_args: &[&str] = if cfg!(target_os = "windows") {
        &["/OUT:", &lib_path, obj_path.to_str().unwrap()]
    } else {
        &["rcs", &lib_path, obj_path.to_str().unwrap()]
    };
    let status = Command::new(ar)
        .args(ar_args)
        .status()
        .expect("Failed to create Mojo stub archive");
    if !status.success() {
        panic!("Failed to create Mojo stub archive");
    }

    let out = out_dir();
    println!("cargo:rustc-link-search=native={}", out.display());
    println!("cargo:rustc-link-lib=static=physics_core");
}

fn main() {
    compile_zig();
    compile_mojo();

    // Ensure re-build when these change
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=Cargo.toml");
    println!("cargo:rerun-if-changed=src/lib.rs");
    println!("cargo:rerun-if-changed=spatial_memory.zig");
    println!("cargo:rerun-if-changed=physics_core.mojo");

    // Print build info for diagnostics
    println!("cargo:info=NIKTO Triple-Engine build complete");
    println!("cargo:info=Output: nikto_triple_engine.pyd / .so");
}

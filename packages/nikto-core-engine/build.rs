/// NIKTO Core Engine build script.
///
/// PyO3's `maturin` or `setuptools-rust` normally handles the build,
/// but this file ensures the correct Rust flags are set when compiling
/// via `cargo build --release` directly.
///
/// Output: `target/release/nikto_core_engine.pyd` (Windows)
///         `target/release/libnikto_core_engine.so` (Linux/macOS)
///
/// The compiled binary must be copied (or symlinked) into the Python
/// package so it can be imported:
///   cp target/release/nikto_core_engine.pyd packages/nikto-core-engine/
///
/// Then in Python:
///   >>> import nikto_core_engine
///   >>> engine = nikto_core_engine.NiktoEngine()

fn main() {
    // PyO3 bridge requires Python to be linkable at build time
    println!("cargo:rustc-link-arg-bin=nikto_core_engine");

    // Re-run if the Python interpreter changes
    println!("cargo:rerun-if-changed=build.rs");
    println!("cargo:rerun-if-changed=Cargo.toml");

    // Instruct maturin / setuptools-rust that we target Python 3.11+
    #[cfg(feature = "abi3-py311")]
    println!("cargo:rustc-cfg=Py_3_11");
}

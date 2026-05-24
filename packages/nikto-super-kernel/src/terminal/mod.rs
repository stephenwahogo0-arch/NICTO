// Sector 4: Terminal & Storage — FFI stubs into C++ kernel_terminal + Zig block_fs.
// Real implementation requires ConPTY (Windows) / PTY (Linux) + O_DIRECT NVMe.
pub mod ffi;

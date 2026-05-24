use std::ffi::CString;
use std::os::raw::c_char;

extern "C" {
    fn kterm_spawn(cmd: *const c_char, rows: i32, cols: i32) -> i32;
    fn kterm_write(fd: i32, data: *const u8, len: i32) -> i32;
    fn kterm_read(fd: i32, buf: *mut u8, max_len: i32) -> i32;
    fn kterm_close(fd: i32) -> i32;
    fn block_fs_open(path: *const c_char) -> i32;
    fn block_fs_read(fd: i32, offset: i64, buf: *mut u8, len: i64) -> i64;
    fn block_fs_write(fd: i32, offset: i64, buf: *const u8, len: i64) -> i64;
    fn block_fs_close(fd: i32) -> i32;
}

pub struct KernelTerminal;

impl KernelTerminal {
    pub fn spawn(cmd: &str, rows: i32, cols: i32) -> Result<i32, String> {
        let c = CString::new(cmd).map_err(|e| format!("CString: {}", e))?;
        let fd = unsafe { kterm_spawn(c.as_ptr(), rows, cols) };
        if fd >= 0 { Ok(fd) } else { Err(format!("kterm_spawn: {}", fd)) }
    }

    pub fn write(fd: i32, data: &[u8]) -> Result<i32, String> {
        let n = unsafe { kterm_write(fd, data.as_ptr(), data.len() as i32) };
        if n >= 0 { Ok(n) } else { Err(format!("kterm_write: {}", n)) }
    }

    pub fn read(fd: i32, max_len: i32) -> Result<Vec<u8>, String> {
        let mut buf = vec![0u8; max_len as usize];
        let n = unsafe { kterm_read(fd, buf.as_mut_ptr(), max_len) };
        if n >= 0 {
            buf.truncate(n as usize);
            Ok(buf)
        } else {
            Err(format!("kterm_read: {}", n))
        }
    }

    pub fn close(fd: i32) -> Result<(), String> {
        let r = unsafe { kterm_close(fd) };
        if r == 0 { Ok(()) } else { Err(format!("kterm_close: {}", r)) }
    }
}

pub struct BlockFileSystem;

impl BlockFileSystem {
    pub fn open(path: &str) -> Result<i32, String> {
        let c = CString::new(path).map_err(|e| format!("CString: {}", e))?;
        let fd = unsafe { block_fs_open(c.as_ptr()) };
        if fd >= 0 { Ok(fd) } else { Err(format!("block_fs_open: {}", fd)) }
    }

    pub fn read(fd: i32, offset: i64, len: i64) -> Result<Vec<u8>, String> {
        let mut buf = vec![0u8; len as usize];
        let n = unsafe { block_fs_read(fd, offset, buf.as_mut_ptr(), len) };
        if n >= 0 { Ok(buf) } else { Err(format!("block_fs_read: {}", n)) }
    }

    pub fn write(fd: i32, offset: i64, data: &[u8]) -> Result<i64, String> {
        let n = unsafe { block_fs_write(fd, offset, data.as_ptr(), data.len() as i64) };
        if n >= 0 { Ok(n) } else { Err(format!("block_fs_write: {}", n)) }
    }

    pub fn close(fd: i32) -> Result<(), String> {
        let r = unsafe { block_fs_close(fd) };
        if r == 0 { Ok(()) } else { Err(format!("block_fs_close: {}", r)) }
    }
}

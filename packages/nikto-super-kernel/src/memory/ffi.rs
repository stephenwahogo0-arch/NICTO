use std::ffi::CString;
use std::os::raw::c_char;

extern "C" {
    fn mem_arena_create(name: *const c_char, size: u64) -> i32;
    fn mem_arena_alloc(arena: i32, size: u64) -> u64;
    fn mem_arena_free(arena: i32, ptr: u64);
    fn mem_arena_write(arena: i32, ptr: u64, src: *const u8, len: u64) -> i32;
    fn mem_arena_read(arena: i32, ptr: u64, dst: *mut u8, len: u64) -> i32;
    fn mem_arena_destroy(arena: i32) -> i32;
}

pub struct SharedMemoryArena;

impl SharedMemoryArena {
    pub fn create(name: &str, size: u64) -> Result<i32, String> {
        let c = CString::new(name).map_err(|e| format!("CString: {}", e))?;
        let id = unsafe { mem_arena_create(c.as_ptr(), size) };
        if id >= 0 { Ok(id) } else { Err(format!("arena_create: {}", id)) }
    }

    pub fn alloc(arena: i32, size: u64) -> Result<u64, String> {
        let ptr = unsafe { mem_arena_alloc(arena, size) };
        if ptr != 0 { Ok(ptr) } else { Err("arena_alloc returned null".into()) }
    }

    pub fn free(arena: i32, ptr: u64) { unsafe { mem_arena_free(arena, ptr); } }

    pub fn write(arena: i32, ptr: u64, data: &[u8]) -> Result<(), String> {
        let r = unsafe { mem_arena_write(arena, ptr, data.as_ptr(), data.len() as u64) };
        if r == 0 { Ok(()) } else { Err(format!("arena_write: {}", r)) }
    }

    pub fn read(arena: i32, ptr: u64, len: u64) -> Result<Vec<u8>, String> {
        let mut buf = vec![0u8; len as usize];
        let r = unsafe { mem_arena_read(arena, ptr, buf.as_mut_ptr(), len) };
        if r == 0 { Ok(buf) } else { Err(format!("arena_read: {}", r)) }
    }

    pub fn destroy(arena: i32) -> Result<(), String> {
        let r = unsafe { mem_arena_destroy(arena) };
        if r == 0 { Ok(()) } else { Err(format!("arena_destroy: {}", r)) }
    }
}

use std::ffi::CString;
use std::os::raw::c_char;

extern "C" {
    fn hsync_connect(endpoint: *const c_char) -> i32;
    fn hsync_publish(topic: *const c_char, data: *const u8, len: i32) -> i32;
    fn hsync_subscribe(topic: *const c_char, cb: extern "C" fn(*const u8, i32)) -> i32;
    fn hsync_disconnect();
}

pub struct HSyncClient;

impl HSyncClient {
    pub fn connect(endpoint: &str) -> Result<(), String> {
        let c = CString::new(endpoint).map_err(|e| format!("CString: {}", e))?;
        let r = unsafe { hsync_connect(c.as_ptr()) };
        if r == 0 { Ok(()) } else { Err(format!("hsync_connect: {}", r)) }
    }

    pub fn publish(topic: &str, data: &[u8]) -> Result<(), String> {
        let t = CString::new(topic).map_err(|e| format!("CString: {}", e))?;
        let r = unsafe { hsync_publish(t.as_ptr(), data.as_ptr(), data.len() as i32) };
        if r == 0 { Ok(()) } else { Err(format!("hsync_publish: {}", r)) }
    }

    pub fn subscribe(topic: &str, cb: extern "C" fn(*const u8, i32)) -> Result<i32, String> {
        let t = CString::new(topic).map_err(|e| format!("CString: {}", e))?;
        let id = unsafe { hsync_subscribe(t.as_ptr(), cb) };
        if id >= 0 { Ok(id) } else { Err(format!("hsync_subscribe: {}", id)) }
    }

    pub fn disconnect() { unsafe { hsync_disconnect(); } }
}

use std::ffi::{CStr, CString};
use std::os::raw::c_char;

extern "C" {
    fn desktop_streamer_start(display: *const c_char) -> i32;
    fn desktop_streamer_capture(dst: *mut u8, width: i32, height: i32) -> i32;
    fn desktop_streamer_stop();
    fn frame_packer_pack(rgb: *const u8, width: i32, height: i32,
                         quality: i32, out: *mut u8, out_len: *mut i32) -> i32;
}

#[derive(Debug)]
pub struct CapturedFrame {
    pub data: Vec<u8>,
    pub width: u32,
    pub height: u32,
}

pub struct DesktopStreamer;

impl DesktopStreamer {
    pub fn start(display: &str) -> Result<(), String> {
        let c_str = CString::new(display).map_err(|e| format!("CString: {}", e))?;
        let ret = unsafe { desktop_streamer_start(c_str.as_ptr()) };
        if ret == 0 { Ok(()) } else { Err(format!("desktop_streamer_start returned {}", ret)) }
    }

    pub fn capture(width: u32, height: u32) -> Result<CapturedFrame, String> {
        let mut buf = vec![0u8; (width * height * 4) as usize];
        let ret = unsafe { desktop_streamer_capture(buf.as_mut_ptr(), width as i32, height as i32) };
        if ret >= 0 {
            Ok(CapturedFrame { data: buf, width, height })
        } else {
            Err(format!("capture failed: {}", ret))
        }
    }

    pub fn stop() { unsafe { desktop_streamer_stop(); } }
}

pub struct FramePacker;

impl FramePacker {
    pub fn pack(rgb: &[u8], width: u32, height: u32, quality: i32) -> Result<Vec<u8>, String> {
        let mut out = vec![0u8; (width * height * 4) as usize];
        let mut out_len: i32 = 0;
        let ret = unsafe {
            frame_packer_pack(rgb.as_ptr(), width as i32, height as i32,
                              quality, out.as_mut_ptr(), &mut out_len)
        };
        if ret == 0 {
            out.truncate(out_len as usize);
            Ok(out)
        } else {
            Err(format!("pack failed: {}", ret))
        }
    }
}

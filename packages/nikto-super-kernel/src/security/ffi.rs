use std::ffi::CString;
use std::os::raw::c_char;

extern "C" {
    fn firewall_enable(iface: *const c_char) -> i32;
    fn firewall_disable() -> i32;
    fn firewall_block(ip: *const c_char, port: i32) -> i32;
    fn sandbox_exec(path: *const c_char, args: *const *const c_char,
                    timeout_ms: i32) -> i32;
    fn ebpf_attach(prog_path: *const c_char, hook: i32) -> i32;
    fn ebpf_detach(id: i32) -> i32;
}

pub struct Firewall;

impl Firewall {
    pub fn enable(iface: &str) -> Result<(), String> {
        let c = CString::new(iface).map_err(|e| format!("CString: {}", e))?;
        let r = unsafe { firewall_enable(c.as_ptr()) };
        if r == 0 { Ok(()) } else { Err(format!("firewall_enable: {}", r)) }
    }

    pub fn disable() -> Result<(), String> {
        let r = unsafe { firewall_disable() };
        if r == 0 { Ok(()) } else { Err(format!("firewall_disable: {}", r)) }
    }

    pub fn block(ip: &str, port: i32) -> Result<(), String> {
        let c = CString::new(ip).map_err(|e| format!("CString: {}", e))?;
        let r = unsafe { firewall_block(c.as_ptr(), port) };
        if r == 0 { Ok(()) } else { Err(format!("firewall_block: {}", r)) }
    }
}

pub struct Sandbox;

impl Sandbox {
    pub fn exec(path: &str, args: &[&str], timeout_ms: i32) -> Result<i32, String> {
        use std::ffi::CString;
        let c_path = CString::new(path).map_err(|e| format!("CString: {}", e))?;
        let mut cargs: Vec<CString> = args.iter()
            .map(|a| CString::new(*a).unwrap()).collect();
        cargs.push(CString::new("").unwrap()); // null terminator
        let mut ptrs: Vec<*const c_char> = cargs.iter().map(|c| c.as_ptr()).collect();
        ptrs.push(std::ptr::null());
        let r = unsafe { sandbox_exec(c_path.as_ptr(), ptrs.as_ptr(), timeout_ms) };
        if r >= 0 { Ok(r) } else { Err(format!("sandbox_exec: {}", r)) }
    }
}

pub struct EBpf;

impl EBpf {
    pub fn attach(prog_path: &str, hook: i32) -> Result<i32, String> {
        let c = CString::new(prog_path).map_err(|e| format!("CString: {}", e))?;
        let id = unsafe { ebpf_attach(c.as_ptr(), hook) };
        if id >= 0 { Ok(id) } else { Err(format!("ebpf_attach: {}", id)) }
    }

    pub fn detach(id: i32) -> Result<(), String> {
        let r = unsafe { ebpf_detach(id) };
        if r == 0 { Ok(()) } else { Err(format!("ebpf_detach: {}", r)) }
    }
}

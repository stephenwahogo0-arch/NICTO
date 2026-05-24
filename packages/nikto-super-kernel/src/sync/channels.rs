use std::collections::VecDeque;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

type Msg = Vec<u8>;

/// An MPMC channel pair built on a shared deque with spin-lock semantics.
pub struct Channel {
    inner: Arc<Mutex<VecDeque<Msg>>>,
    closed: Arc<AtomicBool>,
}

impl Channel {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(Mutex::new(VecDeque::new())),
            closed: Arc::new(AtomicBool::new(false)),
        }
    }

    pub fn send(&self, msg: Msg) -> Result<(), String> {
        if self.closed.load(Ordering::Acquire) {
            return Err("channel closed".into());
        }
        let mut q = self.inner.lock().map_err(|e| format!("lock: {}", e))?;
        q.push_back(msg);
        Ok(())
    }

    pub fn recv(&self) -> Result<Option<Msg>, String> {
        let mut q = self.inner.lock().map_err(|e| format!("lock: {}", e))?;
        Ok(q.pop_front())
    }

    pub fn recv_timeout(&self, timeout: Duration) -> Result<Option<Msg>, String> {
        let deadline = std::time::Instant::now() + timeout;
        loop {
            if std::time::Instant::now() >= deadline {
                return Ok(None);
            }
            let mut q = self.inner.lock().map_err(|e| format!("lock: {}", e))?;
            if let Some(msg) = q.pop_front() {
                return Ok(Some(msg));
            }
            drop(q);
            thread::sleep(Duration::from_micros(100));
        }
    }

    pub fn close(&self) {
        self.closed.store(true, Ordering::Release);
    }
}

unsafe impl Send for Channel {}
unsafe impl Sync for Channel {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn send_recv() {
        let ch = Channel::new();
        ch.send(b"hello".to_vec()).unwrap();
        let out = ch.recv().unwrap().unwrap();
        assert_eq!(out, b"hello");
    }

    #[test]
    fn close_blocks_send() {
        let ch = Channel::new();
        ch.close();
        assert!(ch.send(b"x".to_vec()).is_err());
    }
}

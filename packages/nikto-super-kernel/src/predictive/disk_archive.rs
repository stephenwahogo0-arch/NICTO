use std::fs::{self, File, OpenOptions};
use std::io::{self, Write, Read};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};
use bincode;

use crate::predictive::types::{DiagnosticReport, PredictionMatrix};

pub struct DiagnosticArchive {
    base_path: PathBuf,
}

impl DiagnosticArchive {
    pub fn new(base_path: &str) -> Self {
        let path = PathBuf::from(base_path);
        fs::create_dir_all(&path).ok();
        Self { base_path: path }
    }

    pub fn write_report(&self, report: &DiagnosticReport) -> io::Result<u64> {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos();
        let filename = format!("diagnostic_{}.bin", timestamp);
        let path = self.base_path.join(&filename);

        let encoded: Vec<u8> = bincode::serialize(report)
            .map_err(|e| io::Error::new(io::ErrorKind::Other, e.to_string()))?;

        // O_DIRECT + O_SYNC write when available on Linux
        #[cfg(target_os = "linux")]
        {
            use std::os::unix::fs::OpenOptionsExt;
            let mut file = OpenOptions::new()
                .write(true)
                .create(true)
                .custom_flags(libc::O_DIRECT | libc::O_SYNC)
                .open(&path)?;
            file.write_all(&encoded)?;
            file.sync_all()?;
        }

        #[cfg(not(target_os = "linux"))]
        {
            let mut file = File::create(&path)?;
            file.write_all(&encoded)?;
            file.sync_all()?;
        }

        Ok(encoded.len() as u64)
    }

    pub fn write_prediction(&self, matrix: &PredictionMatrix) -> io::Result<u64> {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos();
        let filename = format!("prediction_{}.bin", timestamp);
        let path = self.base_path.join(&filename);

        let encoded: Vec<u8> = bincode::serialize(matrix)
            .map_err(|e| io::Error::new(io::ErrorKind::Other, e.to_string()))?;

        let mut file = File::create(&path)?;
        file.write_all(&encoded)?;
        file.sync_all()?;

        Ok(encoded.len() as u64)
    }

    pub fn read_report(&self, path: &str) -> io::Result<DiagnosticReport> {
        let data = fs::read(path)?;
        let report: DiagnosticReport = bincode::deserialize(&data)
            .map_err(|e| io::Error::new(io::ErrorKind::InvalidData, e.to_string()))?;
        Ok(report)
    }

    pub fn write_diag(&self, report: &DiagnosticReport) -> Result<(), String> {
        self.write_report(report).map(|_| ()).map_err(|e| e.to_string())
    }

    pub fn read_diag(&self, index: usize) -> Result<DiagnosticReport, String> {
        let archives = self.list_archives().map_err(|e| e.to_string())?;
        let path = archives.get(index).ok_or_else(|| format!("index {} out of range ({} archives)", index, archives.len()))?;
        self.read_report(path).map_err(|e| e.to_string())
    }

    pub fn list_archives(&self) -> io::Result<Vec<String>> {
        let mut entries = Vec::new();
        if self.base_path.exists() {
            for entry in fs::read_dir(&self.base_path)? {
                let entry = entry?;
                if entry.file_name().to_string_lossy().contains("diagnostic_") {
                    entries.push(entry.path().to_string_lossy().to_string());
                }
            }
        }
        entries.sort();
        Ok(entries)
    }
}

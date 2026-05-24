use std::collections::HashMap;

use pyo3::prelude::*;

/// Sector 2 — Brain: lightweight neural inference, knowledge synthesis, context graph.
#[pyclass]
pub struct NeuralCore {
    records: Vec<KnowledgeRecord>,
    index: HashMap<String, Vec<usize>>,
}

#[derive(Clone, Debug)]
struct KnowledgeRecord {
    topic: String,
    content: String,
    embedding: Vec<f32>,
    timestamp: u64,
}

impl NeuralCore {
    pub fn new() -> Self {
        Self { records: Vec::new(), index: HashMap::new() }
    }

    pub fn simple_embed(text: &str, dim: usize) -> Vec<f32> {
        let bytes = text.as_bytes();
        let mut emb = vec![0.0f32; dim];
        for (i, &b) in bytes.iter().enumerate() {
            emb[i % dim] += b as f32 / 255.0;
        }
        let norm = emb.iter().map(|v| v * v).sum::<f32>().sqrt().max(1e-8);
        emb.iter_mut().for_each(|v| *v /= norm);
        emb
    }
}

#[pymethods]
impl NeuralCore {
    pub fn ingest(&mut self, topic: &str, content: &str) {
        let embedding = Self::simple_embed(content, 64);
        let idx = self.records.len();
        self.records.push(KnowledgeRecord {
            topic: topic.into(),
            content: content.into(),
            embedding,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
        });
        self.index.entry(topic.into()).or_default().push(idx);
    }

    pub fn recall(&self, query: &str, top_k: usize) -> Vec<String> {
        let q_emb = Self::simple_embed(query, 64);
        let mut scored: Vec<(f32, usize)> = self.records.iter().enumerate()
            .map(|(i, r)| (cosine_sim(&q_emb, &r.embedding), i))
            .collect();
        scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
        scored.truncate(top_k);
        scored.into_iter()
            .map(|(_, i)| format!("[{}] {}", self.records[i].topic, self.records[i].content))
            .collect()
    }

    pub fn count(&self) -> usize { self.records.len() }
}

pub fn cosine_sim(a: &[f32], b: &[f32]) -> f32 {
    let dot: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let na: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt().max(1e-8);
    let nb: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt().max(1e-8);
    dot / (na * nb)
}

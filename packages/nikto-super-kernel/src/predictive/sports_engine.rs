use std::collections::HashMap;
use rand_distr::{Distribution, StandardNormal};
use rayon::prelude::*;
use pyo3::prelude::*;

#[derive(Clone, Debug)]
#[pyclass]
pub struct TeamRecord {
    #[pyo3(get)]
    pub team: String,
    #[pyo3(get)]
    pub wins: u32,
    #[pyo3(get)]
    pub losses: u32,
    #[pyo3(get)]
    pub draws: u32,
    #[pyo3(get)]
    pub goals_for: u32,
    #[pyo3(get)]
    pub goals_against: u32,
    #[pyo3(get)]
    pub elo: f64,
}

#[derive(Clone, Debug)]
#[pyclass]
pub struct MatchResult {
    #[pyo3(get)]
    pub team_a: String,
    #[pyo3(get)]
    pub team_b: String,
    #[pyo3(get)]
    pub score_a: u32,
    #[pyo3(get)]
    pub score_b: u32,
}

#[derive(Clone, Debug)]
#[pyclass]
pub struct SportsPrediction {
    #[pyo3(get)]
    pub team_a: String,
    #[pyo3(get)]
    pub team_b: String,
    #[pyo3(get)]
    pub prob_a: f64,
    #[pyo3(get)]
    pub prob_b: f64,
    #[pyo3(get)]
    pub prob_draw: f64,
    #[pyo3(get)]
    pub expected_goals_a: f64,
    #[pyo3(get)]
    pub expected_goals_b: f64,
    #[pyo3(get)]
    pub confidence: f64,
    #[pyo3(get)]
    pub simulation_count: u32,
}

#[pymethods]
impl SportsPrediction {
    fn __repr__(&self) -> String {
        format!("SportsPrediction({} vs {} | A:{:.1}% B:{:.1}% Draw:{:.1}% | conf:{:.2})",
                self.team_a, self.team_b,
                self.prob_a * 100.0, self.prob_b * 100.0, self.prob_draw * 100.0,
                self.confidence)
    }
}

#[pymethods]
impl TeamRecord {
    fn __repr__(&self) -> String {
        format!("Team({} | W:{} L:{} D:{} | GF:{} GA:{} | Elo:{:.0})",
                self.team, self.wins, self.losses, self.draws,
                self.goals_for, self.goals_against, self.elo)
    }
}

#[pymethods]
impl MatchResult {
    #[new]
    pub fn new(team_a: String, team_b: String, score_a: u32, score_b: u32) -> Self {
        Self { team_a, team_b, score_a, score_b }
    }

    fn __repr__(&self) -> String {
        format!("Match({} {} - {} {})", self.team_a, self.score_a, self.score_b, self.team_b)
    }
}

pub struct SportsPredictionEngine {
    pub teams: HashMap<String, TeamRecord>,
    pub k_factor: f64,
    pub home_advantage: f64,
    pub simulation_paths: u32,
}

impl SportsPredictionEngine {
    pub fn new(simulation_paths: u32) -> Self {
        Self {
            teams: HashMap::new(),
            k_factor: 32.0,
            home_advantage: 100.0,
            simulation_paths,
        }
    }

    pub fn ingest_match(&mut self, result: &MatchResult, neutral: bool) {
        let team_a_elo = self.teams.get(&result.team_a).map_or(1500.0, |t| t.elo);
        let team_b_elo = self.teams.get(&result.team_b).map_or(1500.0, |t| t.elo);

        let ra = team_a_elo + if neutral { 0.0 } else { self.home_advantage };
        let ea = 1.0 / (1.0 + 10.0_f64.powf((team_b_elo - ra) / 400.0));
        let eb = 1.0 - ea;

        let sa = if result.score_a > result.score_b { 1.0 }
                 else if result.score_a == result.score_b { 0.5 }
                 else { 0.0 };

        let new_elo_a = team_a_elo + self.k_factor * (sa - ea);
        let new_elo_b = team_b_elo + self.k_factor * ((1.0 - sa) - eb);

        self.teams.entry(result.team_a.clone()).or_insert(TeamRecord {
            team: result.team_a.clone(), wins: 0, losses: 0, draws: 0,
            goals_for: 0, goals_against: 0, elo: 1500.0,
        });
        self.teams.entry(result.team_b.clone()).or_insert(TeamRecord {
            team: result.team_b.clone(), wins: 0, losses: 0, draws: 0,
            goals_for: 0, goals_against: 0, elo: 1500.0,
        });

        let a = self.teams.get_mut(&result.team_a).unwrap();
        a.elo = new_elo_a;
        a.goals_for += result.score_a;
        a.goals_against += result.score_b;
        if result.score_a > result.score_b { a.wins += 1; }
        else if result.score_a == result.score_b { a.draws += 1; }
        else { a.losses += 1; }

        let b = self.teams.get_mut(&result.team_b).unwrap();
        b.elo = new_elo_b;
        b.goals_for += result.score_b;
        b.goals_against += result.score_a;
        if result.score_b > result.score_a { b.wins += 1; }
        else if result.score_a == result.score_b { b.draws += 1; }
        else { b.losses += 1; }
    }

    pub fn ingest_bulk(&mut self, results: &[MatchResult]) {
        for r in results {
            self.ingest_match(r, false);
        }
    }

    pub fn predict(&self, team_a: &str, team_b: &str, neutral: bool) -> SportsPrediction {
        let ra = self.teams.get(team_a).map_or(1500.0, |t| t.elo) + if neutral { 0.0 } else { self.home_advantage };
        let rb = self.teams.get(team_b).map_or(1500.0, |t| t.elo);

        let expected_a = 1.0 / (1.0 + 10.0_f64.powf((rb - ra) / 400.0));
        let expected_b = 1.0 - expected_a;

        let avg_goals_a = self.teams.get(team_a).map_or(1.5, |t| {
            let total = t.goals_for + t.goals_against;
            if total == 0 { 1.5 } else { t.goals_for as f64 / (t.wins + t.losses + t.draws).max(1) as f64 }
        });
        let avg_goals_b = self.teams.get(team_b).map_or(1.5, |t| {
            let total = t.goals_for + t.goals_against;
            if total == 0 { 1.5 } else { t.goals_for as f64 / (t.wins + t.losses + t.draws).max(1) as f64 }
        });

        let mut rng = rand::thread_rng();
        let normal = StandardNormal;
        let outcomes: Vec<(u32, u32)> = (0..self.simulation_paths)
            .into_par_iter()
            .map(|_| {
                let mut local_rng = rand::thread_rng();
                let epsilon_a: f64 = Distribution::<f64>::sample(&StandardNormal, &mut local_rng);
                let epsilon_b: f64 = Distribution::<f64>::sample(&StandardNormal, &mut local_rng);
                let noise_a = epsilon_a * 0.3;
                let noise_b = epsilon_b * 0.3;
                let goals_a = (avg_goals_a + noise_a).max(0.0).round() as u32;
                let goals_b = (avg_goals_b + noise_b).max(0.0).round() as u32;
                (goals_a, goals_b)
            })
            .collect();

        let total = outcomes.len() as f64;
        let wins_a = outcomes.iter().filter(|(a, b)| a > b).count() as f64;
        let wins_b = outcomes.iter().filter(|(a, b)| b > a).count() as f64;
        let draws = outcomes.iter().filter(|(a, b)| a == b).count() as f64;

        let exp_goals_a: f64 = outcomes.iter().map(|(a, _)| *a as f64).sum::<f64>() / total;
        let exp_goals_b: f64 = outcomes.iter().map(|(_, b)| *b as f64).sum::<f64>() / total;

        let confidence = (expected_a - 0.5).abs() * 2.0;

        SportsPrediction {
            team_a: team_a.to_string(),
            team_b: team_b.to_string(),
            prob_a: wins_a / total,
            prob_b: wins_b / total,
            prob_draw: draws / total,
            expected_goals_a: exp_goals_a,
            expected_goals_b: exp_goals_b,
            confidence,
            simulation_count: self.simulation_paths,
        }
    }

    pub fn team_count(&self) -> usize {
        self.teams.len()
    }

    pub fn team_summary(&self, team: &str) -> Option<&TeamRecord> {
        self.teams.get(team)
    }

    pub fn top_teams(&self, n: usize) -> Vec<(&String, &TeamRecord)> {
        let mut sorted: Vec<_> = self.teams.iter().collect();
        sorted.sort_by(|a, b| b.1.elo.partial_cmp(&a.1.elo).unwrap_or(std::cmp::Ordering::Equal));
        sorted.into_iter().take(n).collect()
    }
}

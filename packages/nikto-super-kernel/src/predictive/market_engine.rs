use std::f64::consts::PI;
use rand::Rng;
use rand_distr::{Distribution, StandardNormal};
use rayon::prelude::*;

use crate::predictive::types::*;

pub struct MarketEngine {
    simulations: u32,
    horizon_days: u32,
}

impl MarketEngine {
    pub fn new(simulations: u32, horizon_days: u32) -> Self {
        Self { simulations, horizon_days }
    }

    pub fn predict(&self, ohlcv_data: &[MarketOHLCV]) -> PredictionMatrix {
        if ohlcv_data.len() < 30 {
            return PredictionMatrix {
                horizon_days: self.horizon_days,
                simulations: self.simulations,
                price_paths: vec![],
                overall_probability: 0.5,
                value_at_risk_95: 0.0,
                expected_return: 0.0,
                volatility: 0.0,
            };
        }

        // Compute log returns
        let mut log_returns = Vec::with_capacity(ohlcv_data.len() - 1);
        for i in 1..ohlcv_data.len() {
            let r = (ohlcv_data[i].close / ohlcv_data[i - 1].close).ln();
            log_returns.push(r);
        }

        // Compute drift (μ) and volatility (σ)
        let n = log_returns.len() as f64;
        let mean = log_returns.iter().sum::<f64>() / n;
        let variance = log_returns.iter().map(|r| (r - mean).powi(2)).sum::<f64>() / (n - 1.0);
        let daily_vol = variance.sqrt();
        let annual_vol = daily_vol * (252.0_f64).sqrt();
        let daily_drift = mean;
        let last_price = ohlcv_data.last().unwrap().close;
        let dt = 1.0 / 252.0; // ~1 trading day

        // Parallel Monte Carlo simulation
        let final_prices: Vec<f64> = (0..self.simulations)
            .into_par_iter()
            .map(|_| {
                let mut rng = rand::thread_rng();
                let normal = StandardNormal;
                let mut price = last_price;
                for _ in 0..self.horizon_days {
                    let epsilon: f64 = normal.sample(&mut rng);
                    price *= (daily_drift - 0.5 * variance + daily_vol * epsilon).exp();
                }
                price
            })
            .collect();

        // Compute probability distribution
        let up_count = final_prices.iter().filter(|p| **p > last_price).count() as f64;
        let overall_prob = up_count / self.simulations as f64;

        // Sort for VaR calculation
        let mut sorted = final_prices.clone();
        sorted.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let var_95_idx = (self.simulations as f64 * 0.05) as usize;
        let var_95 = (sorted[var_95_idx] - last_price) / last_price;

        let expected_return = (sorted.iter().sum::<f64>() / self.simulations as f64 - last_price) / last_price;

        // Build daily price paths
        let mut price_paths = Vec::with_capacity(self.horizon_days as usize);
        for day in 0..self.horizon_days {
            let day_final_prices: Vec<f64> = (0..self.simulations)
                .into_par_iter()
                .map(|_| {
                    let mut rng = rand::thread_rng();
                    let normal = StandardNormal;
                    let mut price = last_price;
                    for _ in 0..=day {
                        let epsilon: f64 = normal.sample(&mut rng);
                        price *= (daily_drift - 0.5 * variance + daily_vol * epsilon).exp();
                    }
                    price
                })
                .collect();

            let mut sorted_day = day_final_prices.clone();
            sorted_day.sort_by(|a, b| a.partial_cmp(b).unwrap());
            let mean_day = day_final_prices.iter().sum::<f64>() / self.simulations as f64;
            let upper = sorted_day[(self.simulations as f64 * 0.975) as usize];
            let lower = sorted_day[(self.simulations as f64 * 0.025) as usize];

            let probs = vec![0.5_f64; self.horizon_days as usize]; // simplified
            price_paths.push(PricePath {
                probabilities: probs,
                confidence_upper: vec![upper; self.horizon_days as usize],
                confidence_lower: vec![lower; self.horizon_days as usize],
                expected: vec![mean_day; self.horizon_days as usize],
            });
        }

        PredictionMatrix {
            horizon_days: self.horizon_days,
            simulations: self.simulations,
            price_paths,
            overall_probability: overall_prob,
            value_at_risk_95: var_95,
            expected_return,
            volatility: annual_vol,
        }
    }

    pub fn parse_csv(&self, csv_data: &str) -> Vec<MarketOHLCV> {
        let mut reader = csv::ReaderBuilder::new()
            .has_headers(true)
            .from_reader(csv_data.as_bytes());
        let mut data = Vec::new();

        for result in reader.records() {
            if let Ok(record) = result {
                if record.len() >= 6 {
                    if let (Ok(open), Ok(high), Ok(low), Ok(close), Ok(volume)) = (
                        record[1].parse::<f64>(),
                        record[2].parse::<f64>(),
                        record[3].parse::<f64>(),
                        record[4].parse::<f64>(),
                        record[5].parse::<f64>(),
                    ) {
                        data.push(MarketOHLCV {
                            timestamp: record[0].parse::<u64>().unwrap_or(0),
                            open,
                            high,
                            low,
                            close,
                            volume,
                        });
                    }
                }
            }
        }
        data
    }

    pub fn simulation_count(&self) -> u32 { self.simulations }
}

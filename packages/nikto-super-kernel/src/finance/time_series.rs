use rayon::prelude::*;

use crate::predictive::types::MarketOHLCV;
use crate::finance::types::TimeSeriesAnalysis;

pub struct TimeSeriesEngine;

impl TimeSeriesEngine {
    pub fn analyze(ohlcv: &[MarketOHLCV]) -> TimeSeriesAnalysis {
        let closes: Vec<f64> = ohlcv.iter().map(|d| d.close).collect();
        let n = closes.len();
        if n < 50 {
            return TimeSeriesAnalysis {
                sma_20: vec![], sma_50: vec![], ema_12: vec![], ema_26: vec![],
                upper_band: vec![], lower_band: vec![], atr: vec![],
                regression_slope: 0.0, regression_intercept: 0.0,
                r_squared: 0.0, volatility: 0.0, trend: "InsufficientData".into(),
            };
        }

        let sma_20 = Self::sma(&closes, 20);
        let sma_50 = Self::sma(&closes, 50);
        let ema_12 = Self::ema(&closes, 12);
        let ema_26 = Self::ema(&closes, 26);

        let std_20 = Self::rolling_std(&closes, 20, &sma_20);
        let upper_band: Vec<f64> = sma_20.iter().zip(std_20.iter())
            .map(|(m, s)| m + 2.0 * s).collect();
        let lower_band: Vec<f64> = sma_20.iter().zip(std_20.iter())
            .map(|(m, s)| m - 2.0 * s).collect();

        let atr = Self::compute_atr(ohlcv, 14);

        let (slope, intercept, r_sq) = Self::linear_regression(&closes);

        // Compute log returns for volatility
        let log_returns: Vec<f64> = closes.windows(2)
            .map(|w| (w[1] / w[0]).ln()).collect();
        let mean_ret = log_returns.iter().sum::<f64>() / log_returns.len() as f64;
        let variance = log_returns.par_iter()
            .map(|r| (r - mean_ret).powi(2)).sum::<f64>() / (log_returns.len() - 1) as f64;
        let daily_vol = variance.sqrt();
        let annual_vol = daily_vol * 252.0_f64.sqrt();

        let trend = if slope > 0.0001 { "Bullish".into() }
                    else if slope < -0.0001 { "Bearish".into() }
                    else { "Sideways".into() };

        TimeSeriesAnalysis {
            sma_20, sma_50, ema_12, ema_26,
            upper_band, lower_band, atr,
            regression_slope: slope,
            regression_intercept: intercept,
            r_squared: r_sq,
            volatility: annual_vol,
            trend,
        }
    }

    fn sma(data: &[f64], period: usize) -> Vec<f64> {
        if data.len() < period { return vec![]; }
        let mut result = Vec::with_capacity(data.len());
        // Pad front with NaN-equivalent (f64::NAN not serializable, use 0.0)
        for _ in 0..period - 1 { result.push(0.0); }
        for i in (period - 1)..data.len() {
            let sum: f64 = data[i - (period - 1)..=i].iter().sum();
            result.push(sum / period as f64);
        }
        result
    }

    fn ema(data: &[f64], period: usize) -> Vec<f64> {
        if data.len() < period { return vec![]; }
        let k = 2.0 / (period + 1) as f64;
        let mut result = Vec::with_capacity(data.len());
        for _ in 0..period - 1 { result.push(0.0); }
        let init_sma: f64 = data[..period].iter().sum::<f64>() / period as f64;
        result.push(init_sma);
        for i in period..data.len() {
            let ema = (data[i] - result.last().unwrap()) * k + result.last().unwrap();
            result.push(ema);
        }
        result
    }

    fn rolling_std(data: &[f64], period: usize, mean: &[f64]) -> Vec<f64> {
        if data.len() < period || mean.len() < period { return vec![]; }
        let mut result = Vec::with_capacity(data.len());
        for _ in 0..period - 1 { result.push(0.0); }
        for i in (period - 1)..data.len() {
            let variance: f64 = data[i - (period - 1)..=i].iter()
                .zip(mean[i - (period - 1)..=i].iter())
                .map(|(d, m)| (d - m).powi(2)).sum::<f64>() / period as f64;
            result.push(variance.sqrt());
        }
        result
    }

    fn compute_atr(ohlcv: &[MarketOHLCV], period: usize) -> Vec<f64> {
        if ohlcv.len() < period + 1 { return vec![]; }
        let mut tr_values = Vec::with_capacity(ohlcv.len());
        tr_values.push(ohlcv[0].high - ohlcv[0].low); // first TR
        for i in 1..ohlcv.len() {
            let high_low = ohlcv[i].high - ohlcv[i].low;
            let high_pc = (ohlcv[i].high - ohlcv[i - 1].close).abs();
            let low_pc = (ohlcv[i].low - ohlcv[i - 1].close).abs();
            tr_values.push(high_low.max(high_pc).max(low_pc));
        }
        Self::sma(&tr_values, period)
    }

    fn linear_regression(data: &[f64]) -> (f64, f64, f64) {
        let n = data.len() as f64;
        if n < 2.0 { return (0.0, 0.0, 0.0); }
        let x_mean = (n - 1.0) / 2.0;
        let y_mean = data.iter().sum::<f64>() / n;

        let (num, den, ss_res, ss_tot) = data.iter().enumerate()
            .map(|(i, y)| {
                let x = i as f64;
                ((x - x_mean) * (y - y_mean), (x - x_mean).powi(2),
                 (y - (0.0)).powi(2), (y - y_mean).powi(2))
            })
            .reduce(|a, b| (a.0 + b.0, a.1 + b.1, a.2 + b.2, a.3 + b.3))
            .unwrap_or((0.0, 0.0, 0.0, 0.0));

        let slope = if den != 0.0 { num / den } else { 0.0 };
        let intercept = y_mean - slope * x_mean;

        // Recompute R²
        let (ss_res, ss_tot) = data.iter().enumerate()
            .map(|(i, y)| {
                let y_pred = slope * i as f64 + intercept;
                ((y - y_pred).powi(2), (y - y_mean).powi(2))
            })
            .reduce(|a, b| (a.0 + b.0, a.1 + b.1))
            .unwrap_or((0.0, 0.0));

        let r_sq = if ss_tot != 0.0 { 1.0 - ss_res / ss_tot } else { 0.0 };
        (slope, intercept, r_sq)
    }
}

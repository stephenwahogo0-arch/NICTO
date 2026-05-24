use pyo3::prelude::*;
use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct TradeProposal {
    #[pyo3(get, set)]
    pub symbol: String,
    #[pyo3(get, set)]
    pub side: String,
    #[pyo3(get, set)]
    pub quantity: f64,
    #[pyo3(get, set)]
    pub price: f64,
    #[pyo3(get, set)]
    pub stop_loss: f64,
    #[pyo3(get, set)]
    pub take_profit: f64,
}

#[pymethods]
impl TradeProposal {
    #[new]
    pub fn new() -> Self {
        Self { symbol: String::new(), side: String::new(),
               quantity: 0.0, price: 0.0, stop_loss: 0.0, take_profit: 0.0 }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct PortfolioState {
    #[pyo3(get, set)]
    pub total_equity: f64,
    #[pyo3(get, set)]
    pub daily_pnl: f64,
    #[pyo3(get, set)]
    pub daily_loss_limit: f64,
    #[pyo3(get, set)]
    pub max_drawdown_pct: f64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct RiskVerdict {
    #[pyo3(get)]
    pub allowed: bool,
    #[pyo3(get)]
    pub reason: String,
    #[pyo3(get)]
    pub max_allowed_quantity: f64,
    #[pyo3(get)]
    pub max_allowed_value: f64,
    #[pyo3(get)]
    pub breach_severity: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct OrderResult {
    #[pyo3(get)]
    pub order_id: String,
    #[pyo3(get)]
    pub symbol: String,
    #[pyo3(get)]
    pub side: String,
    #[pyo3(get)]
    pub quantity: f64,
    #[pyo3(get)]
    pub price: f64,
    #[pyo3(get)]
    pub filled: bool,
    #[pyo3(get)]
    pub timestamp: u64,
    #[pyo3(get)]
    pub audit_id: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct TimeSeriesAnalysis {
    #[pyo3(get)]
    pub sma_20: Vec<f64>,
    #[pyo3(get)]
    pub sma_50: Vec<f64>,
    #[pyo3(get)]
    pub ema_12: Vec<f64>,
    #[pyo3(get)]
    pub ema_26: Vec<f64>,
    #[pyo3(get)]
    pub upper_band: Vec<f64>,
    #[pyo3(get)]
    pub lower_band: Vec<f64>,
    #[pyo3(get)]
    pub atr: Vec<f64>,
    #[pyo3(get)]
    pub regression_slope: f64,
    #[pyo3(get)]
    pub regression_intercept: f64,
    #[pyo3(get)]
    pub r_squared: f64,
    #[pyo3(get)]
    pub volatility: f64,
    #[pyo3(get)]
    pub trend: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[pyclass]
pub struct BacktestResult {
    #[pyo3(get)]
    pub total_return: f64,
    #[pyo3(get)]
    pub win_ratio: f64,
    #[pyo3(get)]
    pub max_drawdown: f64,
    #[pyo3(get)]
    pub sharpe_ratio: f64,
    #[pyo3(get)]
    pub sortino_ratio: f64,
    #[pyo3(get)]
    pub total_trades: u32,
    #[pyo3(get)]
    pub winning_trades: u32,
    #[pyo3(get)]
    pub losing_trades: u32,
    #[pyo3(get)]
    pub avg_win: f64,
    #[pyo3(get)]
    pub avg_loss: f64,
    #[pyo3(get)]
    pub profit_factor: f64,
    #[pyo3(get)]
    pub equity_curve: Vec<f64>,
}

#[pymethods]
impl RiskVerdict {
    fn __repr__(&self) -> String {
        format!("RiskVerdict(allowed={}, reason={}, severity={})",
                self.allowed, self.reason, self.breach_severity)
    }
}

#[pymethods]
impl TimeSeriesAnalysis {
    fn __repr__(&self) -> String {
        format!("TimeSeriesAnalysis(trend={}, volatility={:.2}%, r²={:.3})",
                self.trend, self.volatility * 100.0, self.r_squared)
    }
}

#[pymethods]
impl BacktestResult {
    fn __repr__(&self) -> String {
        format!("BacktestResult(return={:.2}%, sharpe={:.2}, max_dd={:.2}%, trades={})",
                self.total_return * 100.0, self.sharpe_ratio, self.max_drawdown * 100.0, self.total_trades)
    }
}

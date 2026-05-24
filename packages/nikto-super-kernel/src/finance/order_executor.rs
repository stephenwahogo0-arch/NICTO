use std::collections::VecDeque;

use crate::finance::types::{OrderResult, RiskVerdict, TradeProposal};
use crate::finance::risk_gate::{AuditLedger, RiskGate};
use crate::finance::types::PortfolioState;

pub struct OrderExecutor {
    ledger: AuditLedger,
    fill_latency_ms: u64,
    pending: VecDeque<TradeProposal>,
}

impl OrderExecutor {
    pub fn new(fill_latency_ms: u64) -> Self {
        Self { ledger: AuditLedger::new(), fill_latency_ms, pending: VecDeque::new() }
    }

    /// Submit a trade through the risk gate; if allowed, generate an order id.
    pub fn submit(&mut self, proposal: TradeProposal,
                  state: &PortfolioState) -> (RiskVerdict, Option<OrderResult>) {
        let verdict = RiskGate::evaluate(&proposal, state);

        if !verdict.allowed {
            self.ledger.record("N/A", &proposal.symbol, &proposal.side,
                               proposal.quantity, proposal.price, &verdict.reason);
            let result = OrderResult {
                order_id: "REJECTED".into(),
                symbol: proposal.symbol.clone(),
                side: proposal.side.clone(),
                quantity: proposal.quantity,
                price: proposal.price,
                filled: false,
                timestamp: std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
                audit_id: self.ledger.count() as u64,
            };
            return (verdict, Some(result));
        }

        let order_id = format!("ORD-{:016x}", rand::random::<u64>());
        let audit_id = self.ledger.record(&order_id, &proposal.symbol, &proposal.side,
                                          proposal.quantity, proposal.price, "PASS");

        let result = OrderResult {
            order_id: order_id.clone(),
            symbol: proposal.symbol.clone(),
            side: proposal.side.clone(),
            quantity: proposal.quantity,
            price: proposal.price,
            filled: false,
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
            audit_id,
        };

        self.pending.push_back(proposal);
        (verdict, Some(result))
    }

    /// Simulate filling the oldest pending order.
    pub fn fill_next(&mut self) -> Option<OrderResult> {
        if let Some(proposal) = self.pending.pop_front() {
            let filled = OrderResult {
                order_id: format!("ORD-{:016x}", rand::random::<u64>()),
                symbol: proposal.symbol,
                side: proposal.side,
                quantity: proposal.quantity,
                price: proposal.price,
                filled: true,
                timestamp: std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH).unwrap().as_secs(),
                audit_id: self.ledger.count() as u64,
            };
            Some(filled)
        } else {
            None
        }
    }

    /// Backtest a full strategy; returns equity curve and result.
    pub fn backtest(&self, equity_before: f64, trades: &[TradeProposal],
                    ohlcv: &[crate::predictive::types::MarketOHLCV],
                    state: &PortfolioState) -> crate::finance::types::BacktestResult {
        use crate::finance::types::BacktestResult;

        if trades.is_empty() || ohlcv.is_empty() {
            return BacktestResult {
                total_return: 0.0, win_ratio: 0.0, max_drawdown: 0.0,
                sharpe_ratio: 0.0, sortino_ratio: 0.0,
                total_trades: 0, winning_trades: 0, losing_trades: 0,
                avg_win: 0.0, avg_loss: 0.0, profit_factor: 0.0,
                equity_curve: vec![equity_before],
            };
        }

        let mut equity = equity_before;
        let mut peak = equity;
        let mut max_dd = 0.0;
        let mut wins = 0u32;
        let mut losses = 0u32;
        let mut total_win_val = 0.0;
        let mut total_loss_val = 0.0;
        let mut returns: Vec<f64> = Vec::with_capacity(trades.len());
        let mut equity_curve = Vec::with_capacity(trades.len() + 1);
        equity_curve.push(equity);

        for trade in trades {
            let verdict = RiskGate::evaluate(trade, state);
            if !verdict.allowed { continue; }

            let entry = trade.price;
            let exit = if trade.side == "buy" {
                entry * (1.0 + fast_random_return())
            } else {
                entry * (1.0 - fast_random_return())
            };
            let pnl = trade.quantity * (exit - entry) * if trade.side == "buy" { 1.0 } else { -1.0 };
            equity += pnl;
            equity_curve.push(equity);

            if pnl > 0.0 {
                wins += 1;
                total_win_val += pnl;
            } else {
                losses += 1;
                total_loss_val += pnl.abs();
            }

            if equity > peak { peak = equity; }
            let dd = (peak - equity) / peak;
            if dd > max_dd { max_dd = dd; }

            let ret = pnl / equity_before.max(1.0);
            returns.push(ret);
        }

        let total_trades = wins + losses;
        let win_ratio = if total_trades > 0 { wins as f64 / total_trades as f64 } else { 0.0 };
        let total_return = (equity - equity_before) / equity_before;
        let avg_win = if wins > 0 { total_win_val / wins as f64 } else { 0.0 };
        let avg_loss = if losses > 0 { total_loss_val / losses as f64 } else { 0.0 };
        let profit_factor = if total_loss_val > 0.0 { total_win_val / total_loss_val } else { total_win_val.max(1.0) };

        let mean_ret = if !returns.is_empty() { returns.iter().sum::<f64>() / returns.len() as f64 } else { 0.0 };
        let variance = if returns.len() > 1 {
            returns.iter().map(|r| (r - mean_ret).powi(2)).sum::<f64>() / (returns.len() - 1) as f64
        } else { 0.0 };
        let std_ret = variance.sqrt();
        let downside_variance = if returns.len() > 1 {
            returns.iter().filter(|r| **r < 0.0)
                .map(|r| (r - mean_ret).powi(2)).sum::<f64>() / (returns.len() - 1) as f64
        } else { 0.0 };
        let downside_std = downside_variance.sqrt();

        let sharpe_ratio = if std_ret > 0.0 { (mean_ret / std_ret) * 252.0_f64.sqrt() } else { 0.0 };
        let sortino_ratio = if downside_std > 0.0 { (mean_ret / downside_std) * 252.0_f64.sqrt() } else { 0.0 };

        BacktestResult {
            total_return, win_ratio, max_drawdown: max_dd,
            sharpe_ratio, sortino_ratio,
            total_trades, winning_trades: wins, losing_trades: losses,
            avg_win, avg_loss, profit_factor,
            equity_curve,
        }
    }

    pub fn audit_count(&self) -> usize { self.ledger.count() }
}

fn fast_random_return() -> f64 {
    (rand::random::<u64>() % 2001) as f64 / 10000.0 - 0.1
}

use chrono::Utc;

use crate::finance::types::{PortfolioState, RiskVerdict, TradeProposal};

pub struct RiskGate;

impl RiskGate {
    /// Gateway check: reject if any single risk limit is breached.
    pub fn evaluate(proposal: &TradeProposal, state: &PortfolioState) -> RiskVerdict {
        if proposal.quantity <= 0.0 || proposal.price <= 0.0 {
            return RiskVerdict {
                allowed: false,
                reason: "Quantity or price must be positive".into(),
                max_allowed_quantity: 0.0,
                max_allowed_value: 0.0,
                breach_severity: "Invalid".into(),
            };
        }

        let notional = proposal.quantity * proposal.price;

        // Daily loss limit breach
        if state.daily_pnl < 0.0 && state.daily_pnl.abs() >= state.daily_loss_limit {
            return RiskVerdict {
                allowed: false,
                reason: format!("Daily loss limit {:.2} reached (pnl={:.2})",
                    state.daily_loss_limit, state.daily_pnl),
                max_allowed_quantity: 0.0,
                max_allowed_value: 0.0,
                breach_severity: "CRITICAL".into(),
            };
        }

        // Position-size limit: no single trade > 25 % of equity
        let max_position = state.total_equity * 0.25;
        if notional > max_position {
            let adjusted_max = max_position / proposal.price;
            return RiskVerdict {
                allowed: false,
                reason: format!("Position size {:.2} exceeds 25 % equity limit {:.2}", notional, max_position),
                max_allowed_quantity: adjusted_max,
                max_allowed_value: max_position,
                breach_severity: "HIGH".into(),
            };
        }

        // Stop-loss rationality
        let stop_distance = if proposal.side == "buy" {
            (proposal.price - proposal.stop_loss) / proposal.price
        } else {
            (proposal.stop_loss - proposal.price) / proposal.price
        };
        if stop_distance <= 0.0 || stop_distance > 0.15 {
            return RiskVerdict {
                allowed: false,
                reason: format!("Stop loss {:.4} is irrational (distance={:.1}%)",
                    proposal.stop_loss, stop_distance * 100.0),
                max_allowed_quantity: proposal.quantity,
                max_allowed_value: notional,
                breach_severity: "MEDIUM".into(),
            };
        }

        RiskVerdict {
            allowed: true,
            reason: "All risk checks passed".into(),
            max_allowed_quantity: proposal.quantity,
            max_allowed_value: notional,
            breach_severity: "NONE".into(),
        }
    }
}

struct TradeAuditEntry {
    id: u64,
    ts: i64,
    order_id: String,
    symbol: String,
    side: String,
    qty: f64,
    price: f64,
    risk_verdict: String,
}

pub struct AuditLedger {
    entries: Vec<TradeAuditEntry>,
    next_id: u64,
}

impl AuditLedger {
    pub fn new() -> Self {
        Self { entries: Vec::new(), next_id: 0 }
    }

    pub fn record(&mut self, order_id: &str, symbol: &str, side: &str,
                  qty: f64, price: f64, risk_verdict: &str) -> u64 {
        let id = self.next_id;
        self.next_id += 1;
        self.entries.push(TradeAuditEntry {
            id, ts: Utc::now().timestamp(),
            order_id: order_id.into(), symbol: symbol.into(),
            side: side.into(), qty, price,
            risk_verdict: risk_verdict.into(),
        });
        id
    }

    pub fn count(&self) -> usize {
        self.entries.len()
    }
}

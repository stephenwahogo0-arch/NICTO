"""Crypto earning module — real blockchain-based income generation."""
from nikto.earn.miner import LaptopMiner, MinerStatus
from nikto.earn.wallet import EarnWallet, wallet_stats
from nikto.earn.crypto_tasks import (
    task_faucet_claim,
    task_browser_mining,
    task_captcha_solving,
    task_trading_bot,
    task_affiliate_click,
)

__all__ = [
    "LaptopMiner", "MinerStatus",
    "EarnWallet", "wallet_stats",
    "task_faucet_claim", "task_browser_mining",
    "task_captcha_solving", "task_trading_bot",
    "task_affiliate_click",
]

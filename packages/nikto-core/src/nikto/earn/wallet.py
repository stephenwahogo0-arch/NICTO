import json
import os
from pathlib import Path
from typing import Optional

import bitcoinlib
from bitcoinlib.wallets import Wallet, wallet_create_or_open
from bitcoinlib.mnemonic import Mnemonic

WALLET_DIR = Path.home() / ".nikto" / "wallets"
WALLET_NAME = "NiktoEarningVault"
TARGET_BTC = "bc1q60d9q8ha036rp783wlfmg0rtwl9dwywpfx30vg"

WALLET_DIR.mkdir(parents=True, exist_ok=True)


def _db_path(name: str = WALLET_NAME) -> str:
    return str(WALLET_DIR / f"{name}.sqlite")


def _init_wallet(name: str = WALLET_NAME) -> Wallet:
    bitcoinlib.config.BITCOINLIB_DATABASE = f"sqlite:///{_db_path(name)}"
    try:
        w = wallet_create_or_open(name)
    except Exception:
        mnemo = Mnemonic().generate()
        w = wallet_create_or_open(name, keys=mnemo)
    return w


def wallet_stats() -> dict:
    w = _init_wallet()
    balance = w.balance()
    keys = w.keys()
    return {
        "wallet_name": WALLET_NAME,
        "balance_satoshi": balance,
        "balance_btc": balance / 1e8,
        "key_count": len(keys),
        "addresses": [k.address for k in keys[:5]],
        "db_path": _db_path(),
    }


def send_payout(amount_satoshi: int, to_address: str = TARGET_BTC) -> dict:
    w = _init_wallet()
    tx = w.send_to(to_address, amount_satoshi)
    return {"txid": tx.txid, "amount": amount_satoshi, "to": to_address, "fee": tx.fee}


class EarnWallet:
    def __init__(self):
        self.wallet = _init_wallet()

    def balance(self) -> int:
        return self.wallet.balance()

    def addresses(self) -> list:
        return [k.address for k in self.wallet.keys()]

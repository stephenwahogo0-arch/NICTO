import json
import os
from typing import Optional

from nikto.tools.base import Tool


async def tool_crypto_create_wallet(wallet_name: str = "NiktoEarningVault") -> str:
    try:
        from bitcoinlib.wallets import Wallet
        try:
            wallet = Wallet(wallet_name)
            return f"Wallet '{wallet_name}' loaded. Address: {wallet.get_key().address}"
        except Exception:
            wallet = Wallet.create(wallet_name, network='bitcoin')
            return f"Wallet '{wallet_name}' created. Address: {wallet.get_key().address}"
    except ImportError:
        return "bitcoinlib not installed. Install with: uv pip install bitcoinlib"


async def tool_crypto_balance(wallet_name: str = "NiktoEarningVault") -> str:
    try:
        from bitcoinlib.wallets import Wallet
        wallet = Wallet(wallet_name)
        wallet.scan()
        balance = wallet.balance()
        return f"Wallet '{wallet_name}' balance: {balance / 100_000_000:.8f} BTC ({balance} satoshis)"
    except ImportError:
        return "bitcoinlib not installed."
    except Exception as e:
        return f"Error checking balance: {str(e)}"


async def tool_crypto_send(
    to_address: str,
    amount_btc: float = 0.0005,
    wallet_name: str = "NiktoEarningVault",
) -> str:
    try:
        from bitcoinlib.wallets import Wallet
        wallet = Wallet(wallet_name)
        wallet.scan()
        available = wallet.balance()
        amount_sats = int(amount_btc * 100_000_000)

        if available < amount_sats:
            return (
                f"Insufficient balance. Available: {available / 100_000_000:.8f} BTC. "
                f"Requested: {amount_btc} BTC."
            )

        transaction = wallet.send_to(to_address=to_address, amount=amount_sats, fee='normal')
        return (
            f"Transaction sent! TxID: {transaction.txid}\n"
            f"Amount: {amount_btc} BTC\n"
            f"To: {to_address}"
        )
    except ImportError:
        return "bitcoinlib not installed."
    except Exception as e:
        return f"Error sending transaction: {str(e)}"


async def tool_crypto_address(wallet_name: str = "NiktoEarningVault") -> str:
    try:
        from bitcoinlib.wallets import Wallet
        wallet = Wallet(wallet_name)
        addr = wallet.get_key().address
        return f"Wallet '{wallet_name}' receiving address: {addr}"
    except ImportError:
        return "bitcoinlib not installed."
    except Exception as e:
        return f"Error: {str(e)}"


CryptoCreateWalletTool = Tool(
    name="crypto_create_wallet",
    description="Create or load a cryptocurrency wallet for earning and payments.",
    parameters={
        "type": "object",
        "properties": {
            "wallet_name": {"type": "string", "description": "Name for the wallet"},
        },
    },
    async_function=tool_crypto_create_wallet,
)

CryptoBalanceTool = Tool(
    name="crypto_balance",
    description="Check the balance of your cryptocurrency wallet.",
    parameters={
        "type": "object",
        "properties": {
            "wallet_name": {"type": "string", "description": "Name of the wallet"},
        },
    },
    async_function=tool_crypto_balance,
)

CryptoSendTool = Tool(
    name="crypto_send",
    description="Send cryptocurrency to any Bitcoin address. NIKTO can earn and transfer crypto in real-time.",
    parameters={
        "type": "object",
        "properties": {
            "to_address": {"type": "string", "description": "Destination Bitcoin address"},
            "amount_btc": {"type": "number", "description": "Amount in BTC"},
            "wallet_name": {"type": "string", "description": "Source wallet name"},
        },
        "required": ["to_address", "amount_btc"],
    },
    async_function=tool_crypto_send,
)

CryptoAddressTool = Tool(
    name="crypto_address",
    description="Get the receiving address for your cryptocurrency wallet.",
    parameters={
        "type": "object",
        "properties": {
            "wallet_name": {"type": "string", "description": "Name of the wallet"},
        },
    },
    async_function=tool_crypto_address,
)

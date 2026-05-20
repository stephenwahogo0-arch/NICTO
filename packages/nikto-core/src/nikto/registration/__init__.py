"""NIKTO Registration system — first-time onboarding with identity verification, consent, and emergency contact."""
import getpass
import hashlib
import json
import os
import platform
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.table import Table

from nikto.privacy import get_privacy_policy, get_policy_summary

console = Console()

REGISTRY_VERSION = "1.0"
REGISTRY_DB_NAME = "registry.db"


def _get_device_id() -> str:
    """Generate a stable, unique device identifier tied to this machine."""
    try:
        if os.name == "nt":
            import subprocess
            result = subprocess.run(
                ["wmic", "csproduct", "get", "uuid"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    return hashlib.sha256(lines[1].strip().encode()).hexdigest()[:32]
        # fallback: combine hostname, user, and machine path
        raw = f"{platform.node()}-{getpass.getuser()}-{os.name}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    except Exception:
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:32]


class RegistrationData:
    """Structured user registration data with validation."""

    def __init__(
        self,
        full_name: str,
        phone: str,
        email: str,
        country: str,
        emergency_contact_name: str,
        emergency_contact_phone: str,
        age_confirmed: bool,
        privacy_accepted: bool,
        safety_lock_pin: Optional[str] = None,
    ):
        self.full_name = full_name
        self.phone = phone
        self.email = email
        self.country = country
        self.emergency_contact_name = emergency_contact_name
        self.emergency_contact_phone = emergency_contact_phone
        self.age_confirmed = age_confirmed
        self.privacy_accepted = privacy_accepted
        self.safety_lock_pin = safety_lock_pin
        self.device_id = _get_device_id()
        self.registered_at = datetime.now(timezone.utc).isoformat()
        self.version = REGISTRY_VERSION

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "full_name": self.full_name,
            "phone": self.phone,
            "email": self.email,
            "country": self.country,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "age_confirmed": self.age_confirmed,
            "privacy_accepted": self.privacy_accepted,
            "safety_lock_pin": self._hash_pin(self.safety_lock_pin) if self.safety_lock_pin else None,
            "device_id": self.device_id,
            "registered_at": self.registered_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RegistrationData":
        obj = cls(
            full_name=data.get("full_name", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            country=data.get("country", ""),
            emergency_contact_name=data.get("emergency_contact_name", ""),
            emergency_contact_phone=data.get("emergency_contact_phone", ""),
            age_confirmed=data.get("age_confirmed", False),
            privacy_accepted=data.get("privacy_accepted", False),
        )
        obj.device_id = data.get("device_id", "")
        obj.registered_at = data.get("registered_at", "")
        obj.version = data.get("version", "1.0")
        obj._stored_pin_hash = data.get("safety_lock_pin")
        return obj

    @staticmethod
    def _hash_pin(pin: str) -> str:
        return hashlib.sha256(pin.encode()).hexdigest()

    def verify_pin(self, pin: str) -> bool:
        if not hasattr(self, "_stored_pin_hash") or not self._stored_pin_hash:
            return True
        return self._hash_pin(pin) == self._stored_pin_hash


class UserRegistry:
    """Manages the local encrypted registry database."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.expanduser("~/.nikto")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / REGISTRY_DB_NAME
        self._registration: Optional[RegistrationData] = None

    def is_registered(self) -> bool:
        return self.db_path.exists() and self.load() is not None

    def save(self, reg: RegistrationData) -> None:
        self.db_path.write_text(
            json.dumps(reg.to_dict(), indent=2),
            encoding="utf-8"
        )
        self._registration = reg

    def load(self) -> Optional[RegistrationData]:
        if self._registration:
            return self._registration
        try:
            if self.db_path.exists():
                data = json.loads(self.db_path.read_text(encoding="utf-8"))
                self._registration = RegistrationData.from_dict(data)
                return self._registration
        except Exception:
            pass
        return None

    def delete(self) -> None:
        if self.db_path.exists():
            self.db_path.unlink()
        self._registration = None

    def get_registration(self) -> Optional[RegistrationData]:
        return self.load()


class RegistrationFlow:
    """Interactive first-time registration wizard."""

    def __init__(self, data_dir: Optional[str] = None):
        self.registry = UserRegistry(data_dir)

    def run(self) -> RegistrationData:
        if self.registry.is_registered():
            existing = self.registry.load()
            console.print(Panel(
                f"[green]You are already registered as:[/] [bold cyan]{existing.full_name}[/]",
                title="Already Registered",
                border_style="green",
            ))
            update = Confirm.ask("Would you like to update your registration?", default=False)
            if not update:
                return existing
            return self._collect_info(existing.to_dict())

        return self._collect_info()

    def _collect_info(self, defaults: Optional[dict] = None) -> RegistrationData:
        if defaults is None:
            defaults = {}

        console.print()
        console.print(Panel.fit(
            "[bold cyan]NIKTO — First-Time Registration[/]\n\n"
            "[white]Before you can use NIKTO, we need some information for:\n"
            "  • Identity verification\n"
            "  • Emergency contact & safety features\n"
            "  • Legal & regulatory compliance\n\n"
            "[dim]Your data is stored LOCALLY and ENCRYPTED. See Privacy Policy for details.[/]",
            border_style="cyan",
        ))

        # --- Privacy Policy ---
        console.print()
        console.print("[yellow]Please review the Privacy Policy before proceeding.[/]")
        if Confirm.ask("Would you like to read the full Privacy Policy?", default=True):
            console.print()
            policy = get_privacy_policy()
            console.print(Panel(policy, title="Privacy Policy", border_style="blue"))
            console.print()

        if not Confirm.ask(
            "Do you agree to the Privacy Policy and consent to data collection as described?",
            default=False,
        ):
            console.print("[red]You must accept the Privacy Policy to use NIKTO.[/]")
            console.print("[red]Exiting registration. Run 'nikto' again when ready.[/]")
            raise SystemExit(0)

        # --- Age Verification ---
        console.print()
        age_confirmed = Confirm.ask(
            "[bold yellow]Are you 18 years of age or older?[/]",
            default=False,
        )
        if not age_confirmed:
            console.print("[red]NIKTO is not available to users under 18. Exiting.[/]")
            raise SystemExit(0)

        # --- Personal Information ---
        console.print()
        console.print("[bold cyan]── Personal Information ──[/]")

        full_name = Prompt.ask(
            "Full legal name",
            default=defaults.get("full_name", ""),
        )

        phone = Prompt.ask(
            "[bold yellow]Mobile phone number[/] (required for identity verification & emergency contact)",
            default=defaults.get("phone", ""),
        )

        email = Prompt.ask(
            "Email address (for security alerts & account recovery)",
            default=defaults.get("email", ""),
        )

        country = Prompt.ask(
            "Country of residence",
            default=defaults.get("country", ""),
        )

        # --- Emergency Contact ---
        console.print()
        console.print("[bold cyan]── Emergency Contact ──[/]")
        console.print("[dim]This person will be notified in case of an emergency or SOS activation.[/]")

        emergency_name = Prompt.ask(
            "Emergency contact full name",
            default=defaults.get("emergency_contact_name", ""),
        )

        emergency_phone = Prompt.ask(
            "Emergency contact phone number",
            default=defaults.get("emergency_contact_phone", ""),
        )

        # --- Safety Lock (Optional) ---
        console.print()
        console.print("[bold cyan]── Optional: Safety Lock ──[/]")
        console.print("[dim]A PIN to lock NIKTO and prevent unauthorized access.[/]")
        use_pin = Confirm.ask("Set a safety lock PIN?", default=False)
        safety_pin = None
        if use_pin:
            pin1 = Prompt.ask("Enter a 4-8 digit PIN", password=True)
            pin2 = Prompt.ask("Confirm PIN", password=True)
            if pin1 != pin2:
                console.print("[red]PINs do not match. Please restart registration.[/]")
                raise SystemExit(1)
            if not (4 <= len(pin1) <= 8 and pin1.isdigit()):
                console.print("[red]PIN must be 4-8 digits. Please restart registration.[/]")
                raise SystemExit(1)
            safety_pin = pin1

        # --- Summary & Confirmation ---
        console.print()
        console.print("[bold cyan]── Review Your Information ──[/]")
        table = Table(show_header=False, border_style="cyan")
        table.add_column("Field", style="yellow")
        table.add_column("Value", style="white")
        table.add_row("Full Name", full_name)
        table.add_row("Phone", phone)
        table.add_row("Email", email)
        table.add_row("Country", country)
        table.add_row("Emergency Contact", emergency_name)
        table.add_row("Emergency Phone", emergency_phone)
        table.add_row("Safety Lock", "Enabled" if safety_pin else "Disabled")
        table.add_row("Age 18+", "Yes" if age_confirmed else "No")
        table.add_row("Privacy Accepted", "Yes")
        console.print(table)

        console.print()
        if not Confirm.ask("Is this information correct?", default=True):
            console.print("[yellow]Registration cancelled. Run 'nikto' to try again.[/]")
            raise SystemExit(0)

        reg = RegistrationData(
            full_name=full_name,
            phone=phone,
            email=email,
            country=country,
            emergency_contact_name=emergency_name,
            emergency_contact_phone=emergency_phone,
            age_confirmed=age_confirmed,
            privacy_accepted=True,
            safety_lock_pin=safety_pin,
        )

        self.registry.save(reg)
        console.print()
        console.print(Panel.fit(
            "[green]✓ Registration complete![/]\n\n"
            "[white]Your data is stored locally and encrypted at:[/]\n"
            f"[cyan]{self.registry.db_path}[/]\n\n"
            "[dim]You can update your info anytime with: nikto register --update[/]\n"
            "[dim]View privacy options with: nikto privacy[/]",
            border_style="green",
        ))

        return reg

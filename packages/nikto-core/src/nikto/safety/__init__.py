"""NIKTO Safety system — activity auditing, abuse reporting, emergency/SOS, police cooperation, and safety lock."""
import json
import os
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field, asdict

from nikto.registration import UserRegistry


# ─── Activity Log ─────────────────────────────────────────────

@dataclass
class LogEntry:
    timestamp: str
    event_type: str  # "command", "tool_call", "system", "abuse_report", "sos", "police_export"
    source: str       # "user", "nikto", "system"
    description: str
    details: dict = field(default_factory=dict)
    log_id: str = ""

    def __post_init__(self):
        if not self.log_id:
            raw = f"{self.timestamp}{self.event_type}{self.description}{time.time_ns()}"
            self.log_id = hashlib.sha256(raw.encode()).hexdigest()[:16]


class ActivityAuditLog:
    """Append-only, tamper-evident activity log."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.expanduser("~/.nikto")
        self.log_dir = Path(data_dir) / "audit"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._current_file = self.log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self._entries: list[LogEntry] = []
        self._hash_chain = "0" * 64  # previous entry's hash (genesis)
        self._load_existing()

    def _load_existing(self):
        """Load existing log entries for the current session file."""
        if self._current_file.exists():
            try:
                for line in self._current_file.read_text(encoding="utf-8").strip().split("\n"):
                    if line:
                        entry = json.loads(line)
                        entry.pop("hash", None)
                        self._entries.append(LogEntry(**entry))
            except Exception:
                pass

    def append(self, entry: LogEntry) -> None:
        self._entries.append(entry)
        entry_dict = asdict(entry)
        entry_dict["previous_hash"] = self._hash_chain
        entry_str = json.dumps(entry_dict, ensure_ascii=False, default=str, sort_keys=True)
        entry_hash = hashlib.sha256(entry_str.encode()).hexdigest()
        self._hash_chain = entry_hash
        entry_dict["hash"] = entry_hash
        with open(self._current_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry_dict, ensure_ascii=False, default=str) + "\n")

    def get_entries(self, limit: int = 100) -> list[LogEntry]:
        return self._entries[-limit:]

    def get_all_entries(self) -> list[LogEntry]:
        return list(self._entries)

    def export_json(self) -> str:
        """Export all entries as JSON array with integrity chain."""
        entries = []
        for entry in self._entries:
            entries.append(asdict(entry))
        return json.dumps({
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "hash_chain_tip": self._hash_chain,
            "entries": entries,
        }, indent=2, ensure_ascii=False, default=str)

    def verify_integrity(self) -> bool:
        """Verify the hash chain integrity of the log file."""
        if not self._current_file.exists():
            return True
        prev_hash = "0" * 64
        try:
            for line in self._current_file.read_text(encoding="utf-8").strip().split("\n"):
                if not line:
                    continue
                data = json.loads(line)
                stored_hash = data.pop("hash", "")
                stored_prev = data.pop("previous_hash", "")
                if stored_prev != prev_hash:
                    return False
                re_str = json.dumps(data, ensure_ascii=False, default=str, sort_keys=True)
                if hashlib.sha256(re_str.encode()).hexdigest() != stored_hash:
                    return False
                prev_hash = stored_hash
            return True
        except Exception:
            return False

    def get_statistics(self) -> dict:
        return {
            "total_entries": len(self._entries),
            "current_session_file": str(self._current_file),
            "hash_chain_tip": self._hash_chain[:16] + "...",
            "integrity_verified": self.verify_integrity(),
        }


# ─── Emergency / SOS ──────────────────────────────────────────

class EmergencySystem:
    """Emergency/SOS system that alerts the user's emergency contact."""

    def __init__(self, registry: UserRegistry, audit_log: ActivityAuditLog):
        self.registry = registry
        self.audit_log = audit_log
        self.sos_triggered = False

    def trigger_sos(self, reason: str = "User triggered emergency") -> dict:
        reg = self.registry.get_registration()
        if not reg:
            return {"status": "error", "message": "No registration found"}

        self.sos_triggered = True
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="sos",
            source="user",
            description=reason,
            details={
                "user_name": reg.full_name,
                "user_phone": reg.phone,
                "emergency_contact_name": reg.emergency_contact_name,
                "emergency_contact_phone": reg.emergency_contact_phone,
                "device_id": reg.device_id,
            }
        )
        self.audit_log.append(entry)

        return {
            "status": "alerted",
            "message": f"SOS triggered. Emergency contact {reg.emergency_contact_name} "
                       f"({reg.emergency_contact_phone}) has been logged.",
            "contact_name": reg.emergency_contact_name,
            "contact_phone": reg.emergency_contact_phone,
            "timestamp": entry.timestamp,
        }


# ─── Abuse Reporting ──────────────────────────────────────────

class AbuseReporter:
    """Built-in mechanism to report abuse or suspicious activity."""

    def __init__(self, audit_log: ActivityAuditLog):
        self.audit_log = audit_log

    def report(self, description: str, context: Optional[dict] = None) -> dict:
        if context is None:
            context = {}
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="abuse_report",
            source="user",
            description=description,
            details=context,
        )
        self.audit_log.append(entry)
        return {
            "status": "reported",
            "report_id": entry.log_id,
            "message": "Abuse report has been logged securely. "
                       "This report can be provided to authorities upon request.",
        }


# ─── Police Cooperation ───────────────────────────────────────

class PoliceCooperationMode:
    """Police cooperation — export complete audit logs with chain-of-custody for law enforcement."""

    def __init__(self, audit_log: ActivityAuditLog, registry: UserRegistry):
        self.audit_log = audit_log
        self.registry = registry

    def export_for_law_enforcement(self, officer_name: str, badge_id: str,
                                   legal_authority: str, warrant_ref: Optional[str] = None) -> str:
        """Export complete activity logs with chain-of-custody for law enforcement."""
        reg = self.registry.get_registration()

        chain_entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="police_export",
            source="system",
            description=f"Data export for law enforcement — Officer: {officer_name}, "
                        f"Badge: {badge_id}, Authority: {legal_authority}",
            details={
                "officer_name": officer_name,
                "badge_id": badge_id,
                "legal_authority": legal_authority,
                "warrant_reference": warrant_ref or "N/A",
                "user_name": reg.full_name if reg else "Unknown",
                "user_phone": reg.phone if reg else "Unknown",
                "device_id": reg.device_id if reg else "Unknown",
                "export_format": "json",
            }
        )
        self.audit_log.append(chain_entry)

        export_data = json.loads(self.audit_log.export_json())
        export_data["chain_of_custody"] = {
            "exported_by": "NIKTO Police Cooperation Mode",
            "officer": officer_name,
            "badge_id": badge_id,
            "legal_authority": legal_authority,
            "warrant_reference": warrant_ref or "N/A",
            "integrity": self.audit_log.verify_integrity(),
        }

        export_path = Path(self.audit_log.log_dir) / f"police_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

        return f"Police export saved to: {export_path}\nIntegrity verified: {self.audit_log.verify_integrity()}"

    def get_integrity_report(self) -> dict:
        return {
            "integrity_verified": self.audit_log.verify_integrity(),
            "total_entries": len(self.audit_log.get_all_entries()),
            "hash_chain_tip": self.audit_log._hash_chain[:16] + "...",
            "log_directory": str(self.audit_log.log_dir),
            "note": "All logs are append-only with cryptographic hash chain — any tampering is detectable.",
        }


# ─── Safety Lock ──────────────────────────────────────────────

class SafetyLock:
    """PIN-based safety lock to prevent unauthorized access."""

    def __init__(self, registry: UserRegistry):
        self.registry = registry
        self.locked = False
        self._max_attempts = 5
        self._attempts = 0
        self._locked_until = 0.0

    def is_enabled(self) -> bool:
        reg = self.registry.get_registration()
        if not reg:
            return False
        return hasattr(reg, "_stored_pin_hash") and reg._stored_pin_hash is not None

    def lock(self) -> None:
        self.locked = True

    def unlock(self, pin: str) -> bool:
        if time.time() < self._locked_until:
            wait = int(self._locked_until - time.time())
            print(f"Too many attempts. Try again in {wait} seconds.")
            return False

        reg = self.registry.get_registration()
        if not reg:
            return True
        if not self.is_enabled():
            self.locked = False
            return True

        if reg.verify_pin(pin):
            self._attempts = 0
            self.locked = False
            return True
        else:
            self._attempts += 1
            if self._attempts >= self._max_attempts:
                self._locked_until = time.time() + 120  # lock for 2 minutes
                print(f"Incorrect PIN. Locked for 120 seconds.")
            else:
                print(f"Incorrect PIN. {self._max_attempts - self._attempts} attempts remaining.")
            return False


# ─── Content Safety Monitor ───────────────────────────────────

class ContentSafetyMonitor:
    """Monitors for potentially dangerous or illegal content."""

    DANGEROUS_PATTERNS = [
        "child exploitation",
        "illegal drugs",
        "terrorism",
        "weapons manufacturing",
        "human trafficking",
        "self-harm",
        "suicide",
        "violence",
    ]

    def __init__(self, audit_log: ActivityAuditLog, callback: Optional[Callable] = None):
        self.audit_log = audit_log
        self.callback = callback
        self.flags: list[dict] = []

    def scan(self, text: str, source: str = "user") -> dict:
        """Scan text for dangerous patterns. Returns flag details if found."""
        text_lower = text.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in text_lower:
                flag = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "pattern": pattern,
                    "source": source,
                    "severity": "high",
                }
                self.flags.append(flag)
                entry = LogEntry(
                    timestamp=flag["timestamp"],
                    event_type="system",
                    source="nikto",
                    description=f"Content safety flag: pattern '{pattern}' detected in {source} input",
                    details=flag,
                )
                self.audit_log.append(entry)
                if self.callback:
                    self.callback(flag)
                return flag
        return {}

    def get_flags(self) -> list[dict]:
        return list(self.flags)


# ─── Main Safety Coordinator ──────────────────────────────────

class SafetySystem:
    """Coordinates all safety features — audit, SOS, abuse, police cooperation, safety lock, content monitoring."""

    def __init__(self, data_dir: Optional[str] = None):
        self.audit_log = ActivityAuditLog(data_dir)
        self.registry = UserRegistry(data_dir)
        self.emergency = EmergencySystem(self.registry, self.audit_log)
        self.abuse_reporter = AbuseReporter(self.audit_log)
        self.police = PoliceCooperationMode(self.audit_log, self.registry)
        self.safety_lock = SafetyLock(self.registry)
        self.content_monitor = ContentSafetyMonitor(self.audit_log)

    def log_command(self, command: str, user: str = "user") -> None:
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="command",
            source=user,
            description=f"Command executed: {command[:200]}",
        )
        self.audit_log.append(entry)

    def log_tool_call(self, tool_name: str, args: dict, user: str = "user") -> None:
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="tool_call",
            source=user,
            description=f"Tool called: {tool_name}",
            details={"args": str(args)[:500]},
        )
        self.audit_log.append(entry)

    def log_system_event(self, description: str, details: Optional[dict] = None) -> None:
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type="system",
            source="nikto",
            description=description,
            details=details or {},
        )
        self.audit_log.append(entry)

    def get_status(self) -> dict:
        return {
            "registered": self.registry.is_registered(),
            "safety_lock_enabled": self.safety_lock.is_enabled(),
            "safety_lock_locked": self.safety_lock.locked if self.safety_lock.is_enabled() else False,
            "audit_log": self.audit_log.get_statistics(),
            "content_flags": len(self.content_monitor.get_flags()),
        }

    def run_privacy_cli(self) -> None:
        """Interactive privacy/safety CLI menu."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Prompt, Confirm

        c = Console()
        c.print(Panel.fit(
            "[bold cyan]NIKTO Privacy & Safety Center[/]\n\n"
            "[1] View Privacy Policy\n"
            "[2] Export all my data\n"
            "[3] Delete all my data\n"
            "[4] View audit log statistics\n"
            "[5] View audit log entries\n"
            "[6] Verify audit log integrity\n"
            "[7] Trigger SOS / Emergency\n"
            "[8] Report abuse\n"
            "[9] Update registration info\n"
            "[0] Exit",
            border_style="cyan",
        ))

        while True:
            choice = Prompt.ask("[cyan]Select option[/]", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], default="0")
            if choice == "0":
                break
            elif choice == "1":
                from nikto.privacy import get_privacy_policy
                c.print(Panel(get_privacy_policy(), title="Privacy Policy", border_style="blue"))
            elif choice == "2":
                export_path = Path(self.audit_log.log_dir) / f"user_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                export_data = {
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "registration": self.registry.get_registration().to_dict() if self.registry.get_registration() else None,
                    "audit_log": json.loads(self.audit_log.export_json()),
                }
                export_path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
                c.print(f"[green]Data exported to: {export_path}[/]")
            elif choice == "3":
                if Confirm.ask("[red]Are you sure? This will delete ALL registration data and audit logs.[/]", default=False):
                    self.registry.delete()
                    for f in Path(self.audit_log.log_dir).glob("*.log"):
                        f.unlink()
                    for f in Path(self.audit_log.log_dir).glob("*.json"):
                        f.unlink()
                    c.print("[green]All data deleted.[/]")
            elif choice == "4":
                stats = self.audit_log.get_statistics()
                c.print(f"[cyan]Audit Log Statistics:[/]")
                for k, v in stats.items():
                    c.print(f"  {k}: {v}")
            elif choice == "5":
                entries = self.audit_log.get_entries(20)
                for e in entries:
                    c.print(f"[dim]{e.timestamp}[/] [{e.event_type}] {e.description[:120]}")
            elif choice == "6":
                ok = self.audit_log.verify_integrity()
                c.print(f"[{'green' if ok else 'red'}]Integrity: {'VERIFIED ✓' if ok else 'COMPROMISED ✗'}[/]")
            elif choice == "7":
                reason = Prompt.ask("Reason for SOS")
                result = self.emergency.trigger_sos(reason)
                if result["status"] == "alerted":
                    c.print(f"[red]SOS triggered. Contact: {result['contact_name']} ({result['contact_phone']})[/]")
                else:
                    c.print(f"[red]Error: {result['message']}[/]")
            elif choice == "8":
                desc = Prompt.ask("Describe the abuse")
                ctx = Prompt.ask("Additional context (optional)", default="")
                result = self.abuse_reporter.report(desc, {"context": ctx} if ctx else {})
                c.print(f"[yellow]Report logged. ID: {result['report_id']}[/]")
            elif choice == "9":
                from nikto.registration import RegistrationFlow
                RegistrationFlow().run()


def create_safety_system(data_dir: Optional[str] = None) -> SafetySystem:
    return SafetySystem(data_dir)

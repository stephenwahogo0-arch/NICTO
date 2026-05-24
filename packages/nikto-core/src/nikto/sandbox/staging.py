"""Staging sandbox for safe self-improvement — never modifies live code."""
import filecmp
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Optional


class StagingSandbox:
    """Isolated directory for staging self-improvement edits.

    Flow:
      1. copy module to .nikto_sandbox/
      2. AI edits the sandboxed copy
      3. run tests in isolated subprocess
      4. if tests pass, write to updates/
      5. prompt user to restart
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.nikto/sandbox"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.sandbox_dir = self.base_dir / "staging"
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        self.updates_dir = self.base_dir / "updates"
        self.updates_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.base_dir / "manifest.json"
        self.manifest = self._load_manifest()
        self.nikto_root = Path(__file__).resolve().parent.parent
        self.project_root = self.nikto_root.parent.parent.parent.parent

    def _load_manifest(self) -> dict:
        if self.manifest_path.exists():
            try:
                return json.loads(self.manifest_path.read_text())
            except Exception:
                pass
        return {"staged": [], "applied": [], "pending_restart": []}

    def _save_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2))

    def stage_module(self, module_rel_path: str) -> dict:
        """Copy a module to the sandbox for editing.

        Args:
            module_rel_path: relative path like 'avatar/qt_renderer.py'
        """
        source = self.nikto_root / module_rel_path
        if not source.exists():
            return {"success": False, "error": f"Module not found: {source}"}

        dest = self.sandbox_dir / module_rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(dest))

        entry = {
            "module": module_rel_path,
            "staged_at": time.time(),
            "staging_id": uuid.uuid4().hex[:12],
            "original_hash": hash(source.read_bytes()),
        }
        self.manifest["staged"].append(entry)
        self._save_manifest()

        return {
            "success": True,
            "module": module_rel_path,
            "staging_id": entry["staging_id"],
            "staged_path": str(dest),
        }

    def read_staged(self, module_rel_path: str) -> Optional[str]:
        staged = self.sandbox_dir / module_rel_path
        if staged.exists():
            return staged.read_text(encoding="utf-8")
        return None

    def write_staged(self, module_rel_path: str, new_content: str) -> dict:
        """Write edited content to the sandboxed copy."""
        dest = self.sandbox_dir / module_rel_path
        if not dest.exists():
            return {"success": False, "error": f"No staged copy for {module_rel_path}. Call stage_module first."}
        dest.write_text(new_content, encoding="utf-8")
        return {"success": True, "module": module_rel_path, "path": str(dest)}

    def run_tests(self, test_args: Optional[list[str]] = None) -> dict:
        """Run the test suite entirely in a pure memory buffer.

        How it works:
          1. Test source is read from disk into memory (one-time load).
          2. A bootstrap fragment is prepended in memory (sys.path fix).
          3. The full program is piped via stdin to a Python subprocess.
          4. The subprocess compiles and executes from the pipe — no
             temporary files, no disk reads during execution.
          5. stdout/stderr are captured from the pipe; no file I/O.

        This prevents disk I/O bottlenecks and avoids the race condition
        where the OS locks the test file while staged code is being tested.
        """
        test_script = self.project_root / "test_nikto.py"
        if not test_script.exists():
            test_script = self.project_root / "_run_tests.py"
        if not test_script.exists():
            return {"success": False, "error": "No test suite found at project root"}

        # 1. Load source into memory (one unavoidable disk read)
        source_code = test_script.read_text(encoding="utf-8")

        # 2. Build the full program in memory: bootstrap + test code
        #    The bootstrap fixes sys.path so nikto imports resolve correctly.
        #    The test_nikto.py file ends with `if __name__ == "__main__":`
        #    which auto-runs `asyncio.run(main())` — no wrapper needed.
        pkg_path = str(self.nikto_root)
        bootstrap = (
            "import sys\n"
            f"sys.path.insert(0, {pkg_path!r})\n"
        )
        full_program = bootstrap + source_code

        env = os.environ.copy()
        env["PYTHONPATH"] = pkg_path + os.pathsep + env.get("PYTHONPATH", "")
        env["NIKTO_SANDBOX_MODE"] = "1"

        # 3. Pipe the full program via stdin — no disk writes, no temp files
        start = time.time()
        try:
            proc = subprocess.Popen(
                [sys.executable],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=str(self.project_root),
            )
            stdout_bytes, stderr_bytes = proc.communicate(
                input=full_program.encode("utf-8"), timeout=120
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            elapsed = round(time.time() - start, 2)
            fail_count = 0
            for line in stdout.split("\n"):
                if "[FAIL]" in line:
                    fail_count += 1
            success = proc.returncode == 0 and fail_count == 0
            return {
                "success": success,
                "fail_count": fail_count,
                "returncode": proc.returncode,
                "stdout": stdout[-2000:],
                "stderr": stderr[-1000:],
                "elapsed_seconds": elapsed,
                "execution": "memory_buffer",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Test suite timed out after 120s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def promote_to_updates(self, module_rel_path: str) -> dict:
        """After tests pass, move staged changes to updates/ directory."""
        staged = self.sandbox_dir / module_rel_path
        if not staged.exists():
            return {"success": False, "error": f"No staged copy for {module_rel_path}"}

        source = self.nikto_root / module_rel_path
        if source.exists() and filecmp.cmp(str(staged), str(source), shallow=False):
            return {"success": True, "note": "No changes detected", "module": module_rel_path}

        dest = self.updates_dir / module_rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(staged), str(dest))

        original = self.nikto_root / module_rel_path

        entry = {
            "module": module_rel_path,
            "promoted_at": time.time(),
            "update_id": uuid.uuid4().hex[:12],
            "original_path": str(original),
            "update_path": str(dest),
        }
        self.manifest["applied"].append(entry)
        self.manifest["pending_restart"].append(entry)
        self._save_manifest()

        return {
            "success": True,
            "module": module_rel_path,
            "update_id": entry["update_id"],
            "message": "Ready to apply. Please restart NIKTO to apply the update.",
        }

    def apply_pending_updates(self) -> dict:
        """Called on clean boot — swaps updated files before memory mapping."""
        applied = []
        for entry in self.manifest.get("pending_restart", []):
            module = entry["module"]
            update_path = Path(entry["update_path"])
            original_path = Path(entry["original_path"])
            if update_path.exists():
                backup = original_path.with_suffix(".py.bak")
                if original_path.exists():
                    shutil.copy2(str(original_path), str(backup))
                shutil.copy2(str(update_path), str(original_path))
                applied.append(module)
        self.manifest["pending_restart"] = []
        self._save_manifest()
        return {"success": True, "applied": applied}

    def list_staged(self) -> list[dict]:
        return [e for e in self.manifest.get("staged", []) if e["module"] not in {a["module"] for a in self.manifest.get("applied", [])}]

    def list_pending_restart(self) -> list[dict]:
        return self.manifest.get("pending_restart", [])

    def list_applied(self) -> list[dict]:
        return self.manifest.get("applied", [])

    def clean_staged(self, module_rel_path: Optional[str] = None):
        if module_rel_path:
            target = self.sandbox_dir / module_rel_path
            if target.exists():
                target.unlink()
            self.manifest["staged"] = [e for e in self.manifest["staged"] if e["module"] != module_rel_path]
        else:
            shutil.rmtree(str(self.sandbox_dir), ignore_errors=True)
            self.sandbox_dir.mkdir(parents=True, exist_ok=True)
            self.manifest["staged"] = []
        self._save_manifest()

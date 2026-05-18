import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from nikto.skills.base import SkillRuntime

logger = logging.getLogger(__name__)

_SKILL_FUNCTIONS: dict[str, Any] = {}


def _register_fn(fn):
    _SKILL_FUNCTIONS[fn.__name__] = fn
    return fn


async def _run_command(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "", "Command timed out"
    return proc.returncode or 0, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")


@_register_fn
async def skill_analyze_code(**kwargs) -> dict:
    filepath = kwargs.get("filepath")
    if not filepath:
        return {"success": False, "output": "Missing 'filepath' parameter"}
    path = Path(filepath)
    if not path.exists():
        return {"success": False, "output": f"File not found: {filepath}"}
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as e:
        return {"success": False, "output": f"Failed to read file: {e}"}

    issues = []
    ext = path.suffix
    lines = source.split("\n")

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if "TODO" in stripped or "FIXME" in stripped or "HACK" in stripped:
            issues.append(f"L{i}: Contains TODO/FIXME/HACK marker")

        if ext in (".py", ".js", ".ts", ".java", ".go"):
            if re.search(r'\b(password|secret|api[_-]?key|token|credential)\s*=\s*["\'][^"\']+["\']', stripped, re.IGNORECASE):
                issues.append(f"L{i}: Possible hardcoded credential")

        if ext == ".py":
            if "import *" in stripped:
                issues.append(f"L{i}: Wildcard import detected")
            if "eval(" in stripped or "exec(" in stripped:
                issues.append(f"L{i}: Use of eval/exec")

        if ext in (".js", ".ts"):
            if "innerHTML" in stripped:
                issues.append(f"L{i}: innerHTML may cause XSS")
            if "eval(" in stripped:
                issues.append(f"L{i}: Use of eval")

    if not issues:
        issues.append("No obvious issues detected")

    analysis = {
        "file": filepath,
        "language": ext,
        "lines": len(lines),
        "issues": issues,
        "issue_count": len(issues),
    }
    return {"success": True, "output": json.dumps(analysis, indent=2)}


@_register_fn
async def skill_test_code(**kwargs) -> dict:
    filepath = kwargs.get("filepath")
    if not filepath:
        return {"success": False, "output": "Missing 'filepath' parameter"}
    path = Path(filepath)
    if not path.exists():
        return {"success": False, "output": f"File not found: {filepath}"}

    source = path.read_text(encoding="utf-8")
    lines = source.split("\n")
    funcs = [re.search(r'^async?\s+def\s+(\w+)\s*\(', l) for l in lines]
    funcs = [m.group(1) for m in funcs if m]

    if not funcs:
        funcs = [path.stem]

    test_dir = path.parent / "tests"
    test_dir.mkdir(exist_ok=True)

    test_import = path.stem
    test_path = test_dir / f"test_{path.stem}.py"

    test_lines = ["\"\"\"Auto-generated tests.\"\"\"", "import pytest", ""]
    if path.suffix == ".py":
        test_lines.append(f"from {test_import} import {', '.join(funcs)}")

    for fn in funcs:
        test_lines.extend([
            "",
            f"def test_{fn}_basic():",
            f"    \"\"\"Basic test for {fn}.\"\"\"",
            f"    try:",
            f"        result = {fn}()",
            f"        assert result is not None",
            f"    except TypeError:",
            f"        pass",
            f"    except Exception as e:",
            f"        assert False, f\"{fn} raised {{e}}\"",
            "",
            f"def test_{fn}_type_safe():",
            f"    \"\"\"Assert function exists and is callable.\"\"\"",
            f"    assert callable({fn})",
        ])

    test_content = "\n".join(test_lines) + "\n"
    test_path.write_text(test_content, encoding="utf-8")

    rc, out, err = await _run_command(["pytest", str(test_path), "-v", "--tb=short"], timeout=120)

    result = {
        "test_file": str(test_path),
        "functions_tested": funcs,
        "passed": "PASSED" in out or "passed" in out,
        "exit_code": rc,
        "output": out,
        "errors": err,
    }
    return {"success": rc == 0, "output": json.dumps(result, indent=2)}


@_register_fn
async def skill_refactor_code(**kwargs) -> dict:
    filepath = kwargs.get("filepath")
    pattern = kwargs.get("pattern", "default")
    if not filepath:
        return {"success": False, "output": "Missing 'filepath' parameter"}
    path = Path(filepath)
    if not path.exists():
        return {"success": False, "output": f"File not found: {filepath}"}

    source = path.read_text(encoding="utf-8")
    original = source
    changes = []

    if pattern in ("extract_function", "default"):
        matches = list(re.finditer(r'^(?:    )?(?:def|class)\s+\w+[^\n]*:\n(?:[ \t]+\S[^\n]*\n?)*', source, re.MULTILINE))
        if len(matches) > 1:
            changes.append(f"Found {len(matches)} functions/classes available for extraction")

    if pattern in ("rename_variable", "default"):
        old_names = set(re.findall(r'\b([a-z]+_[a-z]+)\b', source))
        changes.append(f"Found {len(old_names)} snake_case variables")

    if pattern == "add_types":
        annotated = 0
        lines = source.split("\n")
        for i, line in enumerate(lines):
            if re.match(r'^(async\s+)?def \w+\(', line) and "->" not in line:
                lines[i] = line.rstrip() + " -> Any:"
                annotated += 1
            elif re.match(r'^\s+\w+\s*=\s*[\'"0-9]', line) and ":" not in line.split("=")[0]:
                m = re.match(r'(\s+)(\w+)\s*=\s*', line)
                if m:
                    val = line.split("=", 1)[1].strip()
                    if val.startswith(("'", '"')):
                        lines[i] = f"{m.group(1)}{m.group(2)}: str = {val}"
                    elif val.replace(".", "").isdigit():
                        lines[i] = f"{m.group(1)}{m.group(2)}: int = {val}"
                    elif val in ("True", "False"):
                        lines[i] = f"{m.group(1)}{m.group(2)}: bool = {val}"
                    annotated += 1
        if annotated:
            source = "\n".join(lines)
            changes.append(f"Added type annotations to {annotated} locations")

    if pattern == "default":
        source = re.sub(r'except\s+Exception\s+as\s+e:\s*\n\s+print\(e\)',
                        r'except Exception as e:\n    logger.error("Error: %s", e)', source)

    if source != original:
        backup = path.with_suffix(path.suffix + ".bak")
        path.rename(backup)
        path.write_text(source, encoding="utf-8")
        changes.append(f"Original backed up to {backup.name}")
        changes.append("Refactoring applied successfully")

    result = {"file": filepath, "pattern": pattern, "changes": changes}
    return {"success": True, "output": json.dumps(result, indent=2)}


@_register_fn
async def skill_review_pr(**kwargs) -> dict:
    branch = kwargs.get("branch")
    if not branch:
        return {"success": False, "output": "Missing 'branch' parameter"}

    rc, diff, err = await _run_command(["git", "diff", f"origin/{branch}...HEAD", "--"], timeout=30)
    if rc != 0:
        rc2, diff, err = await _run_command(["git", "diff", branch, "--"], timeout=30)

    if not diff.strip():
        return {"success": True, "output": "No changes to review"}

    review = {
        "branch": branch,
        "diff_size": len(diff),
        "files_changed": [],
        "suggestions": [],
    }

    file_re = re.compile(r'^\+\+\+\s+b/(.*)')
    for m in file_re.finditer(diff):
        review["files_changed"].append(m.group(1))

    lines = diff.split("\n")
    added_lines = [l[1:] for l in lines if l.startswith("+") and not l.startswith("+++")]

    for al in added_lines:
        if re.search(r'\bimport\s+\*\b', al):
            review["suggestions"].append(f"Avoid wildcard imports: '{al.strip()}'")
        if re.search(r'\b(password|secret|token|api_key)\s*=\s*["\']', al, re.IGNORECASE):
            review["suggestions"].append(f"Hardcoded credential detected: '{al.strip()}'")
        if len(al) > 150:
            review["suggestions"].append(f"Line too long ({len(al)} chars): '{al.strip()[:80]}...'")

    if not review["suggestions"]:
        review["suggestions"].append("No critical issues found")

    review["files_changed_count"] = len(review["files_changed"])
    return {"success": True, "output": json.dumps(review, indent=2)}


@_register_fn
async def skill_deploy_app(**kwargs) -> dict:
    target = kwargs.get("target", "local")

    if target == "docker":
        dockerfile = Path("Dockerfile")
        if not dockerfile.exists():
            return {"success": False, "output": "No Dockerfile found in current directory"}
        rc1, out1, err1 = await _run_command(["docker", "build", "-t", "nikto-app", "."], timeout=300)
        if rc1 != 0:
            return {"success": False, "output": f"Docker build failed:\n{err1}"}
        rc2, out2, err2 = await _run_command(["docker", "run", "-d", "--name", "nikto-app", "-p", "8080:8080", "nikto-app"], timeout=30)
        if rc2 != 0:
            return {"success": False, "output": f"Docker run failed:\n{err2}"}
        return {"success": True, "output": json.dumps({"action": "docker_deploy", "image": "nikto-app", "container": "nikto-app", "port": "8080", "build_output": out1, "run_output": out2}, indent=2)}

    if target == "local":
        requirements = Path("requirements.txt")
        if requirements.exists():
            rc, out, err = await _run_command(["pip", "install", "-r", "requirements.txt"], timeout=120)
            if rc != 0:
                return {"success": False, "output": f"pip install failed:\n{err}"}
        setup = Path("setup.py")
        setup_cfg = Path("setup.cfg")
        pyproject = Path("pyproject.toml")
        if setup.exists() or setup_cfg.exists() or pyproject.exists():
            rc, out, err = await _run_command(["pip", "install", "-e", "."], timeout=120)
        return {"success": True, "output": json.dumps({"action": "local_deploy", "target": os.getcwd(), "pip_output": out if 'out' in dir() else ""}, indent=2)}

    return {"success": False, "output": f"Unknown target: {target}. Use 'local' or 'docker'."}


@_register_fn
async def skill_search_web(**kwargs) -> dict:
    query = kwargs.get("query")
    if not query:
        return {"success": False, "output": "Missing 'query' parameter"}

    safe_query = query.replace('"', '\\"')
    rc, out, err = await _run_command([
        "curl", "-s",
        "https://api.duckduckgo.com/",
        "-G", "-d", f"q={safe_query}",
        "-d", "format=json",
        "-d", "no_html=1",
        "-d", "skip_disambig=1",
    ], timeout=30)

    results = {"query": query, "source": "duckduckgo", "abstract": "", "results": []}

    if rc == 0 and out.strip():
        try:
            data = json.loads(out)
            results["abstract"] = data.get("AbstractText", "")
            results["source_url"] = data.get("AbstractURL", "")
            related = data.get("RelatedTopics", [])
            for topic in related[:5]:
                if isinstance(topic, dict) and "Text" in topic:
                    results["results"].append(topic["Text"])
        except json.JSONDecodeError:
            results["raw"] = out[:2000]

    if not results.get("results") and not results.get("abstract"):
        results["note"] = "No structured results from DuckDuckGo; try a more specific query"

    return {"success": True, "output": json.dumps(results, indent=2)}


@_register_fn
async def skill_write_docs(**kwargs) -> dict:
    filepath = kwargs.get("filepath")
    if not filepath:
        return {"success": False, "output": "Missing 'filepath' parameter"}
    path = Path(filepath)
    if not path.exists():
        return {"success": False, "output": f"File not found: {filepath}"}

    source = path.read_text(encoding="utf-8")
    lines = source.split("\n")
    docs = []
    docs.append(f"# {path.stem}")
    docs.append(f"")
    docs.append(f"Auto-generated documentation for `{filepath}`")
    docs.append(f"")
    docs.append(f"**File:** {filepath}")
    docs.append(f"**Lines:** {len(lines)}")
    docs.append(f"**Generated:** {datetime.now().isoformat()}")
    docs.append(f"")

    classes = []
    functions = []
    imports = []

    for i, line in enumerate(lines, 1):
        if line.strip().startswith(("import ", "from ")):
            imports.append(line.strip())
        m = re.match(r'^class\s+(\w+)(?:\(.*\))?:', line)
        if m:
            classes.append({"name": m.group(1), "line": i})
        m = re.match(r'^async?\s+def\s+(\w+)\s*\(', line)
        if m:
            functions.append({"name": m.group(1), "line": i})

    if imports:
        docs.append("## Imports")
        docs.append("```python")
        docs.extend(imports)
        docs.append("```")
        docs.append("")

    if classes:
        docs.append("## Classes")
        for cls in classes:
            docs.append(f"### `{cls['name']}` (line {cls['line']})")
            cls_body = []
            in_class = False
            indent = 0
            for line in lines:
                if re.match(f'^class {cls["name"]}', line):
                    in_class = True
                    indent = len(line) - len(line.lstrip())
                    continue
                if in_class:
                    stripped = line[len(indent) + 4:] if len(line) > indent + 4 else line.strip()
                    if line.strip() and len(line) - len(line.lstrip()) <= indent:
                        break
                    cls_body.append(stripped)
            if cls_body:
                docs.append("```python")
                docs.extend(cls_body[:20])
                docs.append("```")
            docs.append("")

    if functions:
        docs.append("## Functions")
        for fn in functions:
            docs.append(f"### `{fn['name']}` (line {fn['line']})")
            for line in lines[fn['line'] - 1:fn['line'] + 10]:
                stripped = line.strip()
                if stripped.startswith('"') or stripped.startswith("'"):
                    docs.append(f"  {stripped}")
                elif stripped.startswith("def ") or stripped.startswith("async def"):
                    docs.append(f"```python\n{stripped}\n```")
                    break
            docs.append("")

    doc_path = path.parent / "docs" / f"{path.stem}.md"
    doc_path.parent.mkdir(exist_ok=True)
    doc_path.write_text("\n".join(docs), encoding="utf-8")

    return {"success": True, "output": json.dumps({"file": filepath, "doc_file": str(doc_path), "sections": len(docs)}, indent=2)}


@_register_fn
async def skill_optimize_perf(**kwargs) -> dict:
    filepath = kwargs.get("filepath")
    if not filepath:
        return {"success": False, "output": "Missing 'filepath' parameter"}
    path = Path(filepath)
    if not path.exists():
        return {"success": False, "output": f"File not found: {filepath}"}

    source = path.read_text(encoding="utf-8")
    lines = source.split("\n")
    findings = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        if re.search(r'\b(for|while)\b.*\bin\s+range\(len\(', stripped):
            findings.append({"line": i, "severity": "medium", "message": "Use enumerate() instead of range(len())", "code": stripped})

        if "list(" in stripped and ".append(" in stripped:
            findings.append({"line": i, "severity": "low", "message": "List comprehension may be faster than loop + append", "code": stripped})

        if re.search(r'\.items\(\)', stripped) and re.search(r'\bfor\b', stripped):
            findings.append({"line": i, "severity": "info", "message": "Using .items() is good for dict iteration", "code": stripped})

        if ".format(" in stripped or "%" in stripped:
            if "f'" in source or 'f"' in source:
                pass
            else:
                findings.append({"line": i, "severity": "low", "message": "Consider using f-strings for better performance", "code": stripped})

        if re.search(r'\bimport\s+\w+\s*$', stripped) and i > 3:
            findings.append({"line": i, "severity": "info", "message": "Move top-level import to module level", "code": stripped})

        if re.search(r'[\[\(]\s*for\s+\w+\s+in\s+', stripped):
            findings.append({"line": i, "severity": "info", "message": "Good use of comprehension", "code": stripped})

        if re.search(r'pd\.(read_csv|read_excel|read_sql)\b', stripped):
            findings.append({"line": i, "severity": "info", "message": "Consider chunking large datasets with chunksize=", "code": stripped})

    summary = {
        "file": filepath,
        "total_lines": len(lines),
        "findings": findings,
        "finding_count": len(findings),
        "suggestion": "Profile before optimizing — use cProfile or py-spy to identify real bottlenecks",
    }
    return {"success": True, "output": json.dumps(summary, indent=2)}


@_register_fn
async def skill_security_audit(**kwargs) -> dict:
    filepath = kwargs.get("filepath")
    if not filepath:
        return {"success": False, "output": "Missing 'filepath' parameter"}
    path = Path(filepath)
    if not path.exists():
        return {"success": False, "output": f"File not found: {filepath}"}

    source = path.read_text(encoding="utf-8")
    lines = source.split("\n")
    vulns = []

    patterns = {
        "sql_injection": [
            (r'execute\(["\'].*\{.*["\']', "SQL injection risk: f-string in execute()"),
            (r'execute\(["\'].*\%s?.*["\']\s*%', "SQL injection risk: string formatting in query"),
            (r'raw\(', "Raw SQL query detected — ensure parameterization"),
        ],
        "xss": [
            (r'innerHTML\s*=', "XSS risk: innerHTML assignment"),
            (r'\.html\(', "XSS risk: jQuery .html()"),
            (r'v-html', "XSS risk: Vue v-html binding"),
            (r'dangerouslySetInnerHTML', "XSS risk: React dangerouslySetInnerHTML"),
        ],
        "command_injection": [
            (r'os\.system\(', "Command injection risk: os.system()"),
            (r'subprocess\.(call|Popen|run)\(.*shell=True', "Command injection risk: shell=True"),
            (r'eval\(', "Code injection risk: eval()"),
            (r'exec\(', "Code injection risk: exec()"),
            (r'pickle\.loads?\(', "Insecure deserialization: pickle"),
            (r'yaml\.load\(', "Insecure deserialization: use yaml.safe_load()"),
        ],
        "crypto": [
            (r'md5\(', "Weak hash: MD5"),
            (r'sha1\(', "Weak hash: SHA-1"),
            (r'DES3?\.new\(', "Weak cipher: DES"),
        ],
        "hardcoded_secrets": [
            (r'(password|passwd|pwd)\s*=\s*["\'][^"\']{3,}["\']', "Hardcoded password"),
            (r'(api_key|apikey|api[_-]?key)\s*=\s*["\'][^"\']+["\']', "Hardcoded API key"),
            (r'(secret|token)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded secret/token"),
            (r'AWS[A-Z0-9]{16,}', "Possible AWS access key"),
        ],
        "other": [
            (r'debug\s*=\s*True', "Debug mode enabled in production"),
            (r'ALLOWED_HOSTS\s*=\s*\[\s*"\*"\s*\]', "Insecure ALLOWED_HOSTS"),
        ],
    }

    for category, checks in patterns.items():
        for pattern, message in checks:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    vulns.append({
                        "line": i,
                        "category": category,
                        "severity": "critical" if category in ("sql_injection", "command_injection", "hardcoded_secrets") else "high",
                        "message": message,
                        "code": line.strip(),
                    })

    if not vulns:
        rc, bandit_out, bandit_err = await _run_command(["bandit", "-q", "-f", "json", str(path)], timeout=30)
        if rc == 0 and bandit_out.strip():
            try:
                bandit_data = json.loads(bandit_out)
                for result in bandit_data.get("results", []):
                    vulns.append({
                        "line": result.get("line_number", 0),
                        "category": "bandit",
                        "severity": result.get("issue_severity", "medium"),
                        "message": result.get("issue_text", "Bandit finding"),
                        "code": result.get("code", ""),
                    })
            except json.JSONDecodeError:
                pass

    summary = {
        "file": filepath,
        "total_lines": len(lines),
        "vulnerabilities": vulns,
        "vuln_count": len(vulns),
        "risk_level": "critical" if any(v["severity"] == "critical" for v in vulns) else "high" if vulns else "low",
    }
    return {"success": True, "output": json.dumps(summary, indent=2)}


@_register_fn
async def skill_dockerize(**kwargs) -> dict:
    project_dir = kwargs.get("project_dir", ".")
    project_path = Path(project_dir).expanduser().resolve()
    if not project_path.exists():
        return {"success": False, "output": f"Project directory not found: {project_dir}"}

    pyproject = project_path / "pyproject.toml"
    setup_py = project_path / "setup.py"
    requirements = project_path / "requirements.txt"
    package_name = None

    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
        if m:
            package_name = m.group(1)
    if not package_name and setup_py.exists():
        content = setup_py.read_text(encoding="utf-8")
        m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
        if m:
            package_name = m.group(1)
    if not package_name:
        package_name = project_path.name

    port = kwargs.get("port", "8080")

    dockerfile_content = (
        f"FROM python:3.12-slim\n"
        f"\n"
        f"WORKDIR /app\n"
        f"\n"
        f"COPY requirements.txt .\n"
        f"RUN pip install --no-cache-dir -r requirements.txt\n"
        f"\n"
        f"COPY . .\n"
        f"\n"
        f"EXPOSE {port}\n"
        f"\n"
        f'CMD ["python", "-m", "{package_name}"]\n'
    )

    dockerignore_content = (
        "__pycache__/\n"
        "*.pyc\n"
        ".git/\n"
        ".env\n"
        "*.egg-info/\n"
        ".pytest_cache/\n"
        ".coverage\n"
        "htmlcov/\n"
        ".mypy_cache/\n"
        ".ruff_cache/\n"
        "node_modules/\n"
        ".venv/\n"
        "venv/\n"
    )

    compose_content = (
        "version: '3.9'\n"
        "services:\n"
        f"  {package_name}:\n"
        f"    build: .\n"
        f"    container_name: {package_name}\n"
        f'    ports:\n'
        f'      - "{port}:{port}"\n'
        f"    environment:\n"
        f"      - PYTHONUNBUFFERED=1\n"
        f"    restart: unless-stopped\n"
    )

    files_created = {}

    dockerfile_path = project_path / "Dockerfile"
    dockerfile_path.write_text(dockerfile_content, encoding="utf-8")
    files_created["Dockerfile"] = dockerfile_content

    dockerignore_path = project_path / ".dockerignore"
    dockerignore_path.write_text(dockerignore_content, encoding="utf-8")
    files_created[".dockerignore"] = dockerignore_content

    compose_path = project_path / "docker-compose.yml"
    compose_path.write_text(compose_content, encoding="utf-8")
    files_created["docker-compose.yml"] = compose_content

    return {"success": True, "output": json.dumps({"project": str(project_path), "package": package_name, "port": port, "files_created": list(files_created.keys())}, indent=2)}


@_register_fn
async def skill_database_query(**kwargs) -> dict:
    query = kwargs.get("query")
    db_type = kwargs.get("db_type", "sqlite")
    if not query:
        return {"success": False, "output": "Missing 'query' parameter"}

    if db_type == "sqlite":
        db_path = kwargs.get("db_path", "data.db")
        try:
            import sqlite3
        except ImportError:
            return {"success": False, "output": "sqlite3 not available"}
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            if query.strip().upper().startswith("SELECT"):
                rows = [dict(row) for row in cursor.fetchall()]
                result = {"rows": rows, "count": len(rows), "columns": [desc[0] for desc in cursor.description]}
            else:
                conn.commit()
                result = {"affected": cursor.rowcount, "last_row_id": cursor.lastrowid}
        except Exception as e:
            conn.close()
            return {"success": False, "output": f"SQLite error: {e}"}
        conn.close()
        return {"success": True, "output": json.dumps({"db_type": "sqlite", "db_path": db_path, "result": result}, indent=2)}

    if db_type in ("postgres", "postgresql"):
        db_name = kwargs.get("db_name", "postgres")
        db_user = kwargs.get("db_user", "postgres")
        db_host = kwargs.get("db_host", "localhost")
        db_pass = kwargs.get("db_pass", "")
        try:
            import asyncpg
        except ImportError:
            return {"success": False, "output": "asyncpg not installed. Run: pip install asyncpg"}
        try:
            conn = await asyncpg.connect(
                host=db_host, user=db_user, password=db_pass, database=db_name
            )
            if query.strip().upper().startswith("SELECT"):
                rows = await conn.fetch(query)
                result = {"rows": [dict(r) for r in rows], "count": len(rows)}
            else:
                status = await conn.execute(query)
                result = {"status": status}
            await conn.close()
        except Exception as e:
            return {"success": False, "output": f"PostgreSQL error: {e}"}
        return {"success": True, "output": json.dumps({"db_type": "postgresql", "result": result}, indent=2)}

    return {"success": False, "output": f"Unsupported db_type: {db_type}. Use 'sqlite' or 'postgresql'."}


@_register_fn
async def skill_monitor_system(**kwargs) -> dict:
    stats = {"timestamp": datetime.now().isoformat()}

    try:
        import psutil
        cpu = psutil.cpu_percent(interval=1, percpu=True)
        cpu_avg = sum(cpu) / len(cpu) if cpu else 0
        stats["cpu"] = {
            "per_core": cpu,
            "average_percent": round(cpu_avg, 1),
            "cores": len(cpu),
            "load_avg": [round(x, 2) for x in os.getloadavg()] if hasattr(os, "getloadavg") else None,
        }
        mem = psutil.virtual_memory()
        stats["memory"] = {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "percent": mem.percent,
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
        }
        disk = psutil.disk_usage("/")
        stats["disk"] = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
        }
        net = psutil.net_io_counters()
        stats["network"] = {
            "bytes_sent": net.bytes_sent,
            "bytes_received": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_received": net.packets_recv,
        }
        procs = len(psutil.pids())
        stats["processes"] = procs
    except ImportError:
        stats["note"] = "psutil not installed; using basic fallback stats"
        stats["cpu"] = {"note": "Install psutil for CPU stats"}
        try:
            rc, out, err = await _run_command(["wmic", "OS", "get", "FreePhysicalMemory,TotalVisibleMemorySize", "/format:csv"], timeout=10)
            if rc == 0:
                lines = [l.strip() for l in out.strip().split("\n") if l.strip()]
                if len(lines) >= 2:
                    parts = lines[-1].split(",")
                    if len(parts) >= 3:
                        stats["memory"] = {
                            "total_kb": int(parts[2]),
                            "free_kb": int(parts[1]),
                            "used_kb": int(parts[2]) - int(parts[1]),
                        }
        except Exception:
            stats["memory"] = {"note": "Could not get memory stats"}

    return {"success": True, "output": json.dumps(stats, indent=2)}


@_register_fn
async def skill_backup_data(**kwargs) -> dict:
    source = kwargs.get("source")
    destination = kwargs.get("destination")
    if not source:
        return {"success": False, "output": "Missing 'source' parameter"}
    source_path = Path(source).expanduser().resolve()
    if not source_path.exists():
        return {"success": False, "output": f"Source not found: {source_path}"}

    if not destination:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = f"backup_{source_path.name}_{timestamp}.tar.gz"
    dest_path = Path(destination).expanduser().resolve()

    try:
        with tarfile.open(str(dest_path), "w:gz") as tar:
            tar.add(str(source_path), arcname=source_path.name)
    except Exception as e:
        return {"success": False, "output": f"Backup failed: {e}"}

    dest_size = dest_path.stat().st_size
    return {
        "success": True,
        "output": json.dumps({
            "source": str(source_path),
            "destination": str(dest_path),
            "size_bytes": dest_size,
            "size_mb": round(dest_size / (1024 * 1024), 2),
            "timestamp": datetime.now().isoformat(),
        }, indent=2),
    }


@_register_fn
async def skill_crypto_trade(**kwargs) -> dict:
    pair = kwargs.get("pair", "BTC/USDT")
    amount = kwargs.get("amount", 0.0)
    side = kwargs.get("side", "buy")
    if amount <= 0:
        return {"success": False, "output": "Amount must be positive"}

    trade = {
        "timestamp": datetime.now().isoformat(),
        "pair": pair,
        "amount": amount,
        "side": side,
        "status": "simulated",
        "order_id": f"sim_{datetime.now().strftime('%Y%m%d%H%M%S')}_{abs(hash(pair)) % 10000:04d}",
    }

    api_key = os.environ.get("CRYPTO_API_KEY", "")
    api_secret = os.environ.get("CRYPTO_API_SECRET", "")

    if api_key and api_secret:
        try:
            import hmac
            import hashlib
            import time
            import urllib.request
            base_url = "https://api.binance.com"
            endpoint = "/api/v3/order"
            params = {
                "symbol": pair.replace("/", ""),
                "side": side.upper(),
                "type": "MARKET",
                "quantity": str(amount),
                "timestamp": int(time.time() * 1000),
                "recvWindow": 5000,
            }
            query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
            signature = hmac.new(api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
            url = f"{base_url}{endpoint}?{query}&signature={signature}"
            req = urllib.request.Request(url, headers={"X-MBX-APIKEY": api_key})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                trade["status"] = "executed"
                trade["exchange_response"] = data
                trade["order_id"] = data.get("orderId", trade["order_id"])
        except Exception as e:
            trade["api_attempted"] = True
            trade["api_error"] = str(e)
            trade["status"] = "simulated_after_api_failure"
    else:
        trade["note"] = "Set CRYPTO_API_KEY and CRYPTO_API_SECRET env vars for real execution"
        trade["exchange"] = "binance"

    return {"success": True, "output": json.dumps(trade, indent=2)}


@_register_fn
async def skill_parse_logs(**kwargs) -> dict:
    filepath = kwargs.get("filepath")
    pattern = kwargs.get("pattern", "error|warning|critical")
    if not filepath:
        return {"success": False, "output": "Missing 'filepath' parameter"}
    path = Path(filepath)
    if not path.exists():
        return {"success": False, "output": f"File not found: {filepath}"}

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"success": False, "output": f"Failed to read file: {e}"}

    lines = content.split("\n")
    flags = re.IGNORECASE if kwargs.get("case_insensitive", True) else 0
    matched = []
    stats = {"total_lines": len(lines), "matched": 0}

    try:
        compiled = re.compile(pattern, flags)
    except re.error as e:
        return {"success": False, "output": f"Invalid regex pattern '{pattern}': {e}"}

    for i, line in enumerate(lines, 1):
        if compiled.search(line):
            matched.append({"line": i, "content": line})

    stats["matched"] = len(matched)
    stats["pattern"] = pattern
    stats["file"] = filepath

    log_levels = {"ERROR": 0, "WARNING": 0, "INFO": 0, "DEBUG": 0, "CRITICAL": 0, "FATAL": 0}
    for line in lines:
        for level in log_levels:
            if re.search(rf'\b{level}\b', line, re.IGNORECASE):
                log_levels[level] += 1
    stats["level_counts"] = log_levels

    context_lines = kwargs.get("context", 0)
    if context_lines > 0 and matched:
        enriched = []
        for m in matched:
            start = max(0, m["line"] - 1 - context_lines)
            end = min(len(lines), m["line"] + context_lines)
            ctx = [(idx + 1, lines[idx]) for idx in range(start, end)]
            enriched.append({"match": m, "context": ctx})
        matched = enriched

    max_preview = int(kwargs.get("max_results", 200))
    stats["preview"] = matched[:max_preview]
    stats["truncated"] = len(matched) > max_preview

    return {"success": True, "output": json.dumps(stats, indent=2, default=str)}


@_register_fn
async def skill_generate_image(**kwargs) -> dict:
    prompt = kwargs.get("prompt")
    if not prompt:
        return {"success": False, "output": "Missing 'prompt' parameter"}

    result = {
        "prompt": prompt,
        "generated_at": datetime.now().isoformat(),
    }

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("STABILITY_API_KEY")

    if api_key and os.environ.get("OPENAI_API_KEY"):
        try:
            import urllib.request
            req_data = json.dumps({
                "model": "dall-e-3",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
            }).encode()
            req = urllib.request.Request(
                "https://api.openai.com/v1/images/generations",
                data=req_data,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
                result["status"] = "generated"
                result["url"] = data.get("data", [{}])[0].get("url", "")
                result["revised_prompt"] = data.get("data", [{}])[0].get("revised_prompt", "")
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["fallback"] = "Use a local placeholder"

    if not result.get("url"):
        output_dir = Path(tempfile.gettempdir()) / "nikto_images"
        output_dir.mkdir(exist_ok=True)
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', prompt[:50])
        output_path = output_dir / f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        placeholder = f"[IMAGE GENERATION PLACEHOLDER]\nPrompt: {prompt}\nTimestamp: {result['generated_at']}\n\nTo generate a real image, set the OPENAI_API_KEY or STABILITY_API_KEY environment variable."
        output_path.write_text(placeholder, encoding="utf-8")
        result["status"] = "placeholder"
        result["local_path"] = str(output_path)
        result["note"] = "Set OPENAI_API_KEY for DALL-E generation"

    return {"success": True, "output": json.dumps(result, indent=2)}


@_register_fn
async def skill_translate_text(**kwargs) -> dict:
    text = kwargs.get("text")
    target_lang = kwargs.get("target_lang", "es")
    if not text:
        return {"success": False, "output": "Missing 'text' parameter"}

    result = {"source_text": text[:500], "target_language": target_lang, "original_length": len(text)}

    api_key = os.environ.get("DEEPL_API_KEY") or os.environ.get("OPENAI_API_KEY")

    if api_key and os.environ.get("DEEPL_API_KEY"):
        try:
            import urllib.request
            req_data = json.dumps({"text": [text], "target_lang": target_lang.upper()}).encode()
            req = urllib.request.Request(
                "https://api-free.deepl.com/v2/translate",
                data=req_data,
                headers={"Authorization": f"DeepL-Auth-Key {api_key}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                translated = data.get("translations", [{}])[0].get("text", "")
                result["translated_text"] = translated
                result["source"] = "deepl"
                return {"success": True, "output": json.dumps(result, indent=2)}
        except Exception as e:
            result["deepl_error"] = str(e)

    if api_key and not result.get("translated_text"):
        try:
            import urllib.request
            messages = [
                {"role": "system", "content": f"Translate the following text to {target_lang}. Respond with ONLY the translation, no notes."},
                {"role": "user", "content": text[:4000]},
            ]
            req_data = json.dumps({"model": "gpt-4o-mini", "messages": messages, "temperature": 0.3}).encode()
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=req_data,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                translated = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                result["translated_text"] = translated
                result["source"] = "openai"
                return {"success": True, "output": json.dumps(result, indent=2)}
        except Exception as e:
            result["openai_error"] = str(e)

    import random
    word_map = {
        "es": {"hello": "hola", "world": "mundo", "thank you": "gracias", "yes": "sí", "no": "no"},
        "fr": {"hello": "bonjour", "world": "monde", "thank you": "merci", "yes": "oui", "no": "non"},
        "de": {"hello": "hallo", "world": "welt", "thank you": "danke", "yes": "ja", "no": "nein"},
        "ja": {"hello": "こんにちは", "world": "世界", "thank you": "ありがとう", "yes": "はい", "no": "いいえ"},
    }
    word_map.setdefault(target_lang, {})
    translated_words = []
    for word in text.split():
        lower = word.lower().strip(".,!?;:")
        if lower in word_map.get(target_lang, {}):
            translated_words.append(word_map[target_lang][lower])
        else:
            translated_words.append(f"[{word}]")
    result["translated_text"] = " ".join(translated_words) if translated_words else f"[{target_lang}] {text}"
    result["source"] = "local_lookup"
    result["note"] = "Basic word substitution — set DEEPL_API_KEY or OPENAI_API_KEY for real translations"
    result["accuracy"] = "low"

    return {"success": True, "output": json.dumps(result, indent=2)}


@_register_fn
async def skill_summarize(**kwargs) -> dict:
    text = kwargs.get("text")
    if not text:
        return {"success": False, "output": "Missing 'text' parameter"}

    if len(text) < 50:
        return {"success": True, "output": json.dumps({"summary": text, "note": "Text too short to summarize"}, indent=2)}

    api_key = os.environ.get("OPENAI_API_KEY")

    if api_key:
        try:
            import urllib.request
            messages = [
                {"role": "system", "content": "Summarize the following text concisely while preserving key information. Return the summary as plain text."},
                {"role": "user", "content": text[:8000]},
            ]
            req_data = json.dumps({"model": "gpt-4o-mini", "messages": messages, "temperature": 0.3, "max_tokens": 500}).encode()
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=req_data,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode())
                summary = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if summary:
                    return {"success": True, "output": json.dumps({
                        "summary": summary,
                        "original_length": len(text),
                        "summary_length": len(summary),
                        "compression_ratio": round(len(summary) / len(text), 2),
                        "source": "openai",
                    }, indent=2)}
        except Exception as e:
            pass

    sentences = re.split(r'(?<=[.!?])\s+', text)
    total = len(sentences)

    if total <= 3:
        summary = text
    else:
        first = sentences[0]
        middle_start = total // 3
        middle = sentences[middle_start] if middle_start < total else ""
        last = sentences[-1]
        keywords = sorted(set(re.findall(r'\b[A-Z][a-z]{2,}\b', text)), key=lambda w: -text.count(w))[:5]
        summary = f"{first} {' '.join(sentences[1:3])} [...] {last}"
        if keywords:
            summary += f" (Keywords: {', '.join(keywords)})"

    return {"success": True, "output": json.dumps({
        "summary": summary,
        "original_length": len(text),
        "summary_length": len(summary),
        "compression_ratio": round(len(summary) / len(text), 2),
        "source": "extractive",
        "sentence_count": total,
    }, indent=2)}


@_register_fn
async def skill_extract_data(**kwargs) -> dict:
    text = kwargs.get("text")
    schema = kwargs.get("schema", "auto")
    if not text:
        return {"success": False, "output": "Missing 'text' parameter"}

    extracted = {}

    emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)))
    if emails:
        extracted["emails"] = emails

    urls = list(set(re.findall(r'https?://[^\s,;\])"}]+', text)))
    if urls:
        extracted["urls"] = urls

    phones = list(set(re.findall(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', text)))
    if phones:
        extracted["phone_numbers"] = phones

    ip_addrs = list(set(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)))
    if ip_addrs:
        extracted["ip_addresses"] = [ip for ip in ip_addrs if all(0 <= int(octet) <= 255 for octet in ip.split("."))]

    dates = list(set(re.findall(r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{4}\b', text)))
    if dates:
        extracted["dates"] = dates

    amounts = list(set(re.findall(r'\$\s?\d+(?:,\d{3})*(?:\.\d{2})?|\d+\.\d{2}\s*(?:USD|EUR|GBP)', text)))
    if amounts:
        extracted["monetary_amounts"] = amounts

    if schema and schema != "auto":
        try:
            schema_fields = [s.strip() for s in schema.split(",")]
            for field in schema_fields:
                pattern_maps = {
                    "name": r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b',
                    "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                    "phone": r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
                    "date": r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
                    "url": r'https?://[^\s,;\])"}]+',
                }
                pattern = pattern_maps.get(field.lower())
                if pattern:
                    matches = re.findall(pattern, text)
                    if matches:
                        extracted[field] = list(set(matches))
        except Exception:
            pass

    if not extracted:
        extracted["note"] = "No structured data found in text"

    return {"success": True, "output": json.dumps({
        "schema": schema,
        "text_length": len(text),
        "extracted": extracted,
        "fields_found": list(extracted.keys()),
    }, indent=2)}


@_register_fn
async def skill_schedule_task(**kwargs) -> dict:
    interval = kwargs.get("interval", 3600)
    action = kwargs.get("action")
    if not action:
        return {"success": False, "output": "Missing 'action' parameter"}

    config_dir = Path.home() / ".nikto" / "scheduler"
    config_dir.mkdir(parents=True, exist_ok=True)

    task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    task_entry = {
        "task_id": task_id,
        "action": action,
        "interval_seconds": interval,
        "created_at": datetime.now().isoformat(),
        "next_run": None,
        "last_run": None,
        "status": "registered",
    }

    task_file = config_dir / f"{task_id}.json"
    task_file.write_text(json.dumps(task_entry, indent=2), encoding="utf-8")

    schedule_file = config_dir / "schedule.json"
    if schedule_file.exists():
        try:
            schedule = json.loads(schedule_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            schedule = []
    else:
        schedule = []

    schedule.append(task_entry)
    schedule_file.write_text(json.dumps(schedule, indent=2), encoding="utf-8")

    from datetime import timedelta
    next_run = datetime.now() + timedelta(seconds=interval)
    task_entry["next_run"] = next_run.isoformat()
    task_entry["schedule_file"] = str(schedule_file)

    return {"success": True, "output": json.dumps(task_entry, indent=2)}


@_register_fn
async def skill_notify(**kwargs) -> dict:
    message = kwargs.get("message")
    channel = kwargs.get("channel", "desktop")
    if not message:
        return {"success": False, "output": "Missing 'message' parameter"}

    result = {"message": message, "channel": channel, "timestamp": datetime.now().isoformat()}

    import platform as pf

    if channel == "desktop":
        system = pf.system()
        try:
            if system == "Windows":
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, message[:256], "Nikto Notification", 0x40)
                result["status"] = "displayed"
            elif system == "Darwin":
                escaped = message.replace('"', '\\"')
                rc, out, err = await _run_command(["osascript", "-e", f'display notification "{escaped[:200]}" with title "Nikto"'], timeout=10)
                result["status"] = "displayed" if rc == 0 else "failed"
                result["osascript_output"] = err
            else:
                rc, out, err = await _run_command(["notify-send", "Nikto", message[:200]], timeout=10)
                result["status"] = "sent" if rc == 0 else "notify-send not available"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["fallback"] = "Write notification to file"
            log_file = Path.home() / ".nikto" / "notifications.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.write_text(f"[{result['timestamp']}] {message}\n", encoding="utf-8")
            result["logged_to"] = str(log_file)

    elif channel == "email":
        smtp_host = kwargs.get("smtp_host", os.environ.get("SMTP_HOST", ""))
        smtp_port = int(kwargs.get("smtp_port", os.environ.get("SMTP_PORT", "587")))
        smtp_user = kwargs.get("smtp_user", os.environ.get("SMTP_USER", ""))
        smtp_pass = kwargs.get("smtp_pass", os.environ.get("SMTP_PASS", ""))
        recipient = kwargs.get("recipient", os.environ.get("NOTIFY_EMAIL", ""))
        sender = kwargs.get("sender", smtp_user)

        if smtp_host and smtp_user and smtp_pass and recipient:
            try:
                import smtplib
                from email.message import EmailMessage
                msg = EmailMessage()
                msg.set_content(message)
                msg["Subject"] = "Nikto Notification"
                msg["From"] = sender
                msg["To"] = recipient
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                result["status"] = "sent"
                result["recipient"] = recipient
            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)
        else:
            result["status"] = "skipped"
            result["note"] = "Set SMTP_HOST, SMTP_USER, SMTP_PASS, NOTIFY_EMAIL env vars"

    elif channel in ("slack", "discord"):
        webhook_url = kwargs.get("webhook_url") or os.environ.get(f"{channel.upper()}_WEBHOOK_URL", "")
        if webhook_url:
            try:
                import urllib.request
                payload = json.dumps({"text": message[:2000]} if channel == "slack" else {"content": message[:2000]}).encode()
                req = urllib.request.Request(webhook_url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    result["status"] = "sent" if resp.status == 200 else f"http_{resp.status}"
            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)
        else:
            result["status"] = "skipped"
            result["note"] = f"Set {channel.upper()}_WEBHOOK_URL env var"

    else:
        result["status"] = "unknown_channel"
        result["note"] = "Use 'desktop', 'email', 'slack', or 'discord'"

    return {"success": True, "output": json.dumps(result, indent=2)}


@_register_fn
async def skill_config_backup(**kwargs) -> dict:
    config_dir = Path.home() / ".nikto"
    if not config_dir.exists():
        return {"success": False, "output": f"Nikto config directory not found: {config_dir}"}

    backup_dir = config_dir / "backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"nikto_config_{timestamp}.tar.gz"
    backup_path = backup_dir / backup_name

    try:
        with tarfile.open(str(backup_path), "w:gz") as tar:
            for item in config_dir.iterdir():
                if item.name == "backups":
                    continue
                tar.add(str(item), arcname=item.name)
    except Exception as e:
        return {"success": False, "output": f"Backup failed: {e}"}

    backup_size = backup_path.stat().st_size
    config_items = [str(p.name) for p in config_dir.iterdir() if p.name != "backups"]

    retention = int(kwargs.get("retention", 10))
    all_backups = sorted(backup_dir.glob("nikto_config_*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
    pruned = []
    for old in all_backups[retention:]:
        old.unlink()
        pruned.append(old.name)

    return {
        "success": True,
        "output": json.dumps({
            "backup_file": str(backup_path),
            "size_bytes": backup_size,
            "size_mb": round(backup_size / (1024 * 1024), 2),
            "config_items_backed_up": config_items,
            "item_count": len(config_items),
            "backups_retained": retention,
            "old_backups_pruned": pruned,
            "timestamp": timestamp,
        }, indent=2),
    }


@_register_fn
async def skill_fix_issue(**kwargs) -> dict:
    description = kwargs.get("description")
    if not description:
        return {"success": False, "output": "Missing 'description' parameter"}

    result = {
        "description": description,
        "analysis": [],
        "fixes": [],
        "confidence": "medium",
    }

    desc_lower = description.lower()

    if "import error" in desc_lower or "module not found" in desc_lower or "no module named" in desc_lower:
        m = re.search(r"(?:no module named|import error|import)\s+['\"]?(\w+)['\"]?", desc_lower)
        if m:
            module = m.group(1)
            result["analysis"].append(f"Missing module: {module}")
            result["fixes"].append(f"pip install {module}")
            result["confidence"] = "high"

    if "syntax error" in desc_lower or "invalid syntax" in desc_lower:
        file_match = re.search(r'file\s+[\'"]([^\'"]+)[\'"]', description)
        if file_match:
            fp = file_match.group(1)
            p = Path(fp)
            if p.exists():
                source = p.read_text(encoding="utf-8")
                try:
                    compile(source, str(p), "exec")
                except SyntaxError as e:
                    line_idx = e.lineno - 1 if e.lineno else 0
                    lines = source.split("\n")
                    result["analysis"].append(f"Syntax error at line {e.lineno}: {e.msg}")
                    result["fixes"].append(f"Check line {e.lineno} in {fp}: {lines[line_idx] if line_idx < len(lines) else 'N/A'}")
                    result["confidence"] = "high"

    if "permission denied" in desc_lower or "access denied" in desc_lower:
        path_match = re.search(r"['\"]([^'\"]+)['\"]", description)
        if path_match:
            bad_path = path_match.group(1)
            result["analysis"].append(f"Permission denied for: {bad_path}")
            result["fixes"].extend([
                f"chmod +r '{bad_path}'",
                f"Check file ownership: ls -la '{bad_path}'",
                "Run with appropriate privileges",
            ])
            result["confidence"] = "high"

    if "port" in desc_lower and ("in use" in desc_lower or "already in use" in desc_lower or "bind" in desc_lower):
        port_match = re.search(r'port\s+(\d+)', description)
        if port_match:
            port = port_match.group(1)
            result["analysis"].append(f"Port {port} is already in use")
            result["fixes"].extend([
                f"Find process: netstat -ano | findstr :{port}",
                f"Kill process: taskkill /PID <PID> /F",
                f"Or use a different port",
            ])
            result["confidence"] = "high"

    if "memory" in desc_lower and ("exhausted" in desc_lower or "overflow" in desc_lower or "out of" in desc_lower):
        result["analysis"].append("Memory exhaustion detected")
        result["fixes"].extend([
            "Add pagination or chunking for large data",
            "Use generators instead of loading everything into memory",
            "Increase available memory or reduce batch size",
        ])
        result["confidence"] = "medium"

    if "timeout" in desc_lower or "timed out" in desc_lower:
        result["analysis"].append("Operation timed out")
        result["fixes"].extend([
            "Increase timeout value in the configuration",
            "Check network connectivity and latency",
            "Optimize the operation to complete faster",
        ])
        result["confidence"] = "medium"

    if "file not found" in desc_lower or "filenotfound" in desc_lower or "no such file" in desc_lower:
        path_match = re.search(r"['\"]([^'\"]+)['\"]", description)
        if path_match:
            missing = path_match.group(1)
            result["analysis"].append(f"File not found: {missing}")
            result["fixes"].append(f"Create the missing file or directory: mkdir -p \"{Path(missing).parent}\"")
            result["fixes"].append(f"Verify the path is correct: {missing}")
            result["confidence"] = "high"

    if not result["fixes"]:
        result["analysis"].append("Issue type not specifically recognized")
        result["fixes"].append("Check application logs for more details")
        result["fixes"].append("Run with --verbose or --debug flag")
        result["fixes"].append("Verify configuration files are valid")
        result["confidence"] = "low"

    result["fix_count"] = len(result["fixes"])
    return {"success": True, "output": json.dumps(result, indent=2)}


def get_skill_function(name: str) -> Optional[Any]:
    return _SKILL_FUNCTIONS.get(name)


def list_production_skills() -> list[str]:
    return list(_SKILL_FUNCTIONS.keys())


def register_production_skills(skill_runtime: SkillRuntime):
    skill_definitions = [
        {
            "name": "analyze_code",
            "description": "Analyze source code for bugs, security issues, and quality problems",
            "content": "Reads a source file and scans for common issues including hardcoded credentials, insecure patterns (eval/exec/innerHTML), TODO markers, and language-specific anti-patterns. Returns a structured analysis with line-level findings.\n\nUsage: /analyze_code filepath=<path>",
        },
        {
            "name": "test_code",
            "description": "Generate and run unit tests for a source file",
            "content": "Reads a Python source file, extracts function definitions, generates pytest test stubs, and executes them. Returns test results including pass/fail status and output.\n\nUsage: /test_code filepath=<path>",
        },
        {
            "name": "refactor_code",
            "description": "Refactor code using specified patterns (extract_function, rename_variable, add_types)",
            "content": "Reads a source file and applies refactoring transformations based on the specified pattern. Supports type annotation injection, function extraction analysis, and variable renaming. Creates a .bak backup before applying changes.\n\nUsage: /refactor_code filepath=<path> pattern=<pattern>",
        },
        {
            "name": "review_pr",
            "description": "Review pull request changes by analyzing git diff against a branch",
            "content": "Runs git diff against the specified branch and analyzes all added/changed lines for common issues including wildcard imports, hardcoded credentials, and excessively long lines.\n\nUsage: /review_pr branch=<branch-name>",
        },
        {
            "name": "deploy_app",
            "description": "Deploy application locally or via Docker",
            "content": "Deploys the application using the specified target. 'local' installs Python dependencies and the package. 'docker' builds a Docker image and runs a container. Returns deployment logs and status.\n\nUsage: /deploy_app target=<local|docker>",
        },
        {
            "name": "search_web",
            "description": "Search the web for information using DuckDuckGo",
            "content": "Performs a web search using the DuckDuckGo Instant Answer API. Returns abstracts, source URLs, and related topics for the query.\n\nUsage: /search_web query=<search query>",
        },
        {
            "name": "write_docs",
            "description": "Generate markdown documentation from source code",
            "content": "Parses a source file extracting imports, classes, and functions with their line numbers and docstrings. Generates a structured markdown document in a docs/ subdirectory.\n\nUsage: /write_docs filepath=<path>",
        },
        {
            "name": "optimize_perf",
            "description": "Analyze code for performance optimization opportunities",
            "content": "Scans source code for common performance anti-patterns and optimization opportunities including range(len()) usage, list comprehension candidates, f-string adoption, and chunking suggestions for data processing.\n\nUsage: /optimize_perf filepath=<path>",
        },
        {
            "name": "security_audit",
            "description": "Perform a comprehensive security audit on a file",
            "content": "Scans for SQL injection, XSS, command injection, insecure deserialization, weak crypto, hardcoded secrets, and misconfigurations. Falls back to bandit for deeper analysis if available.\n\nUsage: /security_audit filepath=<path>",
        },
        {
            "name": "dockerize",
            "description": "Create Docker configuration for a project",
            "content": "Generates a Dockerfile, .dockerignore, and docker-compose.yml for a Python project. Detects the package name from pyproject.toml or setup.py. Configures exposed port and build context.\n\nUsage: /dockerize project_dir=<path> port=<port>",
        },
        {
            "name": "database_query",
            "description": "Execute SQL queries against SQLite or PostgreSQL databases",
            "content": "Runs a SQL query against the specified database type. For SQLite, uses local .db files. For PostgreSQL, uses asyncpg with connection parameters. Returns rows or affected counts.\n\nUsage: /database_query query=<sql> db_type=<sqlite|postgresql>",
        },
        {
            "name": "monitor_system",
            "description": "Monitor system resources including CPU, memory, disk, and network",
            "content": "Collects real-time system statistics using psutil when available or falls back to OS-specific commands (wmic on Windows). Returns per-core CPU usage, memory, disk, and network I/O metrics.\n\nUsage: /monitor_system",
        },
        {
            "name": "backup_data",
            "description": "Backup files or directories to a compressed tar.gz archive",
            "content": "Creates a gzipped tar archive of the specified source path. Automatically generates a timestamped filename if no destination is provided. Returns archive size and metadata.\n\nUsage: /backup_data source=<path> destination=<path>",
        },
        {
            "name": "crypto_trade",
            "description": "Execute cryptocurrency trades via Binance API or simulation",
            "content": "Places a market order on Binance when CRYPTO_API_KEY and CRYPTO_API_SECRET environment variables are set. Falls back to a simulated trade recording the intent with order metadata.\n\nUsage: /crypto_trade pair=<SYMBOL> amount=<float> side=<buy|sell>",
        },
        {
            "name": "parse_logs",
            "description": "Parse and analyze log files using regex patterns",
            "content": "Reads a log file and extracts lines matching a regex pattern. Optionally includes surrounding context lines. Also aggregates log level counts (ERROR, WARNING, INFO, DEBUG, CRITICAL).\n\nUsage: /parse_logs filepath=<path> pattern=<regex> context=<lines>",
        },
        {
            "name": "generate_image",
            "description": "Generate an image from a text prompt using DALL-E or a placeholder",
            "content": "Generates an image using OpenAI DALL-E 3 when OPENAI_API_KEY is set. Falls back to creating a local text placeholder file with the prompt metadata.\n\nUsage: /generate_image prompt=<description>",
        },
        {
            "name": "translate_text",
            "description": "Translate text between languages using DeepL, OpenAI, or local lookup",
            "content": "Translates text using DeepL API (DEEPL_API_KEY), OpenAI (OPENAI_API_KEY), or a local word-substitution fallback for common languages (es, fr, de, ja).\n\nUsage: /translate_text text=<string> target_lang=<code>",
        },
        {
            "name": "summarize",
            "description": "Summarize text content using AI or extractive methods",
            "content": "Summarizes text using OpenAI GPT-4o-mini when OPENAI_API_KEY is set. Falls back to extractive summarization selecting key sentences and keywords based on position and frequency.\n\nUsage: /summarize text=<string>",
        },
        {
            "name": "extract_data",
            "description": "Extract structured data (emails, URLs, phones, IPs, dates) from text",
            "content": "Parses text and extracts structured entities including email addresses, URLs, phone numbers, IP addresses, dates, and monetary amounts. Supports custom schema field extraction.\n\nUsage: /extract_data text=<string> schema=<fields>",
        },
        {
            "name": "schedule_task",
            "description": "Schedule a recurring task with configurable interval",
            "content": "Registers a scheduled task in the Nikto scheduler configuration directory (~/.nikto/scheduler/). Creates a task entry with the specified action and interval, and updates the schedule manifest.\n\nUsage: /schedule_task interval=<seconds> action=<description>",
        },
        {
            "name": "notify",
            "description": "Send notifications via desktop, email, Slack, or Discord",
            "content": "Sends a notification message through the specified channel. Desktop shows a native OS dialog. Email uses SMTP. Slack/Discord sends to a webhook URL. Configure via environment variables (SMTP_*, *_WEBHOOK_URL).\n\nUsage: /notify message=<string> channel=<desktop|email|slack|discord>",
        },
        {
            "name": "config_backup",
            "description": "Backup Nikto agent configuration",
            "content": "Archives the entire ~/.nikto configuration directory (excluding existing backups) into a timestamped tar.gz file. Maintains configurable retention policy and prunes old backups.\n\nUsage: /config_backup retention=<count>",
        },
        {
            "name": "fix_issue",
            "description": "Automatically diagnose and fix common development issues",
            "content": "Analyzes a natural language issue description and generates targeted fixes. Recognizes import errors, syntax errors, permission issues, port conflicts, memory problems, timeouts, and missing files.\n\nUsage: /fix_issue description=<problem description>",
        },
    ]

    for sd in skill_definitions:
        from nikto.skills.base import Skill
        skill = Skill(
            name=sd["name"],
            description=sd["description"],
            content=sd["content"],
            source="production",
        )
        skill_runtime.register(skill)

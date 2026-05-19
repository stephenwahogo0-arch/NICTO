import os
import re
import ast
from pathlib import Path
from typing import Optional

from nikto.tools.base import Tool

NIKTO_ROOT = Path(__file__).resolve().parent.parent


async def tool_nikto_read_own(path: str) -> str:
    root = Path(__file__).resolve().parent.parent
    abs_path = (root / path).resolve()
    if not str(abs_path).startswith(str(root)):
        return f"Error: Path '{path}' is outside the nikto codebase"
    if not abs_path.exists():
        return f"Error: File not found: {abs_path}"
    if abs_path.is_dir():
        files = "\n".join(str(p.relative_to(root)) for p in sorted(abs_path.rglob("*")) if p.is_file())
        return f"Directory: {path}\n\nFiles:\n{files}" if files else f"Directory: {path} (empty)"
    content = abs_path.read_text(encoding="utf-8", errors="replace")
    if len(content) > 100000:
        content = content[:100000] + "\n... (truncated at 100K chars)"
    return content


async def tool_nikto_write_own(path: str, content: str) -> str:
    root = Path(__file__).resolve().parent.parent
    abs_path = (root / path).resolve()
    if not str(abs_path).startswith(str(root)):
        return f"Error: Path '{path}' is outside the nikto codebase"
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {abs_path}"


async def tool_nikto_self_review(filepath: str) -> str:
    root = Path(__file__).resolve().parent.parent
    abs_path = (root / filepath).resolve()
    if not str(abs_path).startswith(str(root)):
        return f"Error: Path '{filepath}' is outside the nikto codebase"
    if not abs_path.exists() or not abs_path.suffix == ".py":
        return f"Error: Not a Python file: {abs_path}"
    source = abs_path.read_text(encoding="utf-8")
    issues = []
    tree = ast.parse(source, filename=str(abs_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not node.body:
                issues.append(f"Line {node.lineno}: Empty function '{node.name}'")
            elif all(isinstance(stmt, ast.Pass) for stmt in node.body):
                issues.append(f"Line {node.lineno}: Function '{node.name}' contains only 'pass'")
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append(f"Line {node.lineno}: Bare except clause (catches all exceptions)")
    return f"Review of {filepath}:\n- Lines: {len(source.splitlines())}\n- Issues found: {len(issues)}\n\n" + ("\n".join(issues) if issues else "No issues found.")


NiktoReadOwnTool = Tool(
    name="nikto_read_own",
    description="Read a file from NIKTO's own source code. Path is relative to the nikto package root. Allows NIKTO to inspect its own code for self-improvement.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path within nikto package (e.g., 'tools/self_review.py')"},
        },
        "required": ["path"],
    },
    async_function=tool_nikto_read_own,
)

NiktoWriteOwnTool = Tool(
    name="nikto_write_own",
    description="Write or modify a file in NIKTO's own source code. Path is relative to the nikto package root. Allows NIKTO to rewrite and improve itself.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path within nikto package (e.g., 'tools/self_review.py')"},
            "content": {"type": "string", "description": "Full content to write"},
        },
        "required": ["path", "content"],
    },
    async_function=tool_nikto_write_own,
)

NiktoSelfReviewTool = Tool(
    name="nikto_self_review",
    description="Analyze a Python file in NIKTO's own codebase for quality issues, empty functions, bare excepts, and other problems. Path is relative to the nikto package root.",
    parameters={
        "type": "object",
        "properties": {
            "filepath": {"type": "string", "description": "Relative path to a .py file within nikto package"},
        },
        "required": ["filepath"],
    },
    async_function=tool_nikto_self_review,
)

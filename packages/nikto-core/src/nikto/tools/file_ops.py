import asyncio
import glob as glob_module
import os
import re
from pathlib import Path
from typing import Optional

from nikto.tools.base import Tool


async def tool_read(path: str, offset: Optional[int] = None, limit: Optional[int] = None) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: File not found: {path}"
    if not p.is_file():
        return f"Error: Not a file: {path}"

    with open(p, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    lines = content.splitlines(keepends=True)
    if offset is not None:
        lines = lines[offset - 1:]
    if limit is not None:
        lines = lines[:limit]

    result = "".join(lines)
    if len(result) > 100000:
        result = result[:100000] + "\n... (truncated at 100K chars)"
    return result


async def tool_write(path: str, content: str) -> str:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written {len(content)} bytes to {p}"


async def tool_edit(path: str, old_string: str, new_string: str) -> str:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return f"Error: File not found: {path}"

    content = p.read_text(encoding="utf-8")

    if old_string not in content:
        return f"Error: old_string not found in file. It must match exactly."

    count = content.count(old_string)
    if count > 1:
        return f"Error: Found {count} matches. Please provide more context."

    new_content = content.replace(old_string, new_string, 1)
    p.write_text(new_content, encoding="utf-8")
    return f"Edited {p} - replaced 1 occurrence."


async def tool_glob(pattern: str, path: Optional[str] = None) -> str:
    search_path = Path(path or ".").expanduser().resolve()
    matches = [str(p) for p in search_path.rglob(pattern)]
    matches.sort(key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)
    if not matches:
        return f"No files matching '{pattern}' found in {search_path}"
    return "\n".join(matches[:200])


async def tool_grep(pattern: str, path: Optional[str] = None, include: Optional[str] = None) -> str:
    search_path = Path(path or ".").expanduser().resolve()
    results = []

    files = search_path.rglob("*") if not include else search_path.rglob(include)
    for f in files:
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(text.splitlines(), 1):
                if re.search(pattern, line, re.IGNORECASE):
                    results.append(f"{f}:{i}: {line[:200]}")
        except Exception:
            pass

    if not results:
        return f"No matches for '{pattern}' in {search_path}"
    return "\n".join(results[:200])


FileReadTool = Tool(
    name="read",
    description="Read a file from the filesystem. Provide path, optional offset (line number), and limit (max lines).",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute or relative path to file"},
            "offset": {"type": "integer", "description": "Line number to start from (1-indexed)"},
            "limit": {"type": "integer", "description": "Max lines to read"},
        },
        "required": ["path"],
    },
    async_function=tool_read,
)

FileWriteTool = Tool(
    name="write",
    description="Write content to a file. Creates parent directories if needed. Overwrites existing.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute or relative path to file"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    },
    async_function=tool_write,
)

FileEditTool = Tool(
    name="edit",
    description="Edit a file by replacing exact string matches. Use for targeted edits.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute or relative path to file"},
            "old_string": {"type": "string", "description": "Exact text to find and replace"},
            "new_string": {"type": "string", "description": "Text to replace with"},
        },
        "required": ["path", "old_string", "new_string"],
    },
    async_function=tool_edit,
)

GlobTool = Tool(
    name="glob",
    description="Search for files matching a glob pattern (e.g., '**/*.py').",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Glob pattern to match"},
            "path": {"type": "string", "description": "Directory to search in"},
        },
        "required": ["pattern"],
    },
    async_function=tool_glob,
)

GrepTool = Tool(
    name="grep",
    description="Search file contents using regex patterns. Returns matching lines with file paths.",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search for"},
            "path": {"type": "string", "description": "Directory to search in"},
            "include": {"type": "string", "description": "File pattern filter (e.g., '*.py')"},
        },
        "required": ["pattern"],
    },
    async_function=tool_grep,
)

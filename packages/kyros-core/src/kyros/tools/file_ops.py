import os
import aiofiles
from kyros.tools.base import Tool


class FileReadTool(Tool):
    name = "file_read"
    description = "Read a file from disk"

    async def execute(self, path: str, **kwargs) -> dict:
        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
        return {"success": True, "content": content, "path": path, "size": len(content)}


class FileWriteTool(Tool):
    name = "file_write"
    description = "Write content to a file"

    async def execute(self, path: str, content: str, **kwargs) -> dict:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)
        return {"success": True, "path": path, "bytes_written": len(content)}


class FileEditTool(Tool):
    name = "file_edit"
    description = "Edit a file by replacing old string with new string"

    async def execute(self, path: str, old_string: str, new_string: str, **kwargs) -> dict:
        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            content = await f.read()
        if old_string not in content:
            return {"success": False, "error": "old_string not found in file"}
        new_content = content.replace(old_string, new_string)
        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(new_content)
        return {"success": True, "path": path, "replacements": content.count(old_string)}


class GlobTool(Tool):
    name = "glob"
    description = "Find files matching a glob pattern"

    async def execute(self, pattern: str, path: str = ".", **kwargs) -> dict:
        import glob as glob_mod
        full = os.path.join(path, pattern)
        matches = glob_mod.glob(full, recursive=True)
        return {"success": True, "matches": matches, "count": len(matches)}


class GrepTool(Tool):
    name = "grep"
    description = "Search for a pattern in files"

    async def execute(self, pattern: str, path: str = ".", include: str = "*", **kwargs) -> dict:
        import re
        matches = []
        import glob as glob_mod
        for filepath in glob_mod.glob(os.path.join(path, "**", include), recursive=True):
            if os.path.isfile(filepath):
                try:
                    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
                        content = await f.read()
                    for i, line in enumerate(content.split("\n"), 1):
                        if re.search(pattern, line):
                            matches.append({"file": filepath, "line": i, "text": line.strip()})
                except Exception:
                    pass
        return {"success": True, "matches": matches, "count": len(matches)}

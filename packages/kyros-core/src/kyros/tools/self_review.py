import os
import ast
from uuid import uuid4
from kyros.tools.base import Tool


class KyrosReadOwnTool(Tool):
    name = "kyros_read_own"
    description = "Read KYROS's own source code files"

    async def execute(self, path: str = None, package: str = "kyros", **kwargs) -> dict:
        import kyros
        pkg_dir = os.path.dirname(nikto.__file__)
        target = os.path.join(pkg_dir, path) if path else pkg_dir
        if not os.path.exists(target):
            return {"success": False, "error": f"Path not found: {target}"}
        if os.path.isfile(target):
            async with open(target, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "content": content, "path": target, "size": len(content)}
        files = []
        for root, dirs, fnames in os.walk(target):
            for fname in fnames:
                if fname.endswith(".py"):
                    files.append(os.path.join(root, fname))
        return {"success": True, "files": files, "count": len(files), "path": target}


class KyrosWriteOwnTool(Tool):
    name = "kyros_write_own"
    description = "Write/modify KYROS's own source code"

    async def execute(self, path: str, content: str, **kwargs) -> dict:
        import kyros
        pkg_dir = os.path.dirname(nikto.__file__)
        full_path = os.path.join(pkg_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        async with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "path": full_path, "bytes_written": len(content)}


class KyrosSelfReviewTool(Tool):
    name = "kyros_self_review"
    description = "Review KYROS's own code quality"

    async def execute(self, path: str = None, **kwargs) -> dict:
        review_id = str(uuid4())[:12]
        import kyros
        pkg_dir = os.path.dirname(nikto.__file__)
        target = os.path.join(pkg_dir, path) if path else pkg_dir
        issues = []
        if os.path.isfile(target) and target.endswith(".py"):
            try:
                with open(target, "r", encoding="utf-8") as f:
                    source = f.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and len(node.body) == 1 and isinstance(node.body[0], ast.Raise):
                        issues.append({"type": "stub", "line": node.lineno, "name": node.name, "severity": "high"})
                    if isinstance(node, ast.ExceptHandler) and node.type is None:
                        issues.append({"type": "bare_except", "line": node.lineno, "severity": "medium"})
            except SyntaxError as e:
                issues.append({"type": "syntax_error", "error": str(e), "severity": "high"})
        return {"success": True, "review_id": review_id, "issues": issues, "file": target, "total_issues": len(issues)}


async def tool_kyros_read_own(path: str = None) -> dict:
    tool = KyrosReadOwnTool()
    return await tool.execute(path=path)


async def tool_kyros_write_own(path: str, content: str) -> dict:
    tool = KyrosWriteOwnTool()
    return await tool.execute(path=path, content=content)


async def tool_kyros_self_review(path: str = None) -> dict:
    tool = KyrosSelfReviewTool()
    return await tool.execute(path=path)

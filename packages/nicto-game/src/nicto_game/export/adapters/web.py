"""Web export adapter — generates HTML5/WebAssembly project via Pyodide."""

from __future__ import annotations
import os
from pathlib import Path

from nicto_game.export.adapters.base import PlatformAdapter


class WebAdapter(PlatformAdapter):
    """Exports game for web via Pyodide/Pygbag."""

    def export(self, code: str, output_dir: str, game_name: str, world_data: dict) -> dict:
        web_dir = Path(output_dir) / "web"
        web_dir.mkdir(parents=True, exist_ok=True)

        game_py = web_dir / "game.py"
        with open(game_py, "w", encoding="utf-8") as f:
            f.write(code)

        html = '<!DOCTYPE html>\n'
        html += '<html lang="en">\n'
        html += '<head>\n'
        html += '  <meta charset="utf-8">\n'
        html += '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        html += '  <title>' + game_name + '</title>\n'
        html += '  <style>\n'
        html += '    * { margin: 0; padding: 0; box-sizing: border-box; }\n'
        html += '    body { background: #000; overflow: hidden; display: flex; justify-content: center; align-items: center; height: 100vh; }\n'
        html += '    canvas { display: block; }\n'
        html += '  </style>\n'
        html += '</head>\n'
        html += '<body>\n'
        html += '  <script src="https://cdn.pyodide.org/pyodide.js"></script>\n'
        html += '  <script>\n'
        html += '    async function main() {\n'
        html += '      const pyodide = await loadPyodide();\n'
        html += '      await pyodide.loadPackage(["numpy", "pygame"]);\n'
        html += '      const response = await fetch("game.py");\n'
        html += '      const code = await response.text();\n'
        html += '      pyodide.runPython(code);\n'
        html += '    }\n'
        html += '    main();\n'
        html += '  </script>\n'
        html += '</body>\n'
        html += '</html>\n'

        html_path = web_dir / "index.html"
        with open(html_path, "w") as f:
            f.write(html)

        return {
            "project_dir": str(web_dir),
            "main_py": str(game_py),
            "index_html": str(html_path),
            "platform": "web",
            "notes": "Serve with any static file server. Uses Pyodide to run Python in browser.",
        }

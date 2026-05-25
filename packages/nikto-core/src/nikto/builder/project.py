"""NIKTO Project Builder — Production-grade project scaffolding from descriptions."""

import os
import json
import shutil
from datetime import datetime, timezone
from typing import Optional


class ProjectResult:
    def __init__(self, success: bool, project_path: str, files_created: list, message: str):
        self.success = success
        self.project_path = project_path
        self.files_created = files_created
        self.message = message

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoProjectBuilder:

    PROJECT_TYPES = {
        "api": ["api", "rest", "backend", "server", "service", "graphql", "grpc"],
        "frontend": ["frontend", "ui", "web", "react", "vue", "angular", "svelte"],
        "fullstack": ["fullstack", "full-stack", "webapp", "web app"],
        "cli": ["cli", "command", "terminal", "tool"],
        "mobile": ["mobile", "android", "ios", "flutter", "react native"],
        "smart_contract": ["contract", "solidity", "blockchain", "web3", "defi", "nft"],
        "docker": ["docker", "container", "compose"],
        "ci_cd": ["ci", "cd", "pipeline", "github actions", "gitlab"],
        "library": ["library", "package", "sdk", "sdk"],
        "data_pipeline": ["data", "etl", "pipeline", "spark", "airflow"],
    }

    async def build_from_description(self, description: str, output_dir: str) -> ProjectResult:
        os.makedirs(output_dir, exist_ok=True)
        files = []
        name = os.path.basename(output_dir) or "project"
        ptype = self.detect_project_type(description)
        readme = (
            f"# {name}\n\n"
            f"## Overview\n{description}\n\n"
            f"## Type\n{ptype}\n\n"
            f"## Getting Started\n\n"
            f"### Prerequisites\n- Python 3.10+ / Node.js 18+\n- Docker (optional)\n\n"
            f"### Installation\n```bash\ncd {name}\npip install -r requirements.txt  # or npm install\n```\n\n"
            f"### Configuration\n1. Copy `.env.example` to `.env`\n2. Update environment variables\n\n"
            f"### Running\n```bash\npython main.py  # or npm run dev\n```\n\n"
            f"## Project Structure\n\n"
            f"```\n{name}/\n├── src/\n├── tests/\n├── config/\n├── docs/\n├── .env.example\n├── .gitignore\n└── README.md\n```\n"
        )
        with open(os.path.join(output_dir, "README.md"), "w") as f:
            f.write(readme)
        files.append("README.md")

        env_content = "# Environment Variables\n# Application\nAPP_NAME=" + name + "\nAPP_ENV=development\nAPP_DEBUG=true\nAPP_PORT=8000\n\n# Database\nDATABASE_URL=sqlite:///data.db\n# DATABASE_URL=postgresql://user:pass@localhost:5432/dbname\n\n# Security\nSECRET_KEY=change-me-to-a-random-string\nJWT_SECRET=change-me\nJWT_ALGORITHM=HS256\nJWT_EXPIRATION=3600\n\n# External Services\nREDIS_URL=redis://localhost:6379/0\n"
        with open(os.path.join(output_dir, ".env.example"), "w") as f:
            f.write(env_content)
        files.append(".env.example")

        gitignore = (
            "# Dependencies\nnode_modules/\n__pycache__/\n.venv/\nvenv/\n*.egg-info/\n\n"
            "# Environment\n.env\n*.local\n\n"
            "# Build\nbuild/\ndist/\n*.egg\n\n"
            "# IDE\n.idea/\n.vscode/\n*.swp\n*.swo\n*~\n\n"
            "# OS\n.DS_Store\nThumbs.db\n\n"
            "# Database\n*.db\n*.sqlite\n\n"
            "# Logs\n*.log\nlogs/\n\n"
            "# Coverage\ncoverage/\n.coverage*\nhtmlcov/\n"
        )
        with open(os.path.join(output_dir, ".gitignore"), "w") as f:
            f.write(gitignore)
        files.append(".gitignore")

        return ProjectResult(True, output_dir, files, f"Project scaffolding created at {output_dir} ({ptype})")

    def detect_project_type(self, description: str) -> str:
        desc_lower = description.lower()
        for ptype, keywords in self.PROJECT_TYPES.items():
            if any(kw in desc_lower for kw in keywords):
                return ptype
        return "general"

    async def build_api(self, spec: dict, lang: str, output_dir: str) -> ProjectResult:
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "app"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "app", "routers"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "app", "models"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "app", "schemas"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "tests"), exist_ok=True)
        files = []
        name = spec.get("name", "api")
        lang = lang.lower()

        if lang in ("python", "py"):
            files.extend(self._write_fastapi_project(output_dir, name))
        elif lang in ("javascript", "js", "node"):
            files.extend(self._write_express_project(output_dir, name))
        elif lang in ("typescript", "ts"):
            files.extend(self._write_express_ts_project(output_dir, name))
        elif lang in ("go", "golang"):
            files.extend(self._write_go_api_project(output_dir, name))
        elif lang in ("rust", "rs"):
            files.extend(self._write_rust_api_project(output_dir, name))
        else:
            files.extend(self._write_fastapi_project(output_dir, name))

        return ProjectResult(True, output_dir, files, f"API project created at {output_dir} ({lang})")

    def _write_fastapi_project(self, out: str, name: str) -> list:
        files = []
        main_py = (
            '"""FastAPI Application"""\n'
            'import os\nfrom fastapi import FastAPI\n'
            'from fastapi.middleware.cors import CORSMiddleware\n\n'
            f'app = FastAPI(title="{name}", version="1.0.0")\n\n'
            'app.add_middleware(\n'
            '    CORSMiddleware,\n'
            '    allow_origins=["*"],\n'
            '    allow_credentials=True,\n'
            '    allow_methods=["*"],\n'
            '    allow_headers=["*"],\n'
            ')\n\n\n@app.get("/")\ndef root():\n'
            '    return {"message": f"Hello from {app.title}", "version": app.version}\n\n\n'
            '@app.get("/health")\ndef health():\n'
            '    return {"status": "healthy"}\n'
        )
        with open(os.path.join(out, "app", "__init__.py"), "w") as f:
            f.write("")
        with open(os.path.join(out, "app", "main.py"), "w") as f:
            f.write(main_py)
        files.append("app/main.py")
        with open(os.path.join(out, "app", "routers", "__init__.py"), "w") as f:
            f.write("")
        with open(os.path.join(out, "app", "models", "__init__.py"), "w") as f:
            f.write("")
        with open(os.path.join(out, "app", "schemas", "__init__.py"), "w") as f:
            f.write("")
        with open(os.path.join(out, "requirements.txt"), "w") as f:
            f.write("fastapi>=0.104.0\nuvicorn[standard]>=0.24.0\npydantic>=2.5.0\nsqlalchemy>=2.0.0\nhttpx>=0.25.0\npytest>=7.4.0\n")
        files.append("requirements.txt")
        return files

    def _write_express_project(self, out: str, name: str) -> list:
        files = []
        pkg = json.dumps({"name": name, "version": "1.0.0", "main": "index.js",
            "scripts": {"start": "node index.js", "dev": "nodemon index.js"},
            "dependencies": {"express": "^4.18.0", "cors": "^2.8.0", "morgan": "^1.10.0",
                "helmet": "^7.0.0"},
            "devDependencies": {"nodemon": "^3.0.0", "jest": "^29.0.0"}}, indent=2)
        with open(os.path.join(out, "package.json"), "w") as f:
            f.write(pkg + "\n")
        files.append("package.json")
        index_js = (
            'const express = require("express");\n'
            'const cors = require("cors");\n'
            'const morgan = require("morgan");\n'
            'const helmet = require("helmet");\n\n'
            'const app = express();\n'
            'const PORT = process.env.PORT || 3000;\n\n'
            'app.use(helmet());\napp.use(cors());\napp.use(morgan("dev"));\n'
            'app.use(express.json());\n\n'
            'app.get("/", (req, res) => {\n'
            f'  res.json({{ message: "Hello from {name}" }});\n'
            '});\n\napp.get("/health", (req, res) => {\n'
            '  res.json({ status: "healthy" });\n'
            '});\n\napp.listen(PORT, () => {\n'
            '  console.log(`Server running on port ${PORT}`);\n'
            '});\n\nmodule.exports = app;\n'
        )
        with open(os.path.join(out, "index.js"), "w") as f:
            f.write(index_js)
        files.append("index.js")
        return files

    def _write_express_ts_project(self, out: str, name: str) -> list:
        files = []
        pkg = json.dumps({"name": name, "version": "1.0.0", "main": "dist/index.js",
            "scripts": {"build": "tsc", "start": "node dist/index.js", "dev": "ts-node src/index.ts"},
            "dependencies": {"express": "^4.18.0", "cors": "^2.8.0"},
            "devDependencies": {"typescript": "^5.3.0", "@types/express": "^4.17.0",
                "@types/cors": "^2.8.0", "ts-node": "^10.9.0"}}, indent=2)
        with open(os.path.join(out, "package.json"), "w") as f:
            f.write(pkg + "\n")
        files.append("package.json")
        tsconfig = '{"compilerOptions": {"target": "ES2020", "module": "commonjs", "outDir": "./dist", "rootDir": "./src", "strict": true, "esModuleInterop": true, "skipLibCheck": true}}\n'
        with open(os.path.join(out, "tsconfig.json"), "w") as f:
            f.write(tsconfig)
        files.append("tsconfig.json")
        os.makedirs(os.path.join(out, "src"), exist_ok=True)
        src = (
            'import express from "express";\n'
            f'const app = express();\nconst PORT = process.env.PORT || 3000;\n'
            'app.use(express.json());\n'
            'app.get("/", (req, res) => res.json({ message: "' + name + '" }));\n'
            'app.listen(PORT, () => console.log(`Running on ${PORT}`));\n'
        )
        with open(os.path.join(out, "src", "index.ts"), "w") as f:
            f.write(src)
        files.append("src/index.ts")
        return files

    def _write_go_api_project(self, out: str, name: str) -> list:
        files = []
        mod = f"module {name}\n\ngo 1.21\n"
        with open(os.path.join(out, "go.mod"), "w") as f:
            f.write(mod)
        files.append("go.mod")
        main_go = (
            'package main\n\nimport (\n\t"fmt"\n\t"log"\n\t"net/http"\n)\n\n'
            'func main() {\n\t'
            'http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {\n\t\t'
            'fmt.Fprintf(w, `{"message": "Hello from ' + name + '"}`)\n\t})\n\t'
            'http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {\n\t\t'
            'fmt.Fprintf(w, `{"status": "healthy"}`)\n\t})\n\t'
            'log.Println("Server on :8080")\n\tlog.Fatal(http.ListenAndServe(":8080", nil))\n}\n'
        )
        with open(os.path.join(out, "main.go"), "w") as f:
            f.write(main_go)
        files.append("main.go")
        return files

    def _write_rust_api_project(self, out: str, name: str) -> list:
        files = []
        cargo = (
            '[package]\nname = "' + name + '"\nversion = "0.1.0"\nedition = "2021"\n\n'
            '[dependencies]\nactix-web = "4"\nserde = { version = "1", features = ["derive"] }\n'
            'tokio = { version = "1", features = ["full"] }\n'
        )
        with open(os.path.join(out, "Cargo.toml"), "w") as f:
            f.write(cargo)
        files.append("Cargo.toml")
        os.makedirs(os.path.join(out, "src"), exist_ok=True)
        main_rs = (
            'use actix_web::{get, web, App, HttpResponse, HttpServer, Responder};\n\n'
            '#[get("/")]\nasync fn index() -> impl Responder {\n'
            '    HttpResponse::Ok().json(serde_json::json!({"message": "' + name + '"}))\n}\n\n'
            '#[get("/health")]\nasync fn health() -> impl Responder {\n'
            '    HttpResponse::Ok().json(serde_json::json!({"status": "healthy"}))\n}\n\n'
            '#[actix_web::main]\nasync fn main() -> std::io::Result<()> {\n'
            '    HttpServer::new(|| App::new().service(index).service(health))\n'
            '        .bind(("127.0.0.1", 8080))?\n'
            '        .run().await\n}\n'
        )
        with open(os.path.join(out, "src", "main.rs"), "w") as f:
            f.write(main_rs)
        files.append("src/main.rs")
        return files

    async def build_fullstack(self, spec: dict, frontend_framework: str,
                              backend_lang: str, output_dir: str) -> ProjectResult:
        os.makedirs(output_dir, exist_ok=True)
        files = []
        client_dir = os.path.join(output_dir, "client")
        server_dir = os.path.join(output_dir, "server")
        os.makedirs(server_dir, exist_ok=True)
        api_spec = {"name": spec.get("name", "api") + "-server"}
        server_result = await self.build_api(api_spec, backend_lang, server_dir)
        files.extend([f"server/{f}" for f in server_result.files_created])
        fw = frontend_framework.lower()
        if fw in ("react", "next"):
            os.makedirs(os.path.join(client_dir, "src", "components"), exist_ok=True)
            os.makedirs(os.path.join(client_dir, "src", "pages"), exist_ok=True)
            os.makedirs(os.path.join(client_dir, "public"), exist_ok=True)
            pkg = json.dumps({"name": spec.get("name", "app") + "-client",
                "private": True, "scripts": {"dev": "vite", "build": "vite build"},
                "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0",
                    "react-router-dom": "^6.20.0", "axios": "^1.6.0"},
                "devDependencies": {"vite": "^5.0.0", "@vitejs/plugin-react": "^4.2.0"}}, indent=2)
            with open(os.path.join(client_dir, "package.json"), "w") as f:
                f.write(pkg + "\n")
            files.append("client/package.json")
        elif fw in ("vue", "nuxt"):
            os.makedirs(client_dir, exist_ok=True)
            pkg = json.dumps({"name": spec.get("name", "app") + "-client",
                "scripts": {"dev": "vite", "build": "vite build"},
                "dependencies": {"vue": "^3.3.0", "vue-router": "^4.2.0", "axios": "^1.6.0"},
                "devDependencies": {"vite": "^5.0.0", "@vitejs/plugin-vue": "^4.5.0"}}, indent=2)
            with open(os.path.join(client_dir, "package.json"), "w") as f:
                f.write(pkg + "\n")
            files.append("client/package.json")
        return ProjectResult(True, output_dir, files,
            f"Fullstack project created at {output_dir} (frontend: {fw}, backend: {backend_lang})")

    async def build_docker_compose(self, spec: dict, output_dir: str) -> ProjectResult:
        os.makedirs(output_dir, exist_ok=True)
        files = []
        services = spec.get("services", ["app"])
        compose = "version: '3.8'\n\nservices:\n"
        for svc in services:
            compose += f"  {svc}:\n    build: .\n    ports:\n      - '8000:8000'\n    env_file: .env\n    restart: unless-stopped\n"
        compose += "\nvolumes:\n  data:\n"
        with open(os.path.join(output_dir, "docker-compose.yml"), "w") as f:
            f.write(compose)
        files.append("docker-compose.yml")
        dockerfile = (
            "FROM python:3.11-slim\n\nWORKDIR /app\n"
            "COPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\n"
            "COPY . .\nEXPOSE 8000\nCMD ['uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000']\n"
        )
        with open(os.path.join(output_dir, "Dockerfile"), "w") as f:
            f.write(dockerfile)
        files.append("Dockerfile")
        return ProjectResult(True, output_dir, files,
            f"Docker Compose project created at {output_dir}")

    async def build_ci_cd(self, spec: dict, platform: str, output_dir: str) -> ProjectResult:
        os.makedirs(output_dir, exist_ok=True)
        files = []
        platform = platform.lower()
        if platform in ("github", "github actions"):
            gh_dir = os.path.join(output_dir, ".github", "workflows")
            os.makedirs(gh_dir, exist_ok=True)
            workflow = (
                'name: CI/CD\n\non:\n  push:\n    branches: [main]\n'
                '  pull_request:\n    branches: [main]\n\njobs:\n'
                '  test:\n    runs-on: ubuntu-latest\n'
                '    steps:\n      - uses: actions/checkout@v4\n'
                '      - name: Set up Python\n'
                '        uses: actions/setup-python@v5\n'
                '        with:\n          python-version: "3.11"\n'
                '      - name: Install dependencies\n'
                '        run: pip install -r requirements.txt\n'
                '      - name: Run tests\n        run: pytest\n'
                '      - name: Lint\n        run: ruff check .\n'
            )
            with open(os.path.join(gh_dir, "ci.yml"), "w") as f:
                f.write(workflow)
            files.append(".github/workflows/ci.yml")
        elif platform in ("gitlab", "gitlab ci"):
            gitlab_ci = (
                'image: python:3.11\n\nstages:\n  - test\n  - build\n  - deploy\n\n'
                'before_script:\n  - pip install -r requirements.txt\n\n'
                'test:\n  stage: test\n  script:\n    - pytest\n    - ruff check .\n\n'
                'build:\n  stage: build\n  script:\n    - docker build -t $CI_REGISTRY_IMAGE .\n'
            )
            with open(os.path.join(output_dir, ".gitlab-ci.yml"), "w") as f:
                f.write(gitlab_ci)
            files.append(".gitlab-ci.yml")
        return ProjectResult(True, output_dir, files,
            f"CI/CD config created at {output_dir} ({platform})")

    async def build_frontend(self, spec: dict, framework: str, output_dir: str) -> ProjectResult:
        os.makedirs(output_dir, exist_ok=True)
        files = []
        fw = framework.lower()
        if fw in ("react",):
            os.makedirs(os.path.join(output_dir, "src", "components"), exist_ok=True)
            os.makedirs(os.path.join(output_dir, "src", "pages"), exist_ok=True)
            with open(os.path.join(output_dir, "src", "App.jsx"), "w") as f:
                f.write('import React from "react";\nexport default function App() {\n  return <div>Hello from {name}</div>;\n}\n'.format(name=spec.get("name", "app")))
            files.append("src/App.jsx")
        elif fw in ("vue",):
            with open(os.path.join(output_dir, "src", "App.vue"), "w") as f:
                f.write('<template>\n  <div>Hello from {name}</div>\n</template>\n\n<script>\nexport default { name: "App" }\n</script>\n'.format(name=spec.get("name", "app")))
            files.append("src/App.vue")
        else:
            with open(os.path.join(output_dir, "index.html"), "w") as f:
                f.write(f'<!DOCTYPE html><html><head><title>{spec.get("name", "app")}</title></head><body><div id="app"></div></body></html>\n')
            files.append("index.html")
        return ProjectResult(True, output_dir, files, f"Frontend project created at {output_dir}")

    async def build_mobile_app(self, spec: dict, platform: str, output_dir: str) -> ProjectResult:
        os.makedirs(output_dir, exist_ok=True)
        if platform == "flutter":
            pubspec = 'name: {name}\ndescription: {name} Flutter project\nversion: 1.0.0\nenvironment:\n  sdk: ">=3.0.0 <4.0.0"\ndependencies:\n  flutter:\n    sdk: flutter\n  http: ^1.1.0\n  provider: ^6.0.0\n'.format(name=spec.get("name", "app"))
            with open(os.path.join(output_dir, "pubspec.yaml"), "w") as f:
                f.write(pubspec)
            return ProjectResult(True, output_dir, ["pubspec.yaml"], f"Flutter project at {output_dir}")
        else:
            pkg = json.dumps({"name": spec.get("name", "app"), "version": "1.0.0",
                "scripts": {"start": "expo start", "android": "expo start --android",
                    "ios": "expo start --ios"},
                "dependencies": {"expo": "~50.0.0", "react": "18.2.0",
                    "react-native": "0.73.0", "@react-navigation/native": "^6.1.0"}}, indent=2)
            with open(os.path.join(output_dir, "package.json"), "w") as f:
                f.write(pkg + "\n")
            return ProjectResult(True, output_dir, ["package.json"], f"React Native project at {output_dir}")

    async def build_cli_tool(self, spec: dict, lang: str, output_dir: str) -> ProjectResult:
        os.makedirs(output_dir, exist_ok=True)
        lang = lang.lower()
        if lang == "python":
            with open(os.path.join(output_dir, "cli.py"), "w") as f:
                f.write('#!/usr/bin/env python3\n"""CLI tool generated by NICTO."""\nimport click\n\n@click.command()\n@click.option("--name", default="world", help="Who to greet")\n@click.option("--count", default=1, type=int, help="Number of times")\ndef main(name, count):\n    """Simple CLI that greets NAME COUNT times."""\n    for _ in range(count):\n        click.echo(f"Hello {name}!")\n\nif __name__ == "__main__":\n    main()\n')
            return ProjectResult(True, output_dir, ["cli.py"], f"Python CLI at {output_dir}")
        elif lang in ("go", "golang"):
            with open(os.path.join(output_dir, "main.go"), "w") as f:
                f.write('package main\n\nimport (\n\t"fmt"\n\t"os"\n)\n\nfunc main() {\n\tname := "World"\n\tif len(os.Args) > 1 {\n\t\tname = os.Args[1]\n\t}\n\tfmt.Printf("Hello, %s!\\n", name)\n}\n')
            return ProjectResult(True, output_dir, ["main.go"], f"Go CLI at {output_dir}")
        return await self.build_from_description(f"CLI tool: {spec}", output_dir)

    async def build_smart_contract(self, spec: dict, output_dir: str) -> ProjectResult:
        os.makedirs(output_dir, exist_ok=True)
        contract = '''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract {name} {{
    string public name;
    string public symbol;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;

    event Transfer(address indexed from, address indexed to, uint256 value);

    constructor(string memory _name, string memory _symbol, uint256 _supply) {{
        name = _name;
        symbol = _symbol;
        totalSupply = _supply;
        balanceOf[msg.sender] = _supply;
    }}

    function transfer(address to, uint256 amount) public returns (bool) {{
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }}

    function getInfo() public view returns (string memory, string memory, uint256) {{
        return (name, symbol, totalSupply);
    }}
}}
'''.format(name=spec.get("name", "Token"), symbol=spec.get("symbol", "TKN"))
        with open(os.path.join(output_dir, "contract.sol"), "w") as f:
            f.write(contract)
        return ProjectResult(True, output_dir, ["contract.sol"], f"Smart contract at {output_dir}")

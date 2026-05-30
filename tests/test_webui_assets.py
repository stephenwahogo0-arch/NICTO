"""Regression tests for bundled NIKTO web UI brand assets."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[1]
CORE_WEBUI = REPO_ROOT / "packages" / "nikto-core" / "src" / "nikto" / "webui"
WEB_PUBLIC = REPO_ROOT / "packages" / "nikto-web" / "public"
ROUTES_PY = REPO_ROOT / "packages" / "nikto-core" / "src" / "nikto" / "api" / "routes.py"


SVG_ASSETS = [
    CORE_WEBUI / "assets" / "favicon.svg",
    CORE_WEBUI / "assets" / "nikto-logo.svg",
    WEB_PUBLIC / "favicon.svg",
    WEB_PUBLIC / "nikto-logo.svg",
]


def load_routes_module():
    spec = importlib.util.spec_from_file_location("nikto_api_routes_for_test", ROUTES_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_brand_assets_are_text_svg_not_binary_images():
    for path in SVG_ASSETS:
        content = path.read_text(encoding="utf-8")
        assert content.lstrip().startswith("<svg"), path
        assert "NIKTO" in content, path

    binary_extensions = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}
    for asset_dir in (CORE_WEBUI / "assets", WEB_PUBLIC):
        assert not [p for p in asset_dir.iterdir() if p.suffix.lower() in binary_extensions]


def test_html_pages_reference_svg_brand_assets():
    core_html = (CORE_WEBUI / "index.html").read_text(encoding="utf-8")
    web_html = (REPO_ROOT / "packages" / "nikto-web" / "index.html").read_text(encoding="utf-8")
    react_app = (REPO_ROOT / "packages" / "nikto-web" / "src" / "App.tsx").read_text(encoding="utf-8")

    assert "/assets/favicon.svg" in core_html
    assert "/assets/nikto-logo.svg" in core_html
    assert "/favicon.svg" in web_html
    assert "/nikto-logo.svg" in web_html
    assert "/nikto-logo.svg" in react_app


def test_api_serves_bundled_svg_assets():
    routes = load_routes_module()
    assert any(getattr(route, "path", "") == "/assets" for route in routes.app.routes)

    client = TestClient(routes.app)
    response = client.get("/assets/favicon.svg")

    assert response.status_code == 200
    assert response.text.lstrip().startswith("<svg")
    assert "image/svg" in response.headers["content-type"]

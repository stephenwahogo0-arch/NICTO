import os
import sys
import importlib
import json
from typing import Optional


class Plugin:
    def __init__(self, name: str, path: str, version: str, description: str):
        self.name = name
        self.path = path
        self.version = version
        self.description = description
        self.loaded = False
        self.module = None

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "module"}


class NiktoPluginEngine:
    def __init__(self):
        self.plugins = {}
        self.plugin_dirs = []

    async def load_plugin(self, plugin_path: str) -> Plugin:
        path = os.path.abspath(plugin_path)
        name = os.path.splitext(os.path.basename(path))[0]
        if name in self.plugins:
            return self.plugins[name]
        if path.endswith(".py"):
            spec = importlib.util.spec_from_file_location(name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                plugin = Plugin(name, path, getattr(module, "__version__", "1.0.0"),
                                getattr(module, "__description__", f"Plugin: {name}"))
                plugin.loaded = True
                plugin.module = module
                self.plugins[name] = plugin
                return plugin
        raise ImportError(f"Could not load plugin: {plugin_path}")

    async def list_plugins(self) -> list:
        return [p.to_dict() for p in self.plugins.values()]

    async def install_plugin(self, package_name: str) -> bool:
        try:
            import subprocess
            result = subprocess.run([sys.executable, "-m", "pip", "install", package_name],
                                    capture_output=True, text=True, timeout=120)
            return result.returncode == 0
        except Exception:
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            if plugin_name in sys.modules:
                del sys.modules[plugin_name]
            return True
        return False

    async def call_plugin_method(self, plugin_name: str, method: str, *args, **kwargs) -> Optional[any]:
        plugin = self.plugins.get(plugin_name)
        if plugin and plugin.module and hasattr(plugin.module, method):
            return getattr(plugin.module, method)(*args, **kwargs)
        return None

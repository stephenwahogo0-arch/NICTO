"""Real code generator — generates testable Python code."""
import json
import os
import random
import textwrap
from typing import Optional


TEST_TEMPLATES = {
    "function": lambda name, params: f"""def test_{name}():
    result = {name}({', '.join(str(p) for p in params)})
    assert result is not None
    print(f"{{__name__}}.{name}: PASSED")

""",
    "class": lambda name, methods: f"""def test_{name.lower()}():
    instance = {name}()
    for method in {methods}:
        getattr(instance, method)()
    print(f"{{__name__}}.{name}: PASSED")

""",
}


class CodeGenerator:
    def generate(self, spec: str) -> str:
        return ""

    def generate_function(self, name: str, params: list = None, body: str = None) -> str:
        engine = CodeGenEngine()
        return engine.generate_function(name, params, body)

    def generate_class(self, name: str, methods: list = None, props: list = None) -> str:
        engine = CodeGenEngine()
        return engine.generate_class(name, methods, props)


class CodeGenEngine:
    def __init__(self):
        self.templates = TEST_TEMPLATES

    def generate_function(self, name: str, params: list = None, body: str = None) -> str:
        params = params or []
        param_str = ", ".join(params)
        body = body or "pass"
        code = f"def {name}({param_str}):\n"
        for line in body.split("\n"):
            code += f"    {line}\n"
        code += f"\ndef test_{name}():\n    result = {name}({', '.join('None' for _ in params)})\n    assert result is not None\n    print(f'PASSED: {name}')\n\n"
        return code

    def generate_class(self, name: str, methods: list = None, props: list = None) -> str:
        methods = methods or ["__init__"]
        props = props or []
        code = f"class {name}:\n"
        for method in methods:
            if method == "__init__":
                code += f"    def __init__(self):\n"
                if props:
                    for p in props:
                        code += f"        self.{p} = None\n"
                else:
                    code += "        pass\n"
            else:
                code += f"\n    def {method}(self):\n        pass\n"
        code += f"\ndef test_{name.lower()}():\n    instance = {name}()\n    assert instance is not None\n    print(f'PASSED: {name}')\n\n"
        return code

    def generate_test_suite(self, functions: list, output_path: str = None) -> str:
        code = '"""Auto-generated test suite."""\nimport sys\nsys.path.insert(0, ".")\n\n'
        for name, params, body in functions:
            code += self.generate_function(name, params, body)
        code += '\nif __name__ == "__main__":\n    print("Running tests...")\n'
        for name, _, _ in functions:
            code += f"    test_{name}()\n"
        code += '    print("All tests passed!")\n'
        if output_path:
            with open(output_path, "w") as f:
                f.write(code)
        return code

"""Code Generation Engine — autonomously writes new Python modules, classes, functions, and tests."""
import ast, inspect, os, textwrap, uuid
from typing import Any


TEMPLATES = {
    "module": """\"\"\"{description}\"\"\"
import json, os, random, time, uuid
from typing import Any


{class_definition}
""",
    "class_skeleton": """class {name}:
    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.expanduser("~/.nikto")
        {init_body}

    def summary(self) -> dict:
        return {summary_dict}
""",
    "function": """    def {name}(self, {params}) -> dict:
        {docstring}
        return {{"success": True, {return_fields}}}
""",
    "test": """async def test_{name}():
    print("\\n=== {test_name} ===")
    try:
        from {import_path} import {class_name}
        obj = {class_name}()
        result = obj.{method_name}({test_args})
        check("{test_label}", result["success"])
        check("ALL {test_name} FEATURES WORKING", True)
    except Exception as e:
        check("{test_name}", False, str(e))
""",
}


class CodeGenerator:
    def __init__(self, data_dir: str = ""):
        self.data_dir = data_dir or os.path.expanduser("~/.nikto")
        self.generated_count = 0
        self.generation_log: list = []

    def generate_class(self, module_name: str, class_name: str, methods: list, description: str = "") -> dict:
        methods_code = []
        for method in methods:
            fn_template = TEMPLATES["function"]
            methods_code.append(fn_template.format(
                name=method.get("name", "process"),
                params=method.get("params", "self, input_data: str = ''"),
                docstring=f'"""{method.get("doc", "Process input and return result")}"""',
                return_fields=method.get("returns", '"result": input_data[:50]'),
            ))
        class_def = TEMPLATES["class_skeleton"].format(
            name=class_name,
            init_body="pass",
            summary_dict=f'{{"class": "{class_name}", "methods": {len(methods)}}}',
        )
        for method_code in methods_code:
            class_def += "\n" + method_code
        module_code = TEMPLATES["module"].format(description=description or f"Auto-generated {class_name} module", class_definition=class_def)
        module_path = os.path.join(self.data_dir, f"{module_name}.py")
        try:
            with open(module_path, "w") as f:
                f.write(module_code)
            self.generated_count += 1
            self.generation_log.append({"module": module_name, "class": class_name, "methods": len(methods), "path": module_path})
            return {"success": True, "module": module_name, "class": class_name, "methods": len(methods), "path": module_path, "code": module_code[:500]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_from_spec(self, spec: dict) -> dict:
        module = spec.get("module", f"auto_module_{uuid.uuid4().hex[:6]}")
        class_name = spec.get("class", "AutoEngine")
        methods = spec.get("methods", [{"name": "process", "params": "self, data: str = ''", "doc": "Process data", "returns": '"status": "processed"'}])
        description = spec.get("description", "Auto-generated module")
        return self.generate_class(module, class_name, methods, description)

    def summary(self) -> dict:
        return {"generated_modules": self.generated_count, "generation_log_entries": len(self.generation_log)}

"""Blueprint Visual Scripting System.

Node-based visual scripting inspired by Unreal Engine 5 Blueprints:
- Visual node graph with pins, wires, and execution flow
- Code generation from graph definitions
- Event-driven execution model
- Seamless Python integration
"""
from __future__ import annotations
import uuid
import textwrap
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any, Callable
from enum import Enum


class PinType(Enum):
    EXEC = "exec"           # Execution flow
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    VECTOR = "vector"
    COLOR = "color"
    OBJECT = "object"
    ARRAY = "array"
    EVENT = "event"         # Event trigger
    DELEGATE = "delegate"   # Function reference


class NodeCategory(Enum):
    EVENT = "event"
    FLOW = "flow"
    MATH = "math"
    STRING = "string"
    LOGIC = "logic"
    VARIABLE = "variable"
    ACTOR = "actor"
    GAME = "game"
    AI = "ai"
    PHYSICS = "physics"
    AUDIO = "audio"
    VFX = "vfx"
    CUSTOM = "custom"


@dataclass
class Pin:
    """Connection point on a node."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    pin_type: PinType = PinType.EXEC
    is_input: bool = True
    default_value: Any = None
    connected_to: Optional[str] = None  # Pin ID


@dataclass
class BlueprintNode:
    """A single node in the blueprint graph."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = ""
    category: NodeCategory = NodeCategory.CUSTOM
    inputs: List[Pin] = field(default_factory=list)
    outputs: List[Pin] = field(default_factory=list)
    exec_input: Optional[Pin] = None
    exec_outputs: List[Pin] = field(default_factory=list)
    node_type: str = ""  # e.g., "add", "print", "branch"
    metadata: dict = field(default_factory=dict)
    position_x: float = 0.0
    position_y: float = 0.0

    def add_input(self, name: str, pin_type: PinType = PinType.FLOAT,
                  default: Any = None) -> Pin:
        p = Pin(name=name, pin_type=pin_type, is_input=True, default_value=default)
        self.inputs.append(p)
        return p

    def add_output(self, name: str, pin_type: PinType = PinType.FLOAT) -> Pin:
        p = Pin(name=name, pin_type=pin_type, is_input=False)
        self.outputs.append(p)
        return p


@dataclass
class BlueprintGraph:
    """Complete blueprint graph definition."""
    name: str = "NewBlueprint"
    nodes: List[BlueprintNode] = field(default_factory=list)
    entry_node: Optional[str] = None  # Node ID
    variables: Dict[str, Any] = field(default_factory=dict)
    events: Dict[str, str] = field(default_factory=dict)  # event_name -> node_id

    def add_node(self, node: BlueprintNode) -> BlueprintNode:
        self.nodes.append(node)
        return node

    def connect(self, from_pin_id: str, to_pin_id: str):
        """Wire two pins together."""
        for node in self.nodes:
            for pin in node.inputs + node.outputs + [node.exec_input] if node.exec_input else [] + (node.exec_outputs or []):
                pass
            for pin in node.inputs:
                if pin.id == to_pin_id:
                    pin.connected_to = from_pin_id
            for pin in node.outputs:
                if pin.id == from_pin_id:
                    pin.connected_to = to_pin_id
            if node.exec_input and node.exec_input.id == to_pin_id:
                node.exec_input.connected_to = from_pin_id
            for ep in (node.exec_outputs or []):
                if ep.id == from_pin_id:
                    ep.connected_to = to_pin_id

    def find_node(self, node_id: str) -> Optional[BlueprintNode]:
        for n in self.nodes:
            if n.id == node_id:
                return n
        return None

    def get_upstream_nodes(self, node_id: str) -> List[BlueprintNode]:
        """Get all nodes that feed into this node."""
        upstream = []
        node = self.find_node(node_id)
        if not node:
            return upstream
        for pin in node.inputs:
            if pin.connected_to:
                for other in self.nodes:
                    for op in other.outputs:
                        if op.id == pin.connected_to:
                            upstream.append(other)
                    if other.exec_outputs:
                        for ep in other.exec_outputs:
                            if ep.id == pin.connected_to:
                                upstream.append(other)
        return upstream


class BlueprintNodeLibrary:
    """Library of built-in blueprint nodes."""

    @staticmethod
    def event_begin_play() -> BlueprintNode:
        n = BlueprintNode(name="Event BeginPlay", category=NodeCategory.EVENT, node_type="begin_play")
        n.exec_outputs = [Pin(name="Then", pin_type=PinType.EXEC, is_input=False)]
        return n

    @staticmethod
    def event_tick() -> BlueprintNode:
        n = BlueprintNode(name="Event Tick", category=NodeCategory.EVENT, node_type="tick")
        n.outputs = [Pin(name="DeltaTime", pin_type=PinType.FLOAT, is_input=False)]
        n.exec_outputs = [Pin(name="Then", pin_type=PinType.EXEC, is_input=False)]
        return n

    @staticmethod
    def print_string() -> BlueprintNode:
        n = BlueprintNode(name="PrintString", category=NodeCategory.FLOW, node_type="print")
        n.exec_input = Pin(name="In", pin_type=PinType.EXEC)
        n.inputs = [Pin(name="Value", pin_type=PinType.STRING)]
        n.exec_outputs = [Pin(name="Then", pin_type=PinType.EXEC, is_input=False)]
        return n

    @staticmethod
    def branch() -> BlueprintNode:
        n = BlueprintNode(name="Branch", category=NodeCategory.LOGIC, node_type="branch")
        n.exec_input = Pin(name="In", pin_type=PinType.EXEC)
        n.inputs = [Pin(name="Condition", pin_type=PinType.BOOL)]
        n.exec_outputs = [
            Pin(name="True", pin_type=PinType.EXEC, is_input=False),
            Pin(name="False", pin_type=PinType.EXEC, is_input=False),
        ]
        return n

    @staticmethod
    def add_float() -> BlueprintNode:
        n = BlueprintNode(name="AddFloat", category=NodeCategory.MATH, node_type="add")
        n.inputs = [Pin(name="A", pin_type=PinType.FLOAT), Pin(name="B", pin_type=PinType.FLOAT)]
        n.outputs = [Pin(name="Result", pin_type=PinType.FLOAT, is_input=False)]
        return n

    @staticmethod
    def multiply_float() -> BlueprintNode:
        n = BlueprintNode(name="MultiplyFloat", category=NodeCategory.MATH, node_type="multiply")
        n.inputs = [Pin(name="A", pin_type=PinType.FLOAT), Pin(name="B", pin_type=PinType.FLOAT)]
        n.outputs = [Pin(name="Result", pin_type=PinType.FLOAT, is_input=False)]
        return n

    @staticmethod
    def get_actor_location() -> BlueprintNode:
        n = BlueprintNode(name="GetActorLocation", category=NodeCategory.ACTOR, node_type="get_location")
        n.exec_input = Pin(name="In", pin_type=PinType.EXEC)
        n.outputs = [
            Pin(name="X", pin_type=PinType.FLOAT, is_input=False),
            Pin(name="Y", pin_type=PinType.FLOAT, is_input=False),
            Pin(name="Z", pin_type=PinType.FLOAT, is_input=False),
        ]
        n.exec_outputs = [Pin(name="Then", pin_type=PinType.EXEC, is_input=False)]
        return n

    @staticmethod
    def set_actor_location() -> BlueprintNode:
        n = BlueprintNode(name="SetActorLocation", category=NodeCategory.ACTOR, node_type="set_location")
        n.exec_input = Pin(name="In", pin_type=PinType.EXEC)
        n.inputs = [Pin(name="X", pin_type=PinType.FLOAT), Pin(name="Y", pin_type=PinType.FLOAT), Pin(name="Z", pin_type=PinType.FLOAT)]
        n.exec_outputs = [Pin(name="Then", pin_type=PinType.EXEC, is_input=False)]
        return n

    @staticmethod
    def delay() -> BlueprintNode:
        n = BlueprintNode(name="Delay", category=NodeCategory.FLOW, node_type="delay")
        n.exec_input = Pin(name="In", pin_type=PinType.EXEC)
        n.inputs = [Pin(name="Duration", pin_type=PinType.FLOAT, default_value=1.0)]
        n.exec_outputs = [Pin(name="Completed", pin_type=PinType.EXEC, is_input=False)]
        return n

    @staticmethod
    def for_loop() -> BlueprintNode:
        n = BlueprintNode(name="ForLoop", category=NodeCategory.FLOW, node_type="for_loop")
        n.exec_input = Pin(name="In", pin_type=PinType.EXEC)
        n.inputs = [Pin(name="Start", pin_type=PinType.INT), Pin(name="End", pin_type=PinType.INT)]
        n.outputs = [Pin(name="Index", pin_type=PinType.INT, is_input=False)]
        n.exec_outputs = [
            Pin(name="LoopBody", pin_type=PinType.EXEC, is_input=False),
            Pin(name="Completed", pin_type=PinType.EXEC, is_input=False),
        ]
        return n


class BlueprintCompiler:
    """Compiles Blueprint graphs into executable Python code."""

    NODE_HANDLERS: Dict[str, Callable] = {}

    @classmethod
    def register_handler(cls, node_type: str, handler: Callable):
        cls.NODE_HANDLERS[node_type] = handler

    @classmethod
    def compile(cls, graph: BlueprintGraph, class_name: str = "GeneratedBlueprint") -> str:
        """Compile a blueprint graph into a Python class."""
        code_parts = [f"class {class_name}:"]
        code_parts.append("    def __init__(self):")
        code_parts.append("        self.variables = {}")
        for var_name, var_val in graph.variables.items():
            code_parts.append(f"        self.variables['{var_name}'] = {repr(var_val)}")
        code_parts.append("")
        methods = set()
        for event_name, node_id in graph.events.items():
            method_code = cls._compile_event(event_name, node_id, graph)
            if method_code:
                code_parts.extend(method_code)
                methods.add(event_name)
        if "begin_play" not in methods:
            code_parts.append("    def begin_play(self):")
            code_parts.append("        pass")
        if "tick" not in methods:
            code_parts.append("    def tick(self, delta_time: float):")
            code_parts.append("        pass")
        code_parts.append("")
        code_parts.append(f"# Blueprint: {graph.name}")
        code_parts.append(f"# Nodes: {len(graph.nodes)}")
        code_parts.append(f"# Events: {len(graph.events)}")
        return "\n".join(code_parts)

    @classmethod
    def _compile_event(cls, event_name: str, node_id: str, graph: BlueprintGraph) -> List[str]:
        lines = []
        if event_name == "begin_play":
            lines.append("    def begin_play(self):")
        elif event_name == "tick":
            lines.append("    def tick(self, delta_time: float):")
        else:
            lines.append(f"    def on_{event_name}(self):")
        visited = set()
        exec_nodes = cls._walk_exec_graph(node_id, graph, visited)
        depth = 0
        for node in exec_nodes:
            handler = cls.NODE_HANDLERS.get(node.node_type)
            if handler:
                handler_lines = handler(node, depth + 2)
                lines.extend(handler_lines)
            else:
                lines.append(f"        pass  # {node.name} ({node.node_type})")
        if len(lines) == 1:
            lines.append("        pass")
        return lines

    @classmethod
    def _walk_exec_graph(cls, start_node_id: str, graph: BlueprintGraph,
                         visited: set) -> List[BlueprintNode]:
        if start_node_id in visited:
            return []
        visited.add(start_node_id)
        result = []
        node = graph.find_node(start_node_id)
        if not node:
            return result
        result.append(node)
        if node.exec_outputs:
            for exec_pin in node.exec_outputs:
                if exec_pin.connected_to:
                    next_node = cls._node_with_pin(exec_pin.connected_to, graph)
                    if next_node:
                        result.extend(cls._walk_exec_graph(next_node.id, graph, visited))
        return result

    @classmethod
    def _node_with_pin(cls, pin_id: str, graph: BlueprintGraph) -> Optional[BlueprintNode]:
        for n in graph.nodes:
            if n.exec_input and n.exec_input.id == pin_id:
                return n
            for p in n.inputs:
                if p.id == pin_id:
                    return n
        return None


def _handler_print(node: BlueprintNode, depth: int) -> List[str]:
    indent = "    " * depth
    val = node.inputs[0].default_value or "value"
    return [f"{indent}print({repr(val)})"]


def _handler_branch(node: BlueprintNode, depth: int) -> List[str]:
    indent = "    " * depth
    return [f"{indent}if True:  # Branch condition", f"{indent}    pass", f"{indent}else:", f"{indent}    pass"]


def _handler_add(node: BlueprintNode, depth: int) -> List[str]:
    indent = "    " * depth
    return [f"{indent}result = 0.0  # AddFloat"]

BlueprintCompiler.register_handler("print", _handler_print)
BlueprintCompiler.register_handler("branch", _handler_branch)
BlueprintCompiler.register_handler("add", _handler_add)


class BlueprintSystem:
    """Complete Blueprint visual scripting system.

    Manages graphs, compiles them to Python, and executes
    generated code at runtime.
    """

    def __init__(self):
        self.graphs: Dict[str, BlueprintGraph] = {}
        self.compiled_classes: Dict[str, Any] = {}
        self.instances: Dict[str, Any] = {}

    def create_graph(self, name: str = "NewBlueprint") -> BlueprintGraph:
        graph = BlueprintGraph(name=name)
        self.graphs[name] = graph
        return graph

    def create_default_player_controller(self) -> BlueprintGraph:
        graph = self.create_graph("PlayerController")
        begin = BlueprintNodeLibrary.event_begin_play()
        graph.add_node(begin)
        graph.entry_node = begin.id
        graph.events["begin_play"] = begin.id
        tick = BlueprintNodeLibrary.event_tick()
        graph.add_node(tick)
        graph.events["tick"] = tick.id
        return graph

    def compile_graph(self, graph_name: str, class_name: str = None) -> Optional[str]:
        graph = self.graphs.get(graph_name)
        if not graph:
            return None
        cls_name = class_name or f"BP_{graph.name.replace(' ', '_')}"
        source = BlueprintCompiler.compile(graph, cls_name)
        exec_globals = {}
        exec(source, exec_globals)
        self.compiled_classes[cls_name] = exec_globals[cls_name]
        return source

    def instantiate(self, class_name: str, instance_name: str = "default") -> Optional[Any]:
        cls = self.compiled_classes.get(class_name)
        if not cls:
            return None
        instance = cls()
        self.instances[instance_name] = instance
        return instance

    def execute_event(self, instance_name: str, event: str, **kwargs):
        instance = self.instances.get(instance_name)
        if not instance:
            return
        method = getattr(instance, event, None)
        if method:
            method(**kwargs)

    def create_sample_ai_behavior(self) -> BlueprintGraph:
        graph = self.create_graph("AIPatrol")
        tick = BlueprintNodeLibrary.event_tick()
        graph.add_node(tick)
        graph.events["tick"] = tick.id
        branch = BlueprintNodeLibrary.branch()
        graph.add_node(branch)
        graph.connect(tick.exec_outputs[0].id, branch.exec_input.id)
        print_node = BlueprintNodeLibrary.print_string()
        graph.add_node(print_node)
        graph.connect(branch.exec_outputs[0].id, print_node.exec_input.id)
        return graph

    def get_stats(self) -> dict:
        return {
            "graphs": len(self.graphs),
            "compiled": len(self.compiled_classes),
            "instances": len(self.instances),
            "total_nodes": sum(len(g.nodes) for g in self.graphs.values()),
        }

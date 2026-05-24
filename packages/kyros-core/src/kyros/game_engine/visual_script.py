"""KYROS Visual Scripting System — node-based game logic like Unreal Blueprints.
Users connect nodes visually to build gameplay without writing code."""

import json
import math
import uuid
from typing import Any, Callable, Optional


class NodePin:
    def __init__(self, name, pin_type="exec", data_type="any", direction="input", default_value=None):
        self.id = uuid.uuid4().hex[:8]
        self.name = name
        self.pin_type = pin_type  # "exec", "data", "flow"
        self.data_type = data_type  # "int", "float", "bool", "string", "object", "any"
        self.direction = direction  # "input", "output"
        self.default_value = default_value
        self.connections = []  # List of (other_pin_id, other_node_id)
        self.value = default_value

    def connect_to(self, other_pin):
        if other_pin.id not in [c[0] for c in self.connections]:
            self.connections.append((other_pin.id, other_pin.node_id))
            other_pin.connections.append((self.id, self.node_id))

    def disconnect_all(self):
        self.connections.clear()

    def get_value(self, context=None):
        if self.connections and context:
            other_id, other_node = self.connections[0]
            node = context.get(other_node)
            if node and other_id in node.output_pins:
                return node.output_pins[other_id].value
        return self.value

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "pin_type": self.pin_type,
            "data_type": self.data_type, "direction": self.direction,
            "default_value": self.default_value,
            "connections": self.connections,
        }


class Node:
    def __init__(self, name="Node", category="General", color=(100, 100, 100)):
        self.id = uuid.uuid4().hex[:12]
        self.name = name
        self.category = category
        self.color = color
        self.pos_x = 0
        self.pos_y = 0
        self.input_pins = {}
        self.output_pins = {}
        self.exec_input = None
        self.exec_outputs = []
        self._func = None
        self._async_func = None
        self.comment = ""

    def add_input(self, name, data_type="any", default=None):
        pin = NodePin(name, "data", data_type, "input", default)
        self.input_pins[pin.id] = pin
        return pin

    def add_output(self, name, data_type="any", default=None):
        pin = NodePin(name, "data", data_type, "output", default)
        self.output_pins[pin.id] = pin
        return pin

    def add_exec_input(self, name="in"):
        self.exec_input = NodePin(name, "exec", direction="input")
        return self.exec_input

    def add_exec_output(self, name="out"):
        pin = NodePin(name, "exec", direction="output")
        self.exec_outputs.append(pin)
        return pin

    def execute(self, context=None):
        if self._func:
            return self._func(self, context)
        return None

    async def execute_async(self, context=None):
        if self._async_func:
            return await self._async_func(self, context)
        return self.execute(context)

    def on_execute(self, func):
        self._func = func
        return self

    def on_execute_async(self, func):
        self._async_func = func
        return self

    def get_input(self, name, context=None):
        for pin in self.input_pins.values():
            if pin.name == name:
                return pin.get_value(context)
        return None

    def set_output(self, name, value):
        for pin in self.output_pins.values():
            if pin.name == name:
                pin.value = value

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "category": self.category,
            "color": self.color, "pos_x": self.pos_x, "pos_y": self.pos_y,
            "input_pins": [p.to_dict() for p in self.input_pins.values()],
            "output_pins": [p.to_dict() for p in self.output_pins.values()],
            "exec_input": self.exec_input.to_dict() if self.exec_input else None,
            "exec_outputs": [p.to_dict() for p in self.exec_outputs],
            "comment": self.comment,
        }


class NodeGraph:
    def __init__(self, name="Blueprint"):
        self.name = name
        self.nodes = {}
        self.entry_node = None
        self.variables = {}
        self.events = []
        self.functions = {}

    def add_node(self, node: Node) -> Node:
        self.nodes[node.id] = node
        return node

    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            node = self.nodes[node_id]
            for pin in list(node.input_pins.values()) + list(node.output_pins.values()) + (node.exec_outputs or []):
                pin.disconnect_all()
            if node.exec_input:
                node.exec_input.disconnect_all()
            del self.nodes[node_id]

    def connect(self, from_node_id, from_pin_name, to_node_id, to_pin_name):
        from_node = self.nodes.get(from_node_id)
        to_node = self.nodes.get(to_node_id)
        if not from_node or not to_node:
            return False
        from_pin = None
        for p in from_node.output_pins.values():
            if p.name == from_pin_name:
                from_pin = p
                break
        if not from_pin:
            for p in from_node.exec_outputs:
                if p.name == from_pin_name:
                    from_pin = p
                    break
        to_pin = None
        for p in to_node.input_pins.values():
            if p.name == to_pin_name:
                to_pin = p
                break
        if not to_pin and to_node.exec_input and to_pin_name == "in":
            to_pin = to_node.exec_input
        if from_pin and to_pin:
            from_pin.connect_to(to_pin)
            return True
        return False

    def set_variable(self, name, value):
        self.variables[name] = value

    def get_variable(self, name):
        return self.variables.get(name)

    async def execute(self, start_node_id=None, context=None):
        context = context or {}
        node_id = start_node_id or (self.entry_node.id if self.entry_node else None)
        visited = set()
        while node_id and node_id not in visited:
            visited.add(node_id)
            node = self.nodes.get(node_id)
            if not node:
                break
            result = await node.execute_async(context)
            if result == "stop":
                break
            next_id = None
            if node.exec_outputs:
                for pin in node.exec_outputs:
                    if pin.connections:
                        next_id = pin.connections[0][1]
                        break
            node_id = next_id
        return context

    def to_dict(self):
        return {
            "name": self.name,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "variables": self.variables,
            "entry_node": self.entry_node.id if self.entry_node else None,
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, data):
        if isinstance(data, str):
            data = json.loads(data)
        graph = cls(data.get("name", "Blueprint"))
        for nid, ndata in data.get("nodes", {}).items():
            node = Node(ndata["name"], ndata["category"], tuple(ndata["color"]))
            node.id = nid
            node.pos_x = ndata["pos_x"]
            node.pos_y = ndata["pos_y"]
            node.comment = ndata.get("comment", "")
            for pdata in ndata.get("input_pins", []):
                pin = NodePin(pdata["name"], pdata["pin_type"], pdata["data_type"], "input", pdata["default_value"])
                pin.id = pdata["id"]
                pin.connections = pdata.get("connections", [])
                node.input_pins[pin.id] = pin
            for pdata in ndata.get("output_pins", []):
                pin = NodePin(pdata["name"], pdata["pin_type"], pdata["data_type"], "output", pdata["default_value"])
                pin.id = pdata["id"]
                pin.connections = pdata.get("connections", [])
                node.output_pins[pin.id] = pin
            graph.nodes[nid] = node
        if data.get("entry_node"):
            graph.entry_node = graph.nodes.get(data["entry_node"])
        return graph


class BlueprintNodeLibrary:
    def __init__(self):
        self.node_types = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("print", "Debug", (100, 200, 100), self._make_print_node)
        self.register("if", "Flow", (200, 150, 100), self._make_if_node)
        self.register("for_loop", "Flow", (200, 150, 100), self._make_for_loop_node)
        self.register("add", "Math", (100, 100, 200), self._make_math_node("add", lambda a, b: a + b))
        self.register("subtract", "Math", (100, 100, 200), self._make_math_node("subtract", lambda a, b: a - b))
        self.register("multiply", "Math", (100, 100, 200), self._make_math_node("multiply", lambda a, b: a * b))
        self.register("divide", "Math", (100, 100, 200), self._make_math_node("divide", lambda a, b: a / b if b != 0 else 0))
        self.register("random_range", "Math", (100, 100, 200), self._make_random_range_node)
        self.register("set_variable", "Variables", (150, 100, 150), self._make_set_variable_node)
        self.register("get_variable", "Variables", (150, 100, 150), self._make_get_variable_node)
        self.register("spawn_object", "Game", (100, 150, 100), self._make_spawn_node)
        self.register("destroy_object", "Game", (150, 50, 50), self._make_destroy_node)
        self.register("set_position", "Transform", (100, 150, 200), self._make_set_position_node)
        self.register("get_position", "Transform", (100, 150, 200), self._make_get_position_node)
        self.register("play_sound", "Audio", (150, 100, 200), self._make_play_sound_node)
        self.register("wait", "Flow", (200, 200, 100), self._make_wait_node)
        self.register("event_beginplay", "Events", (50, 150, 50), self._make_event_node("BeginPlay"))
        self.register("event_tick", "Events", (50, 150, 50), self._make_event_node("Tick"))
        self.register("event_keypress", "Events", (50, 150, 50), self._make_event_node("KeyPress"))

    def register(self, name, category, color, factory):
        self.node_types[name] = {"category": category, "color": color, "factory": factory}

    def create_node(self, name):
        if name in self.node_types:
            return self.node_types[name]["factory"]()
        return None

    def get_categories(self):
        cats = {}
        for name, info in self.node_types.items():
            cat = info["category"]
            if cat not in cats:
                cats[cat] = []
            cats[cat].append(name)
        return cats

    def _make_print_node(self):
        node = Node("Print", "Debug", (100, 200, 100))
        node.add_exec_input()
        node.add_exec_output()
        node.add_input("Message", "string", "Hello!")
        node.on_execute(lambda n, ctx: print(f"[Blueprint] {n.get_input('Message')}"))
        return node

    def _make_if_node(self):
        node = Node("Branch", "Flow", (200, 150, 100))
        node.add_exec_input()
        node.add_input("Condition", "bool", True)
        node.add_exec_output("True")
        node.add_exec_output("False")
        async def _exec(n, ctx):
            cond = n.get_input("Condition")
            output = "True" if cond else "False"
            for pin in n.exec_outputs:
                if pin.name == output and pin.connections:
                    return pin.connections[0][1]
        node.on_execute_async(_exec)
        return node

    def _make_for_loop_node(self):
        node = Node("For Loop", "Flow", (200, 150, 100))
        node.add_exec_input()
        node.add_input("Start", "int", 0)
        node.add_input("End", "int", 10)
        node.add_exec_output("Loop Body")
        node.add_exec_output("Completed")
        async def _exec(n, ctx):
            start = int(n.get_input("Start", ctx) or 0)
            end = int(n.get_input("End", ctx) or 10)
            ctx["loop_index"] = start
            if start < end:
                for pin in n.exec_outputs:
                    if pin.name == "Loop Body" and pin.connections:
                        ctx["loop_index"] = start
                        return pin.connections[0][1]
            else:
                for pin in n.exec_outputs:
                    if pin.name == "Completed" and pin.connections:
                        return pin.connections[0][1]
        node.on_execute_async(_exec)
        return node

    def _make_math_node(self, op_name, op_func):
        def factory():
            node = Node(op_name.capitalize(), "Math", (100, 100, 200))
            node.add_exec_input()
            node.add_exec_output()
            node.add_input("A", "float", 0)
            node.add_input("B", "float", 0)
            node.add_output("Result", "float", 0)
            node.on_execute(lambda n, ctx: n.set_output("Result", op_func(
                float(n.get_input("A", ctx) or 0),
                float(n.get_input("B", ctx) or 0)
            )))
            return node
        return factory

    def _make_random_range_node(self):
        node = Node("Random Range", "Math", (100, 100, 200))
        node.add_exec_input()
        node.add_exec_output()
        node.add_input("Min", "float", 0)
        node.add_input("Max", "float", 100)
        node.add_output("Result", "float", 0)
        node.on_execute(lambda n, ctx: n.set_output("Result", random.uniform(
            float(n.get_input("Min", ctx) or 0),
            float(n.get_input("Max", ctx) or 100)
        )))
        return node

    def _make_set_variable_node(self):
        node = Node("Set Variable", "Variables", (150, 100, 150))
        node.add_exec_input()
        node.add_exec_output()
        node.add_input("Name", "string", "myVar")
        node.add_input("Value", "any")
        node.on_execute(lambda n, ctx: ctx.__setitem__(str(n.get_input("Name", ctx)), n.get_input("Value", ctx)))
        return node

    def _make_get_variable_node(self):
        node = Node("Get Variable", "Variables", (150, 100, 150))
        node.add_exec_input()
        node.add_exec_output()
        node.add_input("Name", "string", "myVar")
        node.add_output("Value", "any")
        node.on_execute(lambda n, ctx: n.set_output("Value", ctx.get(str(n.get_input("Name", ctx)))))
        return node

    def _make_spawn_node(self):
        node = Node("Spawn Object", "Game", (100, 150, 100))
        node.add_exec_input()
        node.add_exec_output()
        node.add_input("Object Type", "string", "enemy")
        node.add_input("X", "float", 0)
        node.add_input("Y", "float", 0)
        node.add_output("Spawned", "object")
        node.on_execute(lambda n, ctx: n.set_output("Spawned", {
            "type": n.get_input("Object Type", ctx),
            "x": n.get_input("X", ctx), "y": n.get_input("Y", ctx)
        }))
        return node

    def _make_destroy_node(self):
        node = Node("Destroy Object", "Game", (150, 50, 50))
        node.add_exec_input()
        node.add_exec_output()
        node.add_input("Target", "object")
        return node

    def _make_set_position_node(self):
        node = Node("Set Position", "Transform", (100, 150, 200))
        node.add_exec_input()
        node.add_exec_output()
        node.add_input("Object", "object")
        node.add_input("X", "float")
        node.add_input("Y", "float")
        return node

    def _make_get_position_node(self):
        node = Node("Get Position", "Transform", (100, 150, 200))
        node.add_exec_input()
        node.add_exec_output()
        node.add_input("Object", "object")
        node.add_output("X", "float", 0)
        node.add_output("Y", "float", 0)
        return node

    def _make_play_sound_node(self):
        node = Node("Play Sound", "Audio", (150, 100, 200))
        node.add_exec_input()
        node.add_exec_output()
        node.add_input("Sound Name", "string", "explosion")
        node.add_input("Volume", "float", 1.0)
        return node

    def _make_wait_node(self):
        node = Node("Wait", "Flow", (200, 200, 100))
        node.add_exec_input()
        node.add_input("Duration", "float", 1.0)
        node.add_exec_output("Completed")
        import asyncio
        async def _exec(n, ctx):
            duration = float(n.get_input("Duration", ctx) or 1.0)
            await asyncio.sleep(duration)
            for pin in n.exec_outputs:
                if pin.name == "Completed" and pin.connections:
                    return pin.connections[0][1]
        node.on_execute_async(_exec)
        return node

    def _make_event_node(self, event_name):
        def factory():
            node = Node(event_name, "Events", (50, 150, 50))
            node.add_exec_output("Start")
            node.comment = f"Triggers on {event_name}"
            return node
        return factory


class BlueprintManager:
    def __init__(self):
        self.graphs = {}
        self.library = BlueprintNodeLibrary()
        self.active_graphs = {}

    def create_blueprint(self, name):
        graph = NodeGraph(name)
        self.graphs[name] = graph
        return graph

    def get_blueprint(self, name):
        return self.graphs.get(name)

    async def execute_blueprint(self, name, context=None, event="BeginPlay"):
        graph = self.graphs.get(name)
        if not graph:
            return None
        for node in graph.nodes.values():
            if node.name == event:
                return await graph.execute(node.id, context)
        return None

    def serialize(self):
        return {name: g.to_dict() for name, g in self.graphs.items()}

    def deserialize(self, data):
        for name, gdata in data.items():
            self.graphs[name] = NodeGraph.from_json(gdata)

"""NIKTO AI Engine — behavior trees, state machines, utility AI, pathfinding."""

import math
import heapq
import random
from typing import Any, Optional


class BTNode:
    def __init__(self, name="Node"):
        self.name = name
        self.children = []

    def add(self, child):
        self.children.append(child)
        return child

    def execute(self, blackboard):
        raise NotImplementedError


class BTAction(BTNode):
    def __init__(self, name, func=None):
        super().__init__(name)
        self.func = func

    def execute(self, blackboard):
        if self.func:
            return self.func(blackboard)
        return "success"


class BTCondition(BTNode):
    def __init__(self, name, func=None):
        super().__init__(name)
        self.func = func

    def execute(self, blackboard):
        if self.func:
            return "success" if self.func(blackboard) else "failure"
        return "failure"


class BTSequence(BTNode):
    def execute(self, blackboard):
        for child in self.children:
            result = child.execute(blackboard)
            if result == "failure":
                return "failure"
            if result == "running":
                return "running"
        return "success"


class BTSelector(BTNode):
    def execute(self, blackboard):
        for child in self.children:
            result = child.execute(blackboard)
            if result == "success":
                return "success"
            if result == "running":
                return "running"
        return "failure"


class BTInverter(BTNode):
    def execute(self, blackboard):
        result = self.children[0].execute(blackboard) if self.children else "failure"
        if result == "success":
            return "failure"
        if result == "failure":
            return "success"
        return "running"


class BTSucceeder(BTNode):
    def execute(self, blackboard):
        if self.children:
            self.children[0].execute(blackboard)
        return "success"


class BTRepeater(BTNode):
    def __init__(self, name, count=-1):
        super().__init__(name)
        self.count = count
        self._executed = 0

    def execute(self, blackboard):
        if self.count == -1 or self._executed < self.count:
            if self.children:
                self.children[0].execute(blackboard)
            self._executed += 1
            return "running"
        self._executed = 0
        return "success"


class BTParallel(BTNode):
    def __init__(self, name, required=1):
        super().__init__(name)
        self.required = required

    def execute(self, blackboard):
        successes = 0
        failures = 0
        for child in self.children:
            result = child.execute(blackboard)
            if result == "success":
                successes += 1
            elif result == "failure":
                failures += 1
        if successes >= self.required:
            return "success"
        if failures > len(self.children) - self.required:
            return "failure"
        return "running"


class BehaviourTree:
    def __init__(self, root=None):
        self.root = root
        self.blackboard = {}
        self.running = True

    def set(self, key, value):
        self.blackboard[key] = value

    def get(self, key, default=None):
        return self.blackboard.get(key, default)

    def update(self):
        if self.root and self.running:
            return self.root.execute(self.blackboard)
        return "failure"

    def stop(self):
        self.running = False


def create_patrol_ai():
    """Create a patrol behavior tree."""
    seq = BTSequence("PatrolSequence")
    move = BTAction("MoveToPatrolPoint", lambda bb: (
        None if not bb.get("patrol_points") else
        setattr(bb.get("self"), "target", bb.get("patrol_points", [])[bb.get("patrol_index", 0) % len(bb.get("patrol_points", []))]),
        None if not bb.get("patrol_points") else bb.__setitem__("patrol_index", bb.get("patrol_index", 0) + 1),
        "success"
    ))
    wait = BTAction("Wait", lambda bb: "success")
    seq.add(move)
    seq.add(wait)
    return BehaviourTree(seq)


class StateMachine:
    def __init__(self, owner=None):
        self.owner = owner
        self.states = {}
        self.current_state = None
        self.previous_state = None
        self.global_state = None

    def add_state(self, name, enter=None, update=None, exit=None):
        self.states[name] = {
            "enter": enter or (lambda: None),
            "update": update or (lambda dt: None),
            "exit": exit or (lambda: None),
        }
        return self

    def change_state(self, name):
        if name not in self.states:
            return
        if self.current_state:
            self.states[self.current_state]["exit"]()
        self.previous_state = self.current_state
        self.current_state = name
        self.states[name]["enter"]()

    def update(self, dt):
        if self.global_state:
            self.states[self.global_state]["update"](dt)
        if self.current_state:
            self.states[self.current_state]["update"](dt)

    def revert_to_previous(self):
        if self.previous_state:
            self.change_state(self.previous_state)


class UtilityConsideration:
    def __init__(self, name, weight=1.0, curve="linear"):
        self.name = name
        self.weight = weight
        self.curve = curve

    def evaluate(self, context):
        val = self._get_value(context)
        if self.curve == "linear":
            return val * self.weight
        elif self.curve == "quadratic":
            return (val * val) * self.weight
        elif self.curve == "logistic":
            return (1.0 / (1.0 + math.exp(-val * 10))) * self.weight
        return val * self.weight

    def _get_value(self, context):
        return context.get(self.name, 0.0)


class UtilityAction:
    def __init__(self, name):
        self.name = name
        self.considerations = []

    def add_consideration(self, consideration):
        self.considerations.append(consideration)

    def evaluate(self, context):
        score = 1.0
        for c in self.considerations:
            score *= c.evaluate(context)
        return score

    def execute(self, context):
        pass


class UtilityAI:
    def __init__(self):
        self.actions = []

    def add_action(self, action):
        self.actions.append(action)

    def select_action(self, context):
        best_action = None
        best_score = -1.0
        for action in self.actions:
            score = action.evaluate(context)
            if score > best_score:
                best_score = score
                best_action = action
        return best_action

    def update(self, context):
        action = self.select_action(context)
        if action:
            action.execute(context)


class NavNode:
    def __init__(self, x, y, node_id=None):
        self.x = x
        self.y = y
        self.id = node_id or f"{x},{y}"
        self.neighbors = []
        self.cost = 1.0
        self.blocked = False

    def add_neighbor(self, node, cost=1.0):
        self.neighbors.append((node, cost))

    def heuristic(self, other):
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class NavGrid:
    def __init__(self, width, height, cell_size=32, walkable_func=None):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.nodes = {}
        for gy in range(height):
            for gx in range(width):
                walkable = True
                if walkable_func:
                    walkable = walkable_func(gx, gy)
                node = NavNode(gx * cell_size + cell_size / 2, gy * cell_size + cell_size / 2, f"{gx},{gy}")
                node.blocked = not walkable
                self.nodes[node.id] = node
        for gy in range(height):
            for gx in range(width):
                node = self.get_node(gx, gy)
                if not node or node.blocked:
                    continue
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]:
                    nx, ny = gx + dx, gy + dy
                    neighbor = self.get_node(nx, ny)
                    if neighbor and not neighbor.blocked:
                        cost = 1.414 if abs(dx) == 1 and abs(dy) == 1 else 1.0
                        node.add_neighbor(neighbor, cost)

    def get_node(self, gx, gy):
        return self.nodes.get(f"{gx},{gy}")

    def world_to_grid(self, wx, wy):
        return int(wx // self.cell_size), int(wy // self.cell_size)

    def find_path_a_star(self, start_x, start_y, end_x, end_y):
        sx, sy = self.world_to_grid(start_x, start_y)
        ex, ey = self.world_to_grid(end_x, end_y)
        start = self.get_node(sx, sy)
        end = self.get_node(ex, ey)
        if not start or not end or start.blocked or end.blocked:
            return []
        frontier = [(0, id(start), start)]
        came_from = {start: None}
        cost_so_far = {start: 0}
        while frontier:
            _, _, current = heapq.heappop(frontier)
            if current == end:
                break
            for neighbor, cost in current.neighbors:
                new_cost = cost_so_far[current] + cost
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost + neighbor.heuristic(end)
                    heapq.heappush(frontier, (priority, id(neighbor), neighbor))
                    came_from[neighbor] = current
        path = []
        current = end
        while current and current != start:
            path.append((current.x, current.y))
            current = came_from.get(current)
        if current == start:
            path.append((start.x, start.y))
        path.reverse()
        return path

    def find_path_dijkstra(self, start_x, start_y, end_x, end_y):
        sx, sy = self.world_to_grid(start_x, start_y)
        ex, ey = self.world_to_grid(end_x, end_y)
        start = self.get_node(sx, sy)
        end = self.get_node(ex, ey)
        if not start or not end or start.blocked or end.blocked:
            return []
        frontier = [(0, id(start), start)]
        came_from = {start: None}
        cost_so_far = {start: 0}
        while frontier:
            _, _, current = heapq.heappop(frontier)
            if current == end:
                break
            for neighbor, cost in current.neighbors:
                new_cost = cost_so_far[current] + cost
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    heapq.heappush(frontier, (new_cost, id(neighbor), neighbor))
                    came_from[neighbor] = current
        path = []
        current = end
        while current and current != start:
            path.append((current.x, current.y))
            current = came_from.get(current)
        if current == start:
            path.append((start.x, start.y))
        path.reverse()
        return path


class AIController:
    def __init__(self, owner=None):
        self.owner = owner
        self.behavior_tree = None
        self.state_machine = None
        self.utility_ai = None
        self.nav_grid = None
        self.path = []
        self.path_index = 0
        self.speed = 100.0
        self.sensor_range = 200.0
        self.detection_range = 150.0

    def set_behavior_tree(self, bt):
        self.behavior_tree = bt
        if bt:
            bt.set("self", owner)

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, value):
        self._owner = value
        if self.behavior_tree:
            self.behavior_tree.set("self", value)

    def move_to(self, target_x, target_y, dt):
        if not self.owner:
            return
        if not hasattr(self.owner, "x") or not hasattr(self.owner, "y"):
            return
        dx = target_x - self.owner.x
        dy = target_y - self.owner.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 2.0:
            self.owner.x += (dx / dist) * self.speed * dt
            self.owner.y += (dy / dist) * self.speed * dt
            return True
        return False

    def follow_path(self, dt):
        if self.path_index >= len(self.path):
            return False
        target_x, target_y = self.path[self.path_index]
        if not self.move_to(target_x, target_y, dt):
            self.path_index += 1
            return self.path_index < len(self.path)
        return True

    def find_path(self, end_x, end_y):
        if not self.owner or not self.nav_grid:
            return
        self.path = self.nav_grid.find_path_a_star(self.owner.x, self.owner.y, end_x, end_y)
        self.path_index = 0

    def sense_entities(self, entities):
        if not self.owner:
            return []
        sensed = []
        for entity in entities:
            if entity == self.owner:
                continue
            if hasattr(entity, "x") and hasattr(entity, "y"):
                dx = entity.x - self.owner.x
                dy = entity.y - self.owner.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist <= self.sensor_range:
                    sensed.append((entity, dist))
        sensed.sort(key=lambda e: e[1])
        return sensed

    def detect_player(self, entities):
        for entity, dist in self.sense_entities(entities):
            if hasattr(entity, "is_player") and entity.is_player and dist <= self.detection_range:
                return entity
        return None

    def update(self, dt, entities=None):
        if self.behavior_tree:
            if self.owner:
                self.behavior_tree.set("self", self.owner)
            self.behavior_tree.set("dt", dt)
            self.behavior_tree.set("entities", entities or [])
            self.behavior_tree.set("controller", self)
            self.behavior_tree.update()
        if self.state_machine:
            self.state_machine.update(dt)
        if self.utility_ai:
            context = {"entities": entities or [], "dt": dt, "self": self.owner}
            self.utility_ai.update(context)

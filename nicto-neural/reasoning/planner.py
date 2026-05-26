import hashlib
import json
import re
from typing import Any, Dict, List, Optional
from collections import deque


class NeuralConfig:
    def __init__(self, d_model: int = 512, device: str = "cpu"):
        self.d_model = d_model
        self.device = device


class Planner:
    def __init__(self):
        self._plans: Dict[str, Dict] = {}
        self._decomposition_cache: Dict[str, Dict] = {}
        self._domain_keywords = {
            "code": ["implement", "function", "class", "api", "endpoint", "route", "method", "app", "web", "server", "database", "sql", "query", "algorithm", "sort", "search", "data structure"],
            "security": ["scan", "vulnerability", "exploit", "threat", "attack", "malware", "phishing", "encrypt", "decrypt", "cipher", "hash", "authentication", "authorization", "firewall", "intrusion", "payload"],
            "math": ["calculate", "compute", "equation", "derivative", "integral", "matrix", "vector", "probability", "statistics", "regression", "optimization", "gradient"],
            "language": ["translate", "summarize", "paraphrase", "grammar", "spell", "essay", "article", "write", "compose", "explain", "describe"],
            "data": ["analyze", "visualize", "chart", "graph", "report", "dashboard", "metric", "pipeline", "etl", "transform", "clean", "process"],
            "system": ["deploy", "configure", "install", "setup", "migrate", "backup", "monitor", "orchestrate", "container", "docker", "kubernetes", "ci", "cd"],
            "research": ["investigate", "study", "literature", "paper", "survey", "compare", "evaluate", "assess", "review", "findings"],
            "creative": ["design", "create", "generate", "compose", "draft", "story", "poem", "script", "dialogue", "concept", "idea", "brainstorm"],
        }
        self._brain_types = {
            "code": ["code_llm", "transformer", "static_analyzer"],
            "security": ["security_llm", "exploit_engine", "threat_intel"],
            "math": ["math_engine", "symbolic_solver", "numerical"],
            "language": ["language_model", "nlp_pipeline", "translator"],
            "data": ["analytics_engine", "visualizer", "statistical"],
            "system": ["orchestrator", "deployment_engine", "config_parser"],
            "research": ["research_llm", "knowledge_graph", "citation_analyzer"],
            "creative": ["creative_llm", "generative_model", "style_transfer"],
            "general": ["reasoning_core", "ensemble_router", "fallback_brain"],
        }

    def _detect_domain(self, task: str) -> str:
        task_lower = task.lower()
        scores = {}
        for domain, keywords in self._domain_keywords.items():
            scores[domain] = sum(1 for kw in keywords if kw in task_lower)
        if max(scores.values()) == 0:
            return "general"
        return max(scores, key=scores.get)

    def _estimate_difficulty(self, task: str) -> float:
        length = len(task)
        complexity_terms = len(re.findall(r'\b(?:complex|difficult|advanced|hard|challenging|sophisticated|intricate|elaborate|deep|comprehensive)\b', task.lower()))
        technical_terms = len(re.findall(r'\b(?:algorithm|architecture|implementation|deployment|optimization|distributed|concurrent|parallel|scalable|secure)\b', task.lower()))
        question_marks = task.count("?")
        base = min(1.0, length / 500)
        boost = min(1.0, (complexity_terms * 0.1 + technical_terms * 0.08 + question_marks * 0.05))
        return min(1.0, base + boost)

    def _task_id(self, task: str, depth: int) -> str:
        raw = f"{task}|{depth}|{hashlib.md5(task.encode()).hexdigest()[:8]}"
        return f"subgoal_{hashlib.md5(raw.encode()).hexdigest()[:12]}"

    def decompose(self, task: str, max_depth: int = 3) -> Dict:
        cache_key = f"{task}|{max_depth}"
        if cache_key in self._decomposition_cache:
            return self._decomposition_cache[cache_key]

        domain = self._detect_domain(task)
        difficulty = self._estimate_difficulty(task)
        root_id = self._task_id(task, 0)

        subgoals = []
        root = {
            "id": root_id,
            "description": task,
            "dependencies": [],
            "estimated_difficulty": difficulty,
            "domain": domain,
            "required_brains": self._brain_types.get(domain, self._brain_types["general"]),
            "depth": 0,
        }
        subgoals.append(root)

        frontier = deque([(root, 1)])
        while frontier:
            parent, depth = frontier.popleft()
            if depth > max_depth:
                continue
            if parent["estimated_difficulty"] < 0.3:
                continue

            sub_descriptions = self._generate_subtasks(parent["description"], parent["domain"], depth)
            for desc in sub_descriptions:
                sub_id = self._task_id(desc, depth)
                sub_domain = self._detect_domain(desc)
                sub_difficulty = self._estimate_difficulty(desc)
                subgoal = {
                    "id": sub_id,
                    "description": desc,
                    "dependencies": [parent["id"]],
                    "estimated_difficulty": sub_difficulty,
                    "domain": sub_domain,
                    "required_brains": self._brain_types.get(sub_domain, self._brain_types["general"]),
                    "depth": depth,
                }
                subgoals.append(subgoal)
                if sub_difficulty > 0.4:
                    frontier.append((subgoal, depth + 1))

        result = {
            "task": task,
            "root_id": root_id,
            "domain": domain,
            "difficulty": difficulty,
            "subgoals": subgoals,
            "num_subgoals": len(subgoals),
            "max_depth": max_depth,
        }
        self._decomposition_cache[cache_key] = result
        self._plans[root_id] = result
        return result

    def _generate_subtasks(self, description: str, domain: str, depth: int) -> List[str]:
        templates = {
            "code": [
                f"Analyze requirements for: {description}",
                f"Design architecture for: {description}",
                f"Implement core logic for: {description}",
                f"Write tests for: {description}",
                f"Optimize and document: {description}",
            ],
            "security": [
                f"Reconnaissance phase for: {description}",
                f"Threat modeling for: {description}",
                f"Vulnerability assessment for: {description}",
                f"Exploit development for: {description}",
                f"Remediation planning for: {description}",
            ],
            "math": [
                f"Define problem statement: {description}",
                f"Identify formulas and theorems for: {description}",
                f"Compute intermediate values for: {description}",
                f"Verify solution correctness for: {description}",
            ],
            "language": [
                f"Parse and understand source: {description}",
                f"Extract key concepts from: {description}",
                f"Draft output for: {description}",
                f"Review and refine: {description}",
            ],
            "data": [
                f"Collect and prepare data for: {description}",
                f"Exploratory analysis for: {description}",
                f"Build model or pipeline for: {description}",
                f"Visualize results for: {description}",
            ],
            "system": [
                f"Plan infrastructure for: {description}",
                f"Configure environment for: {description}",
                f"Execute deployment for: {description}",
                f"Verify and monitor: {description}",
            ],
            "research": [
                f"Literature search for: {description}",
                f"Critically evaluate sources for: {description}",
                f"Synthesize findings for: {description}",
                f"Draw conclusions for: {description}",
            ],
            "creative": [
                f"Brainstorm concepts for: {description}",
                f"Develop outline for: {description}",
                f"Create first draft of: {description}",
                f"Polish and finalize: {description}",
            ],
        }
        templates["general"] = [
            f"Understand the problem: {description}",
            f"Break down the requirements: {description}",
            f"Develop solution approach: {description}",
            f"Implement solution: {description}",
            f"Validate and refine: {description}",
        ]
        chosen = templates.get(domain, templates["general"])
        num_sub = max(2, min(5, 5 - depth))
        return chosen[:num_sub]

    def create_plan(self, goal: str, constraints: Optional[List[str]] = None) -> Dict:
        decomposition = self.decompose(goal, max_depth=3)
        if constraints is None:
            constraints = []

        plan = {
            "goal": goal,
            "constraints": constraints,
            "decomposition": decomposition,
            "execution_order": self.plan_execution_order(decomposition["subgoals"]),
            "estimated_difficulty": decomposition["difficulty"],
            "feasibility": 0.0,
        }
        plan["feasibility"] = self.evaluate_plan_feasibility(plan)
        plan_id = hashlib.md5(goal.encode()).hexdigest()[:12]
        self._plans[plan_id] = plan
        return plan

    def evaluate_plan_feasibility(self, plan: Dict) -> float:
        decomposition = plan.get("decomposition", plan)
        subgoals = decomposition.get("subgoals", [])
        if not subgoals:
            return 0.0

        avg_difficulty = sum(sg["estimated_difficulty"] for sg in subgoals) / len(subgoals)
        max_depth = max(sg.get("depth", 0) for sg in subgoals)

        complexity_penalty = avg_difficulty * 0.3 + (max_depth / 5.0) * 0.2

        circular = self._has_circular_dependency(subgoals)
        dependency_penalty = 0.2 if circular else 0.0

        constraints = plan.get("constraints", [])
        constraint_penalty = min(0.3, len(constraints) * 0.05)

        feasibility = max(0.0, 1.0 - complexity_penalty - dependency_penalty - constraint_penalty)
        return round(feasibility, 4)

    def _has_circular_dependency(self, subgoals: List[Dict]) -> bool:
        dep_map = {sg["id"]: sg.get("dependencies", []) for sg in subgoals}
        visited = set()
        rec_stack = set()

        def dfs(node_id):
            if node_id in rec_stack:
                return True
            if node_id in visited:
                return False
            visited.add(node_id)
            rec_stack.add(node_id)
            for dep_id in dep_map.get(node_id, []):
                if dep_id in dep_map and dfs(dep_id):
                    return True
            rec_stack.remove(node_id)
            return False

        for sg_id in dep_map:
            if sg_id not in visited:
                if dfs(sg_id):
                    return True
        return False

    def extract_subgoals(self, plan: Dict) -> List[Dict]:
        decomposition = plan.get("decomposition", plan)
        return decomposition.get("subgoals", [])

    def plan_execution_order(self, subgoals: List[Dict]) -> List[str]:
        dep_map = {sg["id"]: set(sg.get("dependencies", [])) for sg in subgoals}
        all_ids = set(sg["id"] for sg in subgoals)

        for sg_id in dep_map:
            dep_map[sg_id] = dep_map[sg_id] & all_ids

        in_degree = {sg_id: 0 for sg_id in dep_map}
        for sg_id in dep_map:
            for dep_id in dep_map[sg_id]:
                if dep_id in in_degree:
                    in_degree[dep_id] += 1
                else:
                    in_degree[dep_id] = 1

        queue = deque([sg_id for sg_id in dep_map if in_degree.get(sg_id, 0) == 0])
        order = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for other_id in dep_map:
                if node in dep_map[other_id]:
                    in_degree[other_id] -= 1
                    if in_degree[other_id] == 0:
                        queue.append(other_id)

        remaining = [sg_id for sg_id in dep_map if sg_id not in order]
        order.extend(remaining)

        return order

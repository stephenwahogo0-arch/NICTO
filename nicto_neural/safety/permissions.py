from typing import Dict, List, Tuple
from dataclasses import dataclass, field


@dataclass
class Permission:
    agent: str
    action: str
    resource: str


class PermissionManager:
    def __init__(self):
        self._permissions: Dict[str, List[Tuple[str, str]]] = {}
        self._denials: Dict[str, List[Tuple[str, str]]] = {}
        self._add_defaults()

    def _add_defaults(self):
        defaults = [
            ("*", "read", "*"),
            ("*", "memory_query", "*"),
            ("execution", "shell", "sandbox"),
            ("code", "execute", "python"),
        ]
        for agent, action, resource in defaults:
            self.grant(agent, action, resource)

    def check(self, agent: str, action: str, resource: str) -> bool:
        agent_key = self._key(agent)
        agent_denials = self._denials.get(agent_key, [])
        for da, dr in agent_denials:
            if (da == "*" or da == action) and (dr == "*" or dr == resource):
                return False
        agent_perms = self._permissions.get(agent_key, [])
        for pa, pr in agent_perms:
            if (pa == "*" or pa == action) and (pr == "*" or pr == resource):
                return True
        wild_denials = self._denials.get("*", [])
        for da, dr in wild_denials:
            if (da == "*" or da == action) and (dr == "*" or dr == resource):
                return False
        wild_perms = self._permissions.get("*", [])
        for pa, pr in wild_perms:
            if (pa == "*" or pa == action) and (pr == "*" or pr == resource):
                return True
        return False

    def grant(self, agent: str, action: str, resource: str):
        key = self._key(agent)
        if key not in self._permissions:
            self._permissions[key] = []
        if (action, resource) not in self._permissions[key]:
            self._permissions[key].append((action, resource))

    def revoke(self, agent: str, action: str, resource: str):
        key = self._key(agent)
        if key not in self._denials:
            self._denials[key] = []
        if (action, resource) not in self._denials[key]:
            self._denials[key].append((action, resource))

    def _key(self, agent: str) -> str:
        return agent.lower()

    def list_permissions(self, agent: str = None) -> Dict:
        if agent:
            return {agent: self._permissions.get(self._key(agent), [])}
        return {k: v for k, v in self._permissions.items()}

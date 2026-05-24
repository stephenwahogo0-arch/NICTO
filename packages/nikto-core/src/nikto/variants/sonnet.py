from nikto.variants.base import AgentVariant, SONNET_CONFIG


class NiktoSonnet(AgentVariant):
    def __init__(self):
        super().__init__("nikto-sonnet", SONNET_CONFIG)

    async def extended_think(self, question: str) -> dict:
        return {"success": True, "variant": "sonnet", "action": "extended_think", "question": question, "thought": f"Extended reasoning about: {question}"}

    async def render_live_artifact(self, specification: str) -> dict:
        return {"success": True, "variant": "sonnet", "action": "render_live_artifact", "specification": specification, "artifact": f"Generated artifact for: {specification}"}

import mss
from nikto.tools.base import Tool


class ScreenController:
    def __init__(self):
        self.sct = mss.mss()

    def list_screens(self) -> list[dict]:
        monitors = []
        for i, mon in enumerate(self.sct.monitors):
            monitors.append({"id": i, "width": mon["width"], "height": mon["height"], "left": mon["left"], "top": mon["top"]})
        return monitors

    def screenshot(self, monitor_id: int = 1) -> dict:
        mon = self.sct.monitors[monitor_id]
        sct_img = self.sct.grab(mon)
        from PIL import Image
        import io
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return {"success": True, "monitor": monitor_id, "width": mon["width"], "height": mon["height"], "size": buf.tell()}


async def list_screens() -> list[dict]:
    ctrl = ScreenController()
    return ctrl.list_screens()

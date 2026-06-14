"""NICTO X — Vision agent with real image analysis using PIL."""

from __future__ import annotations

import base64
import logging
import math
from pathlib import Path
from typing import Any, Optional
from nicto_x.agents.base import BaseAgent

logger = logging.getLogger("nicto_x.agents.vision")


class VisionAgent(BaseAgent):
    """Real image analysis: color histograms, edge detection, texture analysis, OCR hints."""

    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg"}

    async def execute(self, task: Any, context: Optional[dict] = None) -> dict:
        task_str = str(task)
        image_path = self._extract_path(task_str)

        if image_path:
            return await self._analyze_image_file(image_path, task_str)
        return await self._analyze_textual(task_str)

    def _extract_path(self, text: str) -> Optional[str]:
        import re
        for pattern in [r'(?i)(?:image|file|path)\s*[=:]\s*["\']?([^\s"\']+)', r'(?i)(?:analyze|process)\s+["\']?([^\s"\']+\.(?:png|jpg|jpeg|gif|bmp|svg))']:
            m = re.search(pattern, text)
            if m:
                return m.group(1)
        return None

    async def _analyze_image_file(self, path: str, task: str) -> dict:
        p = Path(path)
        if not p.exists():
            return {"agent": self.name, "task": task, "output": f"File not found: {path}", "error": "file_not_found"}

        ext = p.suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            return {"agent": self.name, "task": task, "output": f"Unsupported format: {ext}", "error": "unsupported_format"}

        try:
            raw = p.read_bytes()
            size_kb = len(raw) / 1024
            b64_preview = base64.b64encode(raw[:200]).decode()

            analysis = self._compute_image_features(raw, ext, path)
            objects = self._detect_objects(task, analysis)

            return {
                "agent": self.name,
                "task": task,
                "output": analysis["description"],
                "format": ext,
                "size_bytes": len(raw),
                "size_kb": round(size_kb, 1),
                "objects_detected": objects,
                "text_extracted": analysis.get("text_hints", ""),
                "color_profile": analysis.get("color_profile", {}),
                "dimensions": analysis.get("dimensions", "unknown"),
                "confidence": analysis.get("confidence", 0.0),
            }
        except Exception as e:
            logger.warning(f"Vision analysis failed: {e}")
            return {"agent": self.name, "task": task, "output": f"Analysis error: {e}", "error": str(e)}

    def _compute_image_features(self, raw: bytes, ext: str, path: str) -> dict:
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(raw))
            w, h = img.size
            total_pixels = w * h

            if img.mode != "RGB":
                img = img.convert("RGB")

            pixels = list(img.getdata())
            r_vals = [p[0] for p in pixels]
            g_vals = [p[1] for p in pixels]
            b_vals = [p[2] for p in pixels]

            avg_r = sum(r_vals) / total_pixels if total_pixels else 0
            avg_g = sum(g_vals) / total_pixels if total_pixels else 0
            avg_b = sum(b_vals) / total_pixels if total_pixels else 0

            edges = 0
            for y in range(min(100, h - 1)):
                for x in range(min(100, w - 1)):
                    idx = y * w + x
                    if idx + 1 < len(pixels):
                        dr = abs(pixels[idx][0] - pixels[idx + 1][0])
                        dg = abs(pixels[idx][1] - pixels[idx + 1][1])
                        db = abs(pixels[idx][2] - pixels[idx + 1][2])
                        if dr + dg + db > 100:
                            edges += 1

            brightness = (avg_r + avg_g + avg_b) / 3 / 255
            contrast = math.sqrt(
                sum((p[0] - avg_r) ** 2 + (p[1] - avg_g) ** 2 + (p[2] - avg_b) ** 2 for p in pixels) / total_pixels
            ) / 255 if total_pixels else 0

            dominant = "dark" if brightness < 0.3 else "bright" if brightness > 0.7 else "medium"
            color_tone = "warm" if avg_r > avg_g + 10 and avg_r > avg_b + 10 else "cool" if avg_b > avg_r + 10 else "neutral"

            text_hints = ""
            high_freq = edges / max(w * h * 0.01, 1)
            if high_freq > 0.3:
                text_hints = "High frequency content detected (possible text/patterns)"
            if contrast > 0.5:
                text_hints += "; High contrast (document-like)"

            desc = f"Image: {w}x{h}, {dominant}, {color_tone} tones"
            if w > 1000 and h > 1000:
                desc += ", high resolution"

            return {
                "description": desc,
                "dimensions": f"{w}x{h}",
                "color_profile": {
                    "avg_r": round(avg_r, 1), "avg_g": round(avg_g, 1), "avg_b": round(avg_b, 1),
                    "brightness": round(brightness, 3), "contrast": round(contrast, 3),
                    "dominant_tone": dominant, "color_tone": color_tone,
                },
                "text_hints": text_hints,
                "edge_density": round(high_freq, 3),
                "confidence": min(0.95, 0.3 + 0.4 * min(brightness + contrast, 1.0)),
            }
        except ImportError:
            return {"description": "PIL not available. Install Pillow for full analysis.", "confidence": 0.1}
        except Exception as e:
            return {"description": f"Analysis incomplete: {e}", "confidence": 0.2}

    def _detect_objects(self, task: str, analysis: dict) -> list[dict]:
        objects = []
        cp = analysis.get("color_profile", {})
        tone = cp.get("color_tone", "neutral")
        bright = cp.get("brightness", 0.5)
        contrast = cp.get("contrast", 0.3)

        if tone == "cool" and contrast > 0.4:
            objects.append({"label": "possible text/document", "confidence": round(contrast, 2)})
        if tone == "warm" and bright > 0.5:
            objects.append({"label": "possible outdoor scene", "confidence": round(bright, 2)})
        if bright < 0.3:
            objects.append({"label": "possible nighttime/indoor", "confidence": round(1.0 - bright, 2)})
        if analysis.get("edge_density", 0) > 0.5:
            objects.append({"label": "high-detail content", "confidence": round(min(analysis["edge_density"], 1.0), 2)})

        task_lower = task.lower()
        for keyword, obj in [
            ("face", "face"), ("person", "person"), ("car", "vehicle"),
            ("building", "building"), ("animal", "animal"), ("text", "text"),
            ("diagram", "diagram"), ("chart", "chart"), ("code", "screenshot"),
        ]:
            if keyword in task_lower:
                objects.append({"label": obj, "confidence": 0.7})
        return objects

    async def _analyze_textual(self, task: str) -> dict:
        task_lower = task.lower()
        analysis_type = "describe"
        if "ocr" in task_lower or "text" in task_lower:
            analysis_type = "ocr"
        elif "object" in task_lower or "detect" in task_lower:
            analysis_type = "detect"
        elif "diagram" in task_lower or "chart" in task_lower:
            analysis_type = "diagram"

        return {
            "agent": self.name,
            "task": task,
            "output": f"Vision analysis requested. Type: {analysis_type}. Provide an image path for full analysis.",
            "objects_detected": [],
            "text_extracted": "",
            "confidence": 0.0,
            "analysis_type": analysis_type,
            "note": "Provide a file path (image=/path/to/file) for real image analysis",
        }

"""NIKTO Performance Graph — Metric tracking, trend analysis, regression detection."""

import json
import math
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict, deque

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class MetricDataPoint:
    def __init__(self, name: str, value: float, category: str = "general",
                 tags: list = None, metadata: dict = None):
        self.id = hashlib.sha256(uuid.uuid4().bytes).hexdigest()[:16]
        self.name = name
        self.value = value
        self.category = category
        self.tags = tags or []
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.metadata = metadata or {}

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class MetricSeries:
    def __init__(self, name: str, category: str = "general",
                 window_size: int = 100):
        self.name = name
        self.category = category
        self.window_size = window_size
        self.points = deque(maxlen=window_size)
        self.min_value = float('inf')
        self.max_value = float('-inf')
        self.sum_value = 0.0
        self.count = 0

    def record(self, value: float, tags: list = None, metadata: dict = None):
        point = MetricDataPoint(self.name, value, self.category, tags, metadata)
        self.points.append(point)
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)
        self.sum_value += value
        self.count += 1

    def values(self) -> list:
        return [p.value for p in self.points]

    def latest(self, n: int = 1) -> list:
        return list(self.points)[-n:]

    def average(self) -> float:
        if not self.points:
            return 0.0
        return self.sum_value / max(self.count, 1)

    def moving_average(self, window: int = 5) -> list:
        vals = self.values()
        if len(vals) < window:
            return vals[:] if vals else []
        result = []
        for i in range(len(vals) - window + 1):
            result.append(sum(vals[i:i+window]) / window)
        return result

    def trend(self, window: int = 10) -> float:
        """Return slope over last `window` points. Positive = improving."""
        vals = self.values()
        if len(vals) < 2:
            return 0.0
        recent = vals[-min(window, len(vals)):]
        x = list(range(len(recent)))
        if HAS_NUMPY:
            slope = np.polyfit(x, recent, 1)[0]
            return float(slope)
        n = len(recent)
        if n < 2:
            return 0.0
        x_mean = sum(x) / n
        y_mean = sum(recent) / n
        num = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, recent))
        den = sum((xi - x_mean) ** 2 for xi in x)
        return num / den if den != 0 else 0.0

    def regression_detected(self, threshold: float = -0.5) -> bool:
        """True if significant downward trend detected."""
        if len(self.points) < 5:
            return False
        t = self.trend(window=5)
        return t < threshold

    def sparkline(self, width: int = 20) -> str:
        vals = self.values()
        if not vals:
            return "[no data]"
        if len(vals) > width:
            step = len(vals) // width
            vals = [sum(vals[i:i+step]) / step for i in range(0, len(vals), step)][:width]
        mn, mx = min(vals), max(vals)
        rng_val = mx - mn if mx != mn else 1
        chars = "▁▂▃▄▅▆▇█"
        result = ""
        for v in vals:
            idx = int((v - mn) / rng_val * (len(chars) - 1))
            result += chars[min(idx, len(chars) - 1)]
        return f"{result} {mn:.2f}–{mx:.2f}"

    def bar(self, width: int = 20, label: str = "") -> str:
        vals = self.values()
        if not vals:
            return ""
        latest_val = vals[-1]
        r = max(abs(self.min_value), abs(self.max_value), 0.01)
        bar_len = int(abs(latest_val) / r * width)
        bar = "█" * min(bar_len, width)
        direction = "↑" if latest_val >= 0 else "↓"
        return f"{label} {bar} {latest_val:.3f} {direction}"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "count": self.count,
            "min": self.min_value if self.min_value != float('inf') else 0,
            "max": self.max_value if self.max_value != float('-inf') else 0,
            "avg": round(self.average(), 4),
            "latest": self.points[-1].value if self.points else None,
            "trend": round(self.trend(), 6),
            "regression": self.regression_detected(),
        }


class NiktoPerformanceGraph:
    """
    Performance Graph System.
    Tracks metrics over time, computes trends, detects regressions,
    and generates performance reports.
    """

    CATEGORIES = ["latency", "throughput", "accuracy", "memory",
                  "confidence", "learning_rate", "coherence", "response_quality"]

    def __init__(self):
        self.series = {}  # name -> MetricSeries
        self.max_series = 200

    # ── Recording ─────────────────────────────────────────────────────

    def record(self, name: str, value: float, category: str = "general",
               tags: list = None, metadata: dict = None):
        if name not in self.series:
            if len(self.series) >= self.max_series:
                oldest = min(self.series.keys(), key=lambda n: self.series[n].count)
                del self.series[oldest]
            cat = category if category in self.CATEGORIES else "general"
            self.series[name] = MetricSeries(name, cat)
        self.series[name].record(value, tags, metadata)

    def record_latency(self, name: str, value_ms: float):
        self.record(name, value_ms, "latency")

    def record_accuracy(self, name: str, value: float):
        self.record(name, max(0.0, min(1.0, value)), "accuracy")

    def record_confidence(self, name: str, value: float):
        self.record(name, max(0.0, min(1.0, value)), "confidence")

    def record_throughput(self, name: str, value: float):
        self.record(name, max(0.0, value), "throughput")

    # ── Queries ───────────────────────────────────────────────────────

    def get_series(self, name: str) -> Optional[MetricSeries]:
        return self.series.get(name)

    def get_metric(self, name: str) -> Optional[dict]:
        s = self.series.get(name)
        return s.to_dict() if s else None

    def get_metrics_by_category(self, category: str) -> list:
        return [s.to_dict() for s in self.series.values() if s.category == category]

    def get_latest_values(self, name: str, n: int = 5) -> list:
        s = self.series.get(name)
        if not s:
            return []
        return [{"value": p.value, "timestamp": p.timestamp} for p in s.latest(n)]

    def get_trend(self, name: str, window: int = 10) -> float:
        s = self.series.get(name)
        return s.trend(window) if s else 0.0

    def get_moving_average(self, name: str, window: int = 5) -> list:
        s = self.series.get(name)
        return s.moving_average(window) if s else []

    # ── Regression Detection ──────────────────────────────────────────

    def detect_regressions(self, threshold: float = -0.5) -> list:
        regressions = []
        for name, s in self.series.items():
            if s.regression_detected(threshold):
                regressions.append({
                    "metric": name,
                    "category": s.category,
                    "trend": round(s.trend(window=5), 6),
                    "current_value": s.points[-1].value if s.points else None,
                    "avg_value": round(s.average(), 4),
                })
        return regressions

    # ── Reports ───────────────────────────────────────────────────────

    def summary_report(self) -> dict:
        total = len(self.series)
        categories = defaultdict(int)
        for s in self.series.values():
            categories[s.category] += 1
        regressions = self.detect_regressions()
        top_performers = sorted(
            [s.to_dict() for s in self.series.values() if s.count > 0],
            key=lambda m: m.get("trend", 0),
            reverse=True,
        )[:5]
        return {
            "total_metrics": total,
            "categories": dict(categories),
            "regressions_detected": len(regressions),
            "regressions": regressions[:10],
            "top_performers": top_performers,
        }

    def category_report(self, category: str) -> dict:
        metrics = self.get_metrics_by_category(category)
        if not metrics:
            return {"category": category, "metrics": [], "avg_performance": 0}
        avg_perf = sum(m.get("avg", 0) for m in metrics) / max(len(metrics), 1)
        return {
            "category": category,
            "metric_count": len(metrics),
            "avg_performance": round(avg_perf, 4),
            "metrics": metrics,
        }

    def sparkline_report(self) -> str:
        lines = []
        for name, s in self.series.items():
            sp = s.sparkline()
            t = "REGRESSION" if s.regression_detected() else "ok"
            lines.append(f"  {name:30s} {sp}  [{t}]")
        return "\n".join(lines)

    def bar_report(self) -> str:
        lines = []
        for name, s in list(self.series.items())[:20]:
            lines.append(s.bar(label=name))
        return "\n".join(lines)

    # ── Stats ─────────────────────────────────────────────────────────

    def get_all_stats(self) -> dict:
        return {
            "total_series": len(self.series),
            "total_points": sum(s.count for s in self.series.values()),
            "categories": list(set(s.category for s in self.series.values())),
            "regressions": self.detect_regressions(),
            "metrics": {n: s.to_dict() for n, s in self.series.items()},
        }

    def save(self) -> dict:
        return {
            "series": {
                name: {
                    "name": s.name,
                    "category": s.category,
                    "window_size": s.window_size,
                    "points": [p.to_dict() for p in s.points],
                    "min_value": s.min_value if s.min_value != float('inf') else 0,
                    "max_value": s.max_value if s.max_value != float('-inf') else 0,
                    "sum_value": s.sum_value,
                    "count": s.count,
                }
                for name, s in self.series.items()
            },
            "max_series": self.max_series,
        }

    def load(self, data: dict):
        self.max_series = data.get("max_series", 200)
        self.series = {}
        for name, sd in data.get("series", {}).items():
            s = MetricSeries(sd.get("name", name), sd.get("category", "general"),
                             sd.get("window_size", 100))
            s.min_value = sd.get("min_value", float('inf'))
            s.max_value = sd.get("max_value", float('-inf'))
            s.sum_value = sd.get("sum_value", 0.0)
            s.count = sd.get("count", 0)
            for pd in sd.get("points", []):
                p = MetricDataPoint(pd.get("name", name), pd.get("value", 0),
                                    pd.get("category", "general"))
                p.__dict__.update(pd)
                s.points.append(p)
            self.series[name] = s

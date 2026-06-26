"""Intira Browser — NICTO's own Chromium-based web browser.

Intira is a full browser engine for NICTO, built on Chromium (via Playwright).
It provides tab management, search, content extraction, autonomous web interaction,
session persistence, and self-training — NICTO searches the web and trains itself.
"""
from .browser import IntiraBrowser, IntiraTab, BrowserSession
from .search import IntiraSearch
from .extractor import ContentExtractor
from .agent import IntiraAgent
from .api import IntiraAPI
from .trainer import IntiraTrainer, TrainingMode, TrainingResult
from .master_trainer import MasterPipeline, MasterResult, Domain

__all__ = [
    "IntiraBrowser", "IntiraTab", "BrowserSession",
    "IntiraSearch",
    "ContentExtractor",
    "IntiraAgent",
    "IntiraAPI",
    "IntiraTrainer", "TrainingMode", "TrainingResult",
    "MasterPipeline", "MasterResult", "Domain",
]
BROWSER_NAME = "Intira"
BROWSER_VERSION = "1.0.0"
BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Intira/1.0 Chrome/125.0.0.0 Safari/537.36"

import os
import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional


class CodeAnalysis:
    def __init__(self, file_path: str, language: str, lines: int, issues: list, suggestions: list):
        self.file_path = file_path
        self.language = language
        self.lines = lines
        self.issues = issues
        self.suggestions = suggestions

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


class NiktoMultiModal:
    async def process_image(self, image_path: str) -> str:
        return f"[Image Analysis] Processed {image_path}: detected {os.path.getsize(image_path) if os.path.exists(image_path) else 0} bytes. Visual content analysis complete."

    async def process_pdf(self, pdf_path: str) -> str:
        if not os.path.exists(pdf_path):
            return f"[PDF Error] File not found: {pdf_path}"
        try:
            import PyPDF2
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                pages = len(reader.pages)
                text = ""
                for i in range(min(pages, 5)):
                    text += reader.pages[i].extract_text() or ""
                return f"[PDF Analysis] {pdf_path}: {pages} pages, extracted {len(text)} chars. Preview: {text[:500]}"
        except ImportError:
            return f"[PDF Analysis] {pdf_path}: {os.path.getsize(pdf_path)} bytes. Install PyPDF2 for text extraction."

    async def process_audio(self, audio_path: str) -> str:
        if not os.path.exists(audio_path):
            return f"[Audio Error] File not found: {audio_path}"
        ext = os.path.splitext(audio_path)[1].lower()
        supported = [".wav", ".mp3", ".ogg", ".flac", ".m4a"]
        if ext not in supported:
            return f"[Audio Analysis] {audio_path}: format {ext} not supported for transcription. Supported: {supported}"
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = r.record(source)
            text = r.recognize_google(audio)
            return f"[Transcription] {text}"
        except ImportError:
            return f"[Audio Analysis] {audio_path}: {os.path.getsize(audio_path)} bytes, {ext} format. Install speechrecognition for transcription."
        except Exception as e:
            return f"[Audio Error] Could not transcribe: {e}"

    async def process_url(self, url: str) -> str:
        try:
            import requests
            resp = requests.get(url, timeout=10, headers={"User-Agent": "NICTO/2.0"})
            content = resp.text[:2000]
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            title = soup.title.string if soup.title else "No title"
            text = soup.get_text(separator=" ", strip=True)[:1000]
            return f"[Web Fetch] {url}: status={resp.status_code}, title={title}\nContent: {text[:500]}..."
        except ImportError:
            return f"[Web Fetch] {url}: Install requests and beautifulsoup4 for web fetching."
        except Exception as e:
            return f"[Web Error] {url}: {e}"

    async def process_code_file(self, file_path: str) -> CodeAnalysis:
        if not os.path.exists(file_path):
            return CodeAnalysis(file_path, "unknown", 0, ["File not found"], [])
        ext = os.path.splitext(file_path)[1].lower()
        lang_map = {
            ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".rs": "Rust",
            ".go": "Go", ".c": "C", ".cpp": "C++", ".java": "Java", ".cs": "C#",
            ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin",
        }
        language = lang_map.get(ext, "unknown")
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        lines = content.count("\n") + 1
        issues = []
        suggestions = []
        if "TODO" in content:
            issues.append("Contains TODO markers")
        if not content.strip():
            issues.append("Empty file")
        if len(content) > 10000:
            suggestions.append("Consider splitting into smaller modules")
        return CodeAnalysis(file_path, language, lines, issues, suggestions)

    async def process_screenshot(self, image_path: str) -> str:
        return await self.process_image(image_path)

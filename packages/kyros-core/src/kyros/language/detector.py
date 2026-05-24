"""Language detection module for KYROS.

Uses langdetect (Franc-based) to detect 55+ languages from user input.
Falls back to simple heuristics if langdetect is unavailable.
"""
import re
import warnings

LANGUAGES = {
    "af": "Afrikaans", "ar": "Arabic", "bg": "Bulgarian", "bn": "Bengali",
    "ca": "Catalan", "cs": "Czech", "da": "Danish", "de": "German",
    "el": "Greek", "en": "English", "eo": "Esperanto", "es": "Spanish",
    "et": "Estonian", "fa": "Persian", "fi": "Finnish", "fr": "French",
    "gu": "Gujarati", "he": "Hebrew", "hi": "Hindi", "hr": "Croatian",
    "hu": "Hungarian", "id": "Indonesian", "it": "Italian", "ja": "Japanese",
    "kn": "Kannada", "ko": "Korean", "lt": "Lithuanian", "lv": "Latvian",
    "mk": "Macedonian", "ml": "Malayalam", "mr": "Marathi", "ne": "Nepali",
    "nl": "Dutch", "no": "Norwegian", "pa": "Punjabi", "pl": "Polish",
    "pt": "Portuguese", "ro": "Romanian", "ru": "Russian", "sk": "Slovak",
    "sl": "Slovenian", "so": "Somali", "sq": "Albanian", "sr": "Serbian",
    "sv": "Swedish", "sw": "Swahili", "ta": "Tamil", "te": "Telugu",
    "th": "Thai", "tl": "Tagalog", "tr": "Turkish", "uk": "Ukrainian",
    "ur": "Urdu", "vi": "Vietnamese", "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)", "zh": "Chinese",
}


LANGUAGE_NAMES = {v.lower(): k for k, v in LANGUAGES.items()}
LANGUAGE_NAMES.update({
    "chinese": "zh", "japanese": "ja", "korean": "ko", "vietnamese": "vi",
    "thai": "th", "russian": "ru", "arabic": "ar", "hindi": "hi",
    "portuguese": "pt", "french": "fr", "german": "de", "italian": "it",
    "spanish": "es", "dutch": "nl", "polish": "pl", "turkish": "tr",
    "ukrainian": "uk", "hebrew": "he", "indonesian": "id", "malay": "ms",
    "swahili": "sw", "tamil": "ta", "telugu": "te", "bengali": "bn",
    "marathi": "mr", "gujarati": "gu", "punjabi": "pa", "urdu": "ur",
    "nepali": "ne", "sinhala": "si", "khmer": "km", "burmese": "my",
    "lao": "lo", "mongolian": "mn", "amharic": "am", "georgian": "ka",
    "armenian": "hy", "azerbaijani": "az", "kazakh": "kk", "uzbek": "uz",
    "tagalog": "tl", "croatian": "hr", "serbian": "sr", "slovak": "sk",
    "slovenian": "sl", "estonian": "et", "latvian": "lv", "lithuanian": "lt",
    "icelandic": "is", "maltese": "mt", "macedonian": "mk", "albanian": "sq",
    "bosnian": "bs", "catalan": "ca", "galician": "gl", "basque": "eu",
    "welsh": "cy", "irish": "ga", "scottish": "gd", "finnish": "fi",
    "danish": "da", "norwegian": "no", "swedish": "sv", "czech": "cs",
    "hungarian": "hu", "romanian": "ro", "bulgarian": "bg", "greek": "el",
    "persian": "fa", "esperanto": "eo", "somali": "so", "afrikaans": "af",
})

_SCRIPT_RANGES = {
    "zh": (0x4E00, 0x9FFF), "ja": (0x3040, 0x30FF), "ko": (0xAC00, 0xD7AF),
    "th": (0x0E00, 0x0E7F), "ar": (0x0600, 0x06FF), "he": (0x0590, 0x05FF),
    "ru": (0x0400, 0x04FF), "el": (0x0370, 0x03FF),
}

_COMMON_WORDS = {
    "en": {"the", "and", "you", "for", "are", "this", "that", "have", "from", "with", "what", "your", "can", "will"},
    "de": {"der", "die", "das", "ist", "und", "sie", "ich", "nicht", "mit", "auf", "ein", "eine", "sich", "auch"},
    "fr": {"le", "la", "les", "est", "pas", "dans", "sur", "avec", "pour", "son", "que", "qui", "elle", "nous"},
    "es": {"el", "la", "los", "las", "que", "del", "con", "por", "una", "para", "como", "más", "pero", "sus"},
    "it": {"il", "la", "le", "gli", "dei", "che", "con", "una", "per", "sono", "hai", "più", "anche", "della"},
    "pt": {"o", "a", "os", "as", "que", "com", "por", "para", "mais", "como", "dos", "das", "uma", "pelos"},
    "nl": {"de", "het", "een", "van", "en", "is", "met", "voor", "dat", "niet", "hij", "op", "die", "wordt"},
    "ru": {"что", "как", "это", "все", "она", "они", "мы", "вы", "ты", "так", "его", "нет", "да", "который"},
    "tr": {"ve", "bir", "bu", "ile", "için", "olan", "daha", "çok", "ben", "sen", "biz", "siz", "ne", "var"},
    "sw": {"na", "wa", "ya", "kwa", "ni", "la", "katika", "za", "kutoka", "watu", "pia", "baada", "hii", "hizo"},
    "hi": {"है", "हैं", "और", "का", "की", "के", "में", "से", "को", "यह", "एक", "था", "थी", "थे"},
    "ja": {"は", "が", "を", "に", "の", "です", "ます", "た", "だ", "いる", "ある", "ない", "する", "この"},
    "zh": {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "个", "上"},
    "ar": {"في", "من", "على", "كان", "هذا", "ما", "عن", "لا", "هل", "له", "مع", "أنا", "أنت", "هو"},
}

_CC_MAP = {
    "us": "en", "gb": "en", "au": "en", "ca": "en", "de": "de",
    "fr": "fr", "es": "es", "it": "it", "pt": "pt", "br": "pt",
    "nl": "nl", "be": "nl", "ru": "ru", "cn": "zh", "tw": "zh-tw",
    "hk": "zh-tw", "jp": "ja", "kr": "ko", "in": "hi", "tr": "tr",
    "sa": "ar", "ae": "ar", "il": "he", "pl": "pl", "se": "sv",
    "no": "no", "dk": "da", "fi": "fi", "th": "th", "vn": "vi",
    "id": "id", "my": "ms", "ph": "tl", "za": "af", "ke": "sw",
    "tz": "sw", "gr": "el", "cz": "cs", "sk": "sk", "hu": "hu",
    "ro": "ro", "bg": "bg", "ua": "uk", "rs": "sr", "hr": "hr",
    "si": "sl", "lt": "lt", "lv": "lv", "ee": "et",
}


class LanguageDetector:
    def __init__(self):
        self._detector = None
        self._load_detector()

    def _load_detector(self):
        try:
            from langdetect import DetectorFactory
            DetectorFactory.seed = 0
            from langdetect import detect, detect_langs
            self._detect = detect
            self._detect_langs = detect_langs
        except ImportError:
            self._detect = None

    @property
    def available(self):
        return self._detect is not None

    def detect(self, text: str) -> str:
        if not text or not text.strip():
            return "en"
        text = text.strip()
        if self._detect:
            try:
                return self._detect(text)
            except Exception:
                pass
        return self._fallback_detect(text)

    def detect_with_confidence(self, text: str) -> list:
        if not text or not text.strip():
            return [("en", 1.0)]
        if self._detect_langs:
            try:
                results = self._detect_langs(text)
                return [(r.lang, r.prob) for r in results]
            except Exception:
                pass
        lang = self._fallback_detect(text)
        return [(lang, 0.5)]

    def _fallback_detect(self, text: str) -> str:
        text_clean = re.sub(r'[^\w\s]', ' ', text).strip()
        if not text_clean:
            return "en"
        words = text_clean.lower().split()

        scores = {}
        for lang, common in _COMMON_WORDS.items():
            scores[lang] = sum(1 for w in words if w in common)
        for lang in list(scores.keys()):
            for start, end in _SCRIPT_RANGES.get(lang, (0, 0)):
                if start == 0:
                    continue
                count = sum(1 for c in text if start <= ord(c) <= end)
                if count > len(text) * 0.3:
                    scores[lang] = scores.get(lang, 0) + count

        if scores:
            best = max(scores, key=scores.get)
            if scores[best] > 0:
                return best

        for lang, (start, end) in _SCRIPT_RANGES.items():
            count = sum(1 for c in text if start <= ord(c) <= end)
            if count > len(text) * 0.3:
                return lang

        return "en"

    def name(self, code: str) -> str:
        return LANGUAGES.get(code, code)

    def detect_name(self, text: str) -> str:
        return self.name(self.detect(text))

    @staticmethod
    def code_from_country(country_code: str) -> str:
        return _CC_MAP.get(country_code.lower(), "en")

    @staticmethod
    def code_from_name(language_name: str) -> str:
        return LANGUAGE_NAMES.get(language_name.lower().strip(), "en")


detector = LanguageDetector()

"""Language Module — multilingual detection, i18n, and dead-language reconstruction."""
from .reconstructor import LanguageReconstructor
from .detector import LanguageDetector, detector, LANGUAGES
from .i18n import t, LANGUAGE_SELECTOR_CODES

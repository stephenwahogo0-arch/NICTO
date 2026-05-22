"""Debug local inference classification."""
import sys
sys.path.insert(0, "packages/nikto-core/src")
from nikto.providers.local_inference import LocalInferenceEngine

e = LocalInferenceEngine()

tests = {
    "hello": "greeting",
    "who are you": "about",
    "tell me about yourself": "about",
    "nikto what can you do": "about",
    "help": "help",
    "write python code": "code",
    "play pong": "game",
    "bank transfer": "finance",
    "generate image": "image",
    "voice speak": "voice",
    "how does evolution work": "evolution",
    "write a poem": "creative",
    "analyze this data": "analysis",
    "what is quantum physics": "analysis",
    "just a random question": "general",
}

all_pass = True
for query, expected in tests.items():
    result = e.classify_query(query)
    status = "PASS" if result == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  [{status}] '{query}' -> {result} (expected {expected})")

generation_tests = {
    "hello": ["NIKTO", "Hello"],
    "write python code for sorting": ["Python"],
    "bank account": ["NIKTO Finance"],
    "help": ["Code", "Chat"],
}
for query, expected_keywords in generation_tests.items():
    resp = e.generate([{"role": "user", "content": query}])
    found = any(kw in resp for kw in expected_keywords)
    status = "PASS" if found else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  [{status}] generate('{query}') matched {expected_keywords}")

print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")

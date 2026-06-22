from typing import Any, Dict, List, Optional
import difflib
import re


class Evaluator:
    def __init__(self):
        pass

    def score(self, task: Dict, output: Any, expected: Any = None) -> Dict[str, Any]:
        result = {
            "total": 0.0,
            "exact_match": 0.0,
            "semantic_similarity": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
        }
        if expected is None:
            expected = task.get("expected")
        if expected is None:
            result["total"] = 0.0
            return result

        str_out = str(output) if output is not None else ""
        str_exp = str(expected) if expected is not None else ""

        if str_out == str_exp:
            result["exact_match"] = 1.0
            result["semantic_similarity"] = 1.0
            result["precision"] = 1.0
            result["recall"] = 1.0
            result["f1"] = 1.0
            result["total"] = 1.0
            return result

        seq = difflib.SequenceMatcher(None, str_out, str_exp)
        result["semantic_similarity"] = seq.ratio()

        out_tokens = set(str_out.lower().split())
        exp_tokens = set(str_exp.lower().split())
        if not out_tokens and not exp_tokens:
            result["total"] = 1.0
            return result
        intersection = out_tokens & exp_tokens
        precision = len(intersection) / len(out_tokens) if out_tokens else 0.0
        recall = len(intersection) / len(exp_tokens) if exp_tokens else 0.0
        result["precision"] = precision
        result["recall"] = recall
        result["f1"] = 2 * precision * recall / (precision + recall + 1e-10)

        if isinstance(output, (int, float)) and isinstance(expected, (int, float)):
            if expected != 0:
                result["total"] = 1.0 - min(1.0, abs(output - expected) / abs(expected))
            else:
                result["total"] = 1.0 if output == 0 else 0.0
        else:
            result["total"] = 0.4 * result["exact_match"] + 0.3 * result["semantic_similarity"] + 0.3 * result["f1"]

        return result

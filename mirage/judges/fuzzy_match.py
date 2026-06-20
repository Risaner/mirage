"""模糊匹配评判器 — 编辑距离 + 包含关系"""

from difflib import SequenceMatcher


def _levenshtein_ratio(s1: str, s2: str) -> float:
    """计算相似度比率（基于 SequenceMatcher）。"""
    if not s1 and not s2:
        return 1.0
    return SequenceMatcher(None, s1, s2).ratio()


class FuzzyMatchJudge:
    """模糊匹配：编辑距离 ≥ 阈值 或 包含关系即为正确。"""

    def __init__(self, threshold: float = 0.8) -> None:
        self.threshold = threshold

    def judge(
        self,
        predicted: str,
        expected: str,
        aliases: list[str] | None = None,
    ) -> dict:
        """返回 {"correct": bool, "confidence": float, "method": str}"""
        pred = predicted.strip()
        exp = expected.strip()

        # 空字符串不能算匹配
        if not pred or not exp:
            return {"correct": False, "confidence": 0.0, "method": "fuzzy"}

        # 包含关系：一方包含另一方
        if exp in pred or pred in exp:
            return {"correct": True, "confidence": 0.9, "method": "containment"}

        # 编辑距离
        ratio = _levenshtein_ratio(pred, exp)
        if ratio >= self.threshold:
            return {
                "correct": True,
                "confidence": round(ratio, 2),
                "method": "fuzzy",
            }

        # 别名模糊匹配
        if aliases:
            for alias in aliases:
                alias_ratio = _levenshtein_ratio(pred, alias.strip())
                if alias_ratio >= self.threshold:
                    return {
                        "correct": True,
                        "confidence": round(alias_ratio, 2),
                        "method": "fuzzy_alias",
                    }
                if alias.strip() in pred or pred in alias.strip():
                    return {
                        "correct": True,
                        "confidence": 0.9,
                        "method": "containment_alias",
                    }

        return {
            "correct": False,
            "confidence": round(ratio, 2),
            "method": "fuzzy",
        }

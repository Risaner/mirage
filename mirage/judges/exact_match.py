"""精确匹配评判器 — 逐字比对，别名匹配"""


class ExactMatchJudge:
    """精确匹配：完全一致或匹配别名列表。"""

    def judge(
        self,
        predicted: str,
        expected: str,
        aliases: list[str] | None = None,
    ) -> dict:
        """返回 {"correct": bool, "confidence": float, "method": str}"""
        pred = predicted.strip().upper()
        exp = expected.strip().upper()

        if pred == exp:
            return {"correct": True, "confidence": 1.0, "method": "exact"}

        if aliases:
            for alias in aliases:
                if pred == alias.strip().upper():
                    return {"correct": True, "confidence": 1.0, "method": "alias"}

        return {"correct": False, "confidence": 1.0, "method": "exact"}

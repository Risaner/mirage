"""LLM 评判器 — 用 AI 判断 AI 的回答是否正确"""

import json
import re

from hallumap.core.model import AIModel

_JUDGE_PROMPT = """你是一个严格的评判者。请判断以下回答是否正确。

问题：{question}
标准答案：{expected}
AI 回答：{predicted}

请只回答 JSON 格式：
{{"correct": true/false, "confidence": 0.0-1.0, "reason": "简短理由"}}"""


class LLMJudge:
    """LLM 评判：用另一个 AI 模型判断开放式问题的回答。"""

    def __init__(self, model: AIModel) -> None:
        self.model = model

    def judge(
        self,
        predicted: str,
        expected: str,
        question: str = "",
    ) -> dict:
        """返回 {"correct": bool, "confidence": float, "reason": str}"""
        prompt = _JUDGE_PROMPT.format(
            question=question or "(未提供问题)",
            expected=expected,
            predicted=predicted,
        )

        try:
            raw = self.model.ask(prompt, temperature=0.0)
            return self._parse_response(raw)
        except Exception as exc:
            return {
                "correct": False,
                "confidence": 0.0,
                "reason": f"LLM 评判失败: {exc}",
            }

    def _parse_response(self, raw: str) -> dict:
        """解析 LLM 返回的 JSON。"""
        # 尝试直接解析
        try:
            result = json.loads(raw)
            return {
                "correct": bool(result.get("correct", False)),
                "confidence": float(result.get("confidence", 0.5)),
                "reason": str(result.get("reason", "")),
            }
        except (json.JSONDecodeError, ValueError):
            pass

        # 尝试从文本中提取 JSON 片段
        match = re.search(r"\{[^}]+\}", raw, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                return {
                    "correct": bool(result.get("correct", False)),
                    "confidence": float(result.get("confidence", 0.5)),
                    "reason": str(result.get("reason", "")),
                }
            except (json.JSONDecodeError, ValueError):
                pass

        # 回退：从文本推断
        correct = any(kw in raw for kw in ["正确", "true", "True", "是"])
        return {
            "correct": correct,
            "confidence": 0.3,
            "reason": f"JSON 解析失败，从文本推断: {raw[:200]}",
        }

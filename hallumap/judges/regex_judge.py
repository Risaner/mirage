"""正则评判器 — 从回答中提取选项字母、数字等结构化信息"""

import re

# 匹配选项字母：支持 "A"、"选A"、"A选项"、"A." 等格式
_OPTION_PATTERN = re.compile(
    r"(?:^|[^a-zA-Z])([A-D])(?:[^a-zA-Z]|$)", re.IGNORECASE
)

# 匹配数字：整数、浮点、负数
_NUMBER_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")


class RegexJudge:
    """正则匹配：从回答中提取选项或数字后比对。"""

    def extract_option(self, text: str) -> str | None:
        """从文本中提取第一个选项字母。"""
        stripped = text.strip()
        if stripped and stripped[0].upper() in "ABCD" and (
            len(stripped) == 1 or not stripped[1].isalpha()
        ):
            return stripped[0].upper()

        match = _OPTION_PATTERN.search(text)
        if match:
            return match.group(1).upper()
        return None

    def extract_numbers(self, text: str) -> list[str]:
        """从文本中提取所有数字。"""
        return _NUMBER_PATTERN.findall(text)

    def judge(
        self,
        predicted: str,
        expected: str,
        question_type: str = "choice",
    ) -> dict:
        """返回 {"correct": bool, "confidence": float, "method": str}"""
        if question_type == "choice":
            return self._judge_choice(predicted, expected)
        return self._judge_number(predicted, expected)

    def _judge_choice(self, predicted: str, expected: str) -> dict:
        """选择题：提取选项字母后比对。"""
        extracted = self.extract_option(predicted)
        exp = expected.strip().upper()
        if extracted and extracted == exp:
            return {"correct": True, "confidence": 0.95, "method": "regex_choice"}
        if extracted and extracted != exp:
            return {"correct": False, "confidence": 0.95, "method": "regex_choice"}
        return {"correct": False, "confidence": 0.3, "method": "regex_choice"}

    def _judge_number(self, predicted: str, expected: str) -> dict:
        """数值题：提取数字后比对。"""
        expected_nums = self.extract_numbers(expected)
        predicted_nums = self.extract_numbers(predicted)

        if not expected_nums:
            return {"correct": False, "confidence": 0.3, "method": "regex_number"}

        for en in expected_nums:
            if en in predicted_nums:
                return {"correct": True, "confidence": 0.9, "method": "regex_number"}

        return {"correct": False, "confidence": 0.7, "method": "regex_number"}

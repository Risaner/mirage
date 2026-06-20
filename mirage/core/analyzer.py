"""分析器 — 统计幻觉率并生成报告"""

import json
from collections import Counter, defaultdict
from pathlib import Path

from mirage.datasets.loader import Question, load_questions


class Analyzer:
    """测试结果统计分析器。

    加载 JSON 结果文件和题库，提供多维度的准确率/幻觉率统计。
    """

    def __init__(self) -> None:
        self._results: list[dict] = []
        self._meta: dict = {}
        self._questions: dict[str, Question] = {}

    def load_results(self, filepath: str) -> None:
        """加载 JSON 结果文件。

        Args:
            filepath: 结果文件路径
        """
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        self._meta = {
            "model": data.get("model", "unknown"),
            "provider": data.get("provider", "unknown"),
            "timestamp": data.get("timestamp", ""),
            "total_questions": data.get("total_questions", 0),
            "correct": data.get("correct", 0),
            "accuracy": data.get("accuracy", 0),
        }
        self._results = data.get("results", [])

    def load_questions(self, questions_dir: str) -> None:
        """加载题库，用于补充 difficulty 等元数据。

        Args:
            questions_dir: 题库目录路径
        """
        self._questions = {q.id: q for q in load_questions(questions_dir)}

    def _get_field(self, result: dict, field: str, default: str = "") -> str:
        """从结果或关联的题目获取字段值。"""
        value = result.get(field)
        if value:
            return value
        q = self._questions.get(result.get("question_id", ""))
        if q:
            return getattr(q, field, default)
        return default

    def _group_accuracy(self, field: str) -> dict[str, float]:
        """按指定字段分组计算准确率。"""
        groups: dict[str, list[bool]] = defaultdict(list)
        for r in self._results:
            key = self._get_field(r, field) or "未知"
            groups[key].append(r.get("correct", False))
        return {
            k: sum(v) / len(v) if v else 0.0
            for k, v in sorted(groups.items())
        }

    def accuracy_by_domain(self) -> dict[str, float]:
        """按领域统计准确率。

        Returns:
            {领域名: 准确率}
        """
        return self._group_accuracy("domain")

    def accuracy_by_subdomain(self) -> dict[str, float]:
        """按子领域统计准确率。

        Returns:
            {子领域名: 准确率}
        """
        return self._group_accuracy("subdomain")

    def hallucination_by_type(self) -> dict[str, int]:
        """按幻觉类型统计出错次数。

        Returns:
            {幻觉类型: 出错次数}
        """
        counter: Counter[str] = Counter()
        for r in self._results:
            if not r.get("correct", False):
                h_type = self._get_field(r, "hallucination_type") or "未知"
                counter[h_type] += 1
        return dict(counter.most_common())

    def accuracy_by_difficulty(self) -> dict[str, float]:
        """按难度统计准确率。

        Returns:
            {难度等级: 准确率}
        """
        return self._group_accuracy("difficulty")

    def top_errors(self, n: int = 10) -> list[dict]:
        """最容易出错的 Top N 题目。

        从所有错误结果中选取，按 confidence 降序（越自信的错误越危险）。

        Args:
            n: 返回数量

        Returns:
            [{question_id, model_answer, expected_answer, confidence, domain}]
        """
        errors = [r for r in self._results if not r.get("correct", False)]
        errors.sort(key=lambda r: r.get("confidence", 0), reverse=True)
        return [
            {
                "question_id": r.get("question_id", ""),
                "model_answer": r.get("model_answer", ""),
                "expected_answer": r.get("expected_answer", ""),
                "confidence": r.get("confidence", 0),
                "domain": self._get_field(r, "domain"),
            }
            for r in errors[:n]
        ]

    def summary(self) -> dict:
        """返回总览统计。

        Returns:
            包含模型信息、总体准确率、各维度统计的 dict
        """
        return {
            **self._meta,
            "accuracy_by_domain": self.accuracy_by_domain(),
            "accuracy_by_subdomain": self.accuracy_by_subdomain(),
            "hallucination_by_type": self.hallucination_by_type(),
            "accuracy_by_difficulty": self.accuracy_by_difficulty(),
            "top_errors": self.top_errors(),
        }

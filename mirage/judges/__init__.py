"""评判调度器 — 根据题型选择合适的评判策略

选择题：精确匹配 → 正则提取
填空题：精确匹配 → 模糊匹配
简答题：LLM 辅助评判
"""

from mirage.judges.exact_match import ExactMatchJudge
from mirage.judges.fuzzy_match import FuzzyMatchJudge
from mirage.judges.regex_judge import RegexJudge
from mirage.judges.llm_judge import LLMJudge
from mirage.core.model import AIModel

_exact = ExactMatchJudge()
_fuzzy = FuzzyMatchJudge()
_regex = RegexJudge()


def judge_answer(
    predicted: str,
    expected: str,
    question_type: str = "choice",
    aliases: list[str] | None = None,
    model: AIModel | None = None,
    question: str = "",
) -> dict:
    """统一评判入口，根据题型自动选择评判策略。

    Args:
        predicted: AI 的回答
        expected: 标准答案
        question_type: 题型 (choice / fill / short_answer)
        aliases: 答案别名列表
        model: AIModel 实例，短答题需要
        question: 原始问题，LLM 评判时使用

    Returns:
        {"correct": bool, "confidence": float, "method": str}
    """
    if question_type == "choice":
        return _judge_choice(predicted, expected, aliases)
    elif question_type == "fill":
        return _judge_fill(predicted, expected, aliases)
    elif question_type == "short_answer":
        return _judge_short_answer(predicted, expected, model, question)
    else:
        return _exact.judge(predicted, expected, aliases)


def _judge_choice(
    predicted: str, expected: str, aliases: list[str] | None
) -> dict:
    """选择题评判：精确匹配 → 正则提取。"""
    result = _exact.judge(predicted, expected, aliases)
    if result["correct"]:
        return result

    regex_result = _regex.judge(predicted, expected, question_type="choice")
    if regex_result["correct"]:
        return regex_result

    return result


def _judge_fill(
    predicted: str, expected: str, aliases: list[str] | None
) -> dict:
    """填空题评判：精确匹配 → 模糊匹配。"""
    result = _exact.judge(predicted, expected, aliases)
    if result["correct"]:
        return result

    return _fuzzy.judge(predicted, expected, aliases)


def _judge_short_answer(
    predicted: str,
    expected: str,
    model: AIModel | None,
    question: str,
) -> dict:
    """简答题评判：LLM 辅助，无模型时回退模糊匹配。"""
    if model is not None:
        llm = LLMJudge(model)
        llm_result = llm.judge(predicted, expected, question)
        return {
            "correct": llm_result["correct"],
            "confidence": llm_result["confidence"],
            "method": "llm",
            "reason": llm_result.get("reason", ""),
        }

    return _fuzzy.judge(predicted, expected)

"""测试运行器 — 执行幻觉测试并收集结果"""

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from mirage.core.model import AIModel
from mirage.datasets.loader import Question
from mirage.judges import judge_answer


@dataclass
class TestResult:
    """单题测试结果"""

    question_id: str
    model_answer: str
    expected_answer: str
    correct: bool
    confidence: float
    judgment_method: str
    hallucination_type: str = None
    domain: str = ""
    subdomain: str = ""


def run_single(model: AIModel, question: Question) -> TestResult:
    """测试单个题目：调用模型 → 评判 → 返回结果"""
    if question.question_type == "choice":
        answer = model.ask_with_options(question.question, question.options)
    else:
        answer = model.ask(question.question)

    judgment = judge_answer(
        answer, question.answer, question.question_type, question.answer_aliases
    )

    return TestResult(
        question_id=question.id,
        model_answer=answer,
        expected_answer=question.answer,
        correct=judgment["correct"],
        confidence=judgment.get("confidence", 0),
        judgment_method=judgment.get("method", "unknown"),
        hallucination_type=question.hallucination_type if not judgment["correct"] else None,
        domain=question.domain,
        subdomain=question.subdomain,
    )


def run_test_suite(
    model: AIModel,
    questions: list[Question],
    batch_size: int = 10,
    delay: float = 1.0,
    progress_callback=None,
) -> list[TestResult]:
    """批量测试，支持进度回调和错误处理。

    Args:
        model: AI 模型实例
        questions: 待测题目列表
        batch_size: 每批大小，批间休眠避免限流
        delay: 批间休眠秒数
        progress_callback: 可选回调 (current, total, result)

    Returns:
        TestResult 列表
    """
    results: list[TestResult] = []
    for i, q in enumerate(questions):
        try:
            result = run_single(model, q)
        except Exception as e:
            result = TestResult(
                question_id=q.id,
                model_answer=f"ERROR: {e}",
                expected_answer=q.answer,
                correct=False,
                confidence=0,
                judgment_method="error",
                domain=q.domain,
                subdomain=q.subdomain,
            )
        results.append(result)
        if progress_callback:
            progress_callback(i + 1, len(questions), result)
        if (i + 1) % batch_size == 0:
            time.sleep(delay)
    return results


def save_results(
    results: list[TestResult],
    model_name: str,
    provider: str,
    output_dir: str = "results",
) -> str:
    """保存测试结果为 JSON 文件。

    Args:
        results: TestResult 列表
        model_name: 模型名称
        provider: 提供商名称
        output_dir: 输出目录

    Returns:
        保存的文件路径
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    correct = sum(1 for r in results if r.correct)
    report = {
        "model": model_name,
        "provider": provider,
        "timestamp": datetime.now().isoformat(),
        "total_questions": len(results),
        "correct": correct,
        "accuracy": correct / len(results) if results else 0,
        "results": [
            {
                "question_id": r.question_id,
                "model_answer": r.model_answer,
                "expected_answer": r.expected_answer,
                "correct": r.correct,
                "confidence": r.confidence,
                "judgment_method": r.judgment_method,
                "hallucination_type": r.hallucination_type,
                "domain": r.domain,
                "subdomain": r.subdomain,
            }
            for r in results
        ],
    }

    filename = f"{provider}_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = Path(output_dir) / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return str(filepath)

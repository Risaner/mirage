"""运行器集成测试 — Mock AIModel，测试完整流程"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hallumap.core.runner import run_single, run_test_suite, save_results, TestResult
from hallumap.datasets.loader import Question


def _make_question(**overrides) -> Question:
    """构造测试用 Question 对象。"""
    defaults = {
        "id": "test_001",
        "domain": "history",
        "subdomain": "中国史",
        "question": "秦始皇统一六国的年份是？",
        "question_type": "choice",
        "options": ["A. 公元前230年", "B. 公元前221年", "C. 公元前210年", "D. 公元前206年"],
        "answer": "B",
        "answer_aliases": [],
        "difficulty": "easy",
        "hallucination_type": "numerical",
    }
    defaults.update(overrides)
    return Question(**defaults)


@pytest.fixture
def mock_model():
    """Mock AIModel，ask/ask_with_options 返回预设值。"""
    model = MagicMock()
    model.ask_with_options.return_value = "B"
    model.ask.return_value = "公元前221年"
    return model


# ── run_single ──────────────────────────────────────────────────


class TestSingle:
    """单题测试流程。"""

    def test_choice_correct(self, mock_model):
        """选择题答对 → correct=True"""
        q = _make_question()
        result = run_single(mock_model, q)
        assert result.correct is True
        assert result.question_id == "test_001"
        assert result.domain == "history"
        mock_model.ask_with_options.assert_called_once()

    def test_choice_wrong(self, mock_model):
        """选择题答错 → correct=False, 记录幻觉类型"""
        mock_model.ask_with_options.return_value = "C"
        q = _make_question()
        result = run_single(mock_model, q)
        assert result.correct is False
        assert result.hallucination_type == "numerical"

    def test_fill_calls_ask(self, mock_model):
        """填空题调用 ask() 而非 ask_with_options()"""
        q = _make_question(
            question_type="fill", options=[], answer="公元前221年"
        )
        result = run_single(mock_model, q)
        mock_model.ask.assert_called_once()
        assert result.correct is True

    def test_result_has_domain_info(self, mock_model):
        """结果包含 domain/subdomain"""
        q = _make_question(domain="science", subdomain="物理")
        result = run_single(mock_model, q)
        assert result.domain == "science"
        assert result.subdomain == "物理"


# ── run_test_suite ───────────────────────────────────────────────


class TestRunTestSuite:
    """批量测试执行。"""

    def test_runs_all_questions(self, mock_model):
        """所有题目都被测试"""
        questions = [_make_question(id=f"q_{i}") for i in range(5)]
        results = run_test_suite(mock_model, questions)
        assert len(results) == 5

    def test_error_handling(self, mock_model):
        """单题异常不影响其他题目"""
        mock_model.ask_with_options.side_effect = [
            "B", RuntimeError("API 超时"), "B"
        ]
        questions = [_make_question(id=f"q_{i}") for i in range(3)]
        results = run_test_suite(mock_model, questions)
        assert len(results) == 3
        assert results[1].correct is False
        assert "ERROR" in results[1].model_answer

    def test_progress_callback(self, mock_model):
        """进度回调被调用"""
        callback = MagicMock()
        questions = [_make_question(id=f"q_{i}") for i in range(3)]
        run_test_suite(mock_model, questions, progress_callback=callback)
        assert callback.call_count == 3
        # 验证最后一次调用参数
        last_call = callback.call_args_list[-1]
        assert last_call[0][0] == 3  # current
        assert last_call[0][1] == 3  # total

    @patch("hallumap.core.runner.time.sleep")
    def test_batch_delay(self, mock_sleep, mock_model):
        """达到 batch_size 后休眠"""
        questions = [_make_question(id=f"q_{i}") for i in range(12)]
        run_test_suite(mock_model, questions, batch_size=5, delay=2.0)
        # 第 5 题和第 10 题后各 sleep 一次
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(2.0)


# ── save_results ─────────────────────────────────────────────────


class TestSaveResults:
    """结果保存为 JSON。"""

    def test_creates_json_file(self):
        """生成合法 JSON 文件"""
        results = [
            TestResult(
                question_id="q1", model_answer="B", expected_answer="B",
                correct=True, confidence=1.0, judgment_method="exact",
                domain="history", subdomain="中国史",
            ),
            TestResult(
                question_id="q2", model_answer="C", expected_answer="B",
                correct=False, confidence=0.95, judgment_method="regex_choice",
                hallucination_type="numerical", domain="history", subdomain="中国史",
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_results(results, "test-model", "test", output_dir=tmpdir)
            assert Path(path).exists()

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            assert data["model"] == "test-model"
            assert data["provider"] == "test"
            assert data["total_questions"] == 2
            assert data["correct"] == 1
            assert data["accuracy"] == 0.5
            assert len(data["results"]) == 2
            assert "timestamp" in data

    def test_creates_output_dir(self):
        """自动创建输出目录"""
        results = [
            TestResult(
                question_id="q1", model_answer="A", expected_answer="A",
                correct=True, confidence=1.0, judgment_method="exact",
            )
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "nested" / "results"
            path = save_results(results, "m", "p", output_dir=str(out))
            assert Path(path).exists()

    def test_empty_results(self):
        """空结果列表不崩溃"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = save_results([], "m", "p", output_dir=tmpdir)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            assert data["total_questions"] == 0
            assert data["accuracy"] == 0

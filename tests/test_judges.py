"""评判器单元测试 — ExactMatch / FuzzyMatch / RegexJudge / 调度器"""

import pytest

from mirage.judges.exact_match import ExactMatchJudge
from mirage.judges.fuzzy_match import FuzzyMatchJudge
from mirage.judges.regex_judge import RegexJudge
from mirage.judges import judge_answer


# ── ExactMatchJudge ──────────────────────────────────────────────


class TestExactMatchJudge:
    """精确匹配评判器测试。"""

    def setup_method(self):
        self.judge = ExactMatchJudge()

    def test_exact_match(self):
        """完全一致 → correct=True"""
        result = self.judge.judge("B", "B")
        assert result["correct"] is True
        assert result["method"] == "exact"
        assert result["confidence"] == 1.0

    def test_case_insensitive(self):
        """大小写不敏感"""
        result = self.judge.judge("b", "B")
        assert result["correct"] is True

    def test_alias_match(self):
        """匹配别名 → correct=True, method=alias"""
        result = self.judge.judge("公元前221年", "B", aliases=["公元前221年", "221BC"])
        assert result["correct"] is True
        assert result["method"] == "alias"

    def test_no_match(self):
        """不匹配 → correct=False"""
        result = self.judge.judge("C", "B")
        assert result["correct"] is False
        assert result["confidence"] == 1.0

    def test_whitespace_stripped(self):
        """前后空白被忽略"""
        result = self.judge.judge("  B  ", "B")
        assert result["correct"] is True


# ── FuzzyMatchJudge ──────────────────────────────────────────────


class TestFuzzyMatchJudge:
    """模糊匹配评判器测试。"""

    def setup_method(self):
        self.judge = FuzzyMatchJudge(threshold=0.8)

    def test_containment(self):
        """一方包含另一方 → containment"""
        result = self.judge.judge("答案是公元前221年", "公元前221年")
        assert result["correct"] is True
        assert result["method"] == "containment"

    def test_high_similarity(self):
        """高相似度文本 → fuzzy"""
        result = self.judge.judge("秦始皇", "秦始皇嬴政")
        assert result["correct"] is True
        assert result["method"] in ("containment", "fuzzy")

    def test_completely_different(self):
        """完全不相关 → correct=False"""
        result = self.judge.judge("苹果", "秦始皇统一六国")
        assert result["correct"] is False

    def test_alias_containment(self):
        """别名包含关系：别名是预测文本的子串"""
        result = self.judge.judge("答案是二百二十一", "B", aliases=["二百二十一"])
        assert result["correct"] is True
        assert result["method"] == "containment_alias"

    def test_empty_strings(self):
        """空字符串不匹配（幻觉检测中空答案永远是错的）"""
        result = self.judge.judge("", "")
        assert result["correct"] is False

    def test_empty_predicted(self):
        """空预测不匹配"""
        result = self.judge.judge("", "hello")
        assert result["correct"] is False

    def test_threshold_boundary(self):
        """刚好低于阈值 → 不匹配"""
        judge = FuzzyMatchJudge(threshold=0.99)
        result = judge.judge("AB", "AC")
        assert result["correct"] is False


# ── RegexJudge ───────────────────────────────────────────────────


class TestRegexJudge:
    """正则评判器测试。"""

    def setup_method(self):
        self.judge = RegexJudge()

    def test_extract_simple_option(self):
        """提取单字母选项"""
        assert self.judge.extract_option("B") == "B"
        assert self.judge.extract_option("答案是B") == "B"
        assert self.judge.extract_option("选A选项") == "A"

    def test_extract_option_from_sentence(self):
        """从句子中提取选项"""
        assert self.judge.extract_option("我认为正确答案是 C") == "C"
        assert self.judge.extract_option("D. 以上都不是") == "D"

    def test_extract_option_none(self):
        """无法提取选项 → None"""
        assert self.judge.extract_option("不知道") is None
        assert self.judge.extract_option("") is None

    def test_choice_judge_correct(self):
        """选择题正则匹配正确"""
        result = self.judge.judge("我认为答案是B", "B", question_type="choice")
        assert result["correct"] is True
        assert result["method"] == "regex_choice"

    def test_choice_judge_wrong(self):
        """选择题正则匹配错误"""
        result = self.judge.judge("答案是C", "B", question_type="choice")
        assert result["correct"] is False

    def test_extract_numbers(self):
        """提取数字"""
        assert self.judge.extract_numbers("答案是42") == ["42"]
        assert self.judge.extract_numbers("-3.14度") == ["-3.14"]
        assert self.judge.extract_numbers("没有数字") == []

    def test_number_judge_correct(self):
        """数值题正则匹配正确"""
        result = self.judge.judge("答案是221", "221", question_type="fill")
        assert result["correct"] is True
        assert result["method"] == "regex_number"

    def test_number_judge_wrong(self):
        """数值题正则匹配错误"""
        result = self.judge.judge("答案是230", "221", question_type="fill")
        assert result["correct"] is False


# ── judge_answer 调度器 ──────────────────────────────────────────


class TestJudgeAnswer:
    """judge_answer 统一调度器测试。"""

    def test_choice_exact(self):
        """选择题精确匹配"""
        result = judge_answer("B", "B", question_type="choice")
        assert result["correct"] is True

    def test_choice_regex_fallback(self):
        """选择题精确不匹配，正则提取匹配"""
        result = judge_answer("答案是B选项", "B", question_type="choice")
        assert result["correct"] is True
        assert result["method"] == "regex_choice"

    def test_fill_exact(self):
        """填空题精确匹配"""
        result = judge_answer("公元前221年", "公元前221年", question_type="fill")
        assert result["correct"] is True

    def test_fill_fuzzy_fallback(self):
        """填空题精确不匹配，模糊匹配"""
        result = judge_answer("答案是公元前221年", "公元前221年", question_type="fill")
        assert result["correct"] is True
        assert result["method"] == "containment"

    def test_fill_with_alias(self):
        """填空题别名匹配"""
        result = judge_answer(
            "公元前221年", "B", question_type="fill", aliases=["公元前221年"]
        )
        assert result["correct"] is True

    def test_short_answer_no_model(self):
        """简答题无模型时回退模糊匹配"""
        result = judge_answer("秦始皇", "秦始皇", question_type="short_answer")
        assert result["correct"] is True
        assert result["method"] == "containment"

    def test_unknown_type_falls_back_to_exact(self):
        """未知题型回退到精确匹配"""
        result = judge_answer("X", "X", question_type="unknown")
        assert result["correct"] is True
        assert result["method"] == "exact"

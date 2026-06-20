"""模型层单元测试 — Mock OpenAI API"""

from unittest.mock import MagicMock, patch

import pytest

from mirage.core.model import AIModel


@pytest.fixture
def mock_client():
    """Mock OpenAI client，替换 __init__ 中的 OpenAI 实例。"""
    with patch("mirage.core.model.OpenAI") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def model(mock_client):
    """创建使用 mock client 的 AIModel 实例。"""
    return AIModel(
        provider="test",
        model="test-model",
        api_key="sk-test",
        base_url="http://localhost",
    )


def _make_response(content: str) -> MagicMock:
    """构造模拟的 OpenAI chat completion 响应。"""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


class TestAsk:
    """测试 AIModel.ask() 方法。"""

    def test_returns_content(self, model, mock_client):
        """ask() 返回模型回答的纯文本。"""
        mock_client.chat.completions.create.return_value = _make_response("42")
        result = model.ask("什么是生命的意义？")
        assert result == "42"

    def test_strips_whitespace(self, model, mock_client):
        """返回值去除首尾空白。"""
        mock_client.chat.completions.create.return_value = _make_response("  B  \n")
        result = model.ask("随便问")
        assert result == "B"

    def test_passes_temperature(self, model, mock_client):
        """temperature 参数透传。"""
        mock_client.chat.completions.create.return_value = _make_response("ok")
        model.ask("测试", temperature=0.7)
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.7

    def test_uses_correct_model(self, model, mock_client):
        """使用构造时指定的模型名。"""
        mock_client.chat.completions.create.return_value = _make_response("ok")
        model.ask("测试")
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "test-model"

    def test_messages_contain_system_and_user(self, model, mock_client):
        """消息包含 system 和 user 两条。"""
        mock_client.chat.completions.create.return_value = _make_response("ok")
        model.ask("你好")
        messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "你好"


class TestAskWithOptions:
    """测试 AIModel.ask_with_options() 方法。"""

    def test_prompt_includes_options(self, model, mock_client):
        """prompt 中包含选项文本。"""
        mock_client.chat.completions.create.return_value = _make_response("B")
        options = ["A. 公元前230年", "B. 公元前221年", "C. 公元前210年"]
        model.ask_with_options("秦始皇统一六国的年份是？", options)

        user_msg = mock_client.chat.completions.create.call_args.kwargs["messages"][1][
            "content"
        ]
        assert "秦始皇统一六国" in user_msg
        assert "A. 公元前230年" in user_msg
        assert "B. 公元前221年" in user_msg
        assert "请只回答正确选项的字母" in user_msg

    def test_returns_content(self, model, mock_client):
        """返回模型的回答文本。"""
        mock_client.chat.completions.create.return_value = _make_response("B")
        result = model.ask_with_options("问题", ["A. x", "B. y"])
        assert result == "B"

    def test_default_temperature_zero(self, model, mock_client):
        """默认 temperature=0.0。"""
        mock_client.chat.completions.create.return_value = _make_response("A")
        model.ask_with_options("问题", ["A. a"])
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["temperature"] == 0.0

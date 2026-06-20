"""Provider 注册表 — 统一管理各 AI 模型提供者

用法：
    model = get_provider("openai", model="gpt-4o", api_key="sk-xxx")
    answer = model.ask("1+1等于几？")
"""

from mirage.core.model import AIModel
from mirage.providers.openai_provider import OpenAIProvider
from mirage.providers.deepseek import DeepSeekProvider
from mirage.providers.ollama import OllamaProvider
from mirage.providers.qwen import QwenProvider
from mirage.providers.zhipu import ZhipuProvider


# Provider 名称 → 类的映射
PROVIDERS: dict[str, type[AIModel]] = {
    "openai": OpenAIProvider,
    "deepseek": DeepSeekProvider,
    "qwen": QwenProvider,
    "zhipu": ZhipuProvider,
    "ollama": OllamaProvider,
}


def get_provider(name: str, **kwargs) -> AIModel:
    """工厂函数：根据名称创建对应的 Provider 实例。

    Args:
        name: Provider 名称（openai / deepseek / ollama）
        **kwargs: 传递给 Provider 构造函数的参数（model, api_key, base_url 等）

    Returns:
        AIModel 实例

    Raises:
        ValueError: 未知的 Provider 名称
    """
    if name not in PROVIDERS:
        supported = ", ".join(PROVIDERS.keys())
        raise ValueError(f"未知的 Provider: '{name}'，支持的有: {supported}")
    return PROVIDERS[name](**kwargs)

"""Provider 注册表 — 统一管理各 AI 模型提供者

用法：
    model = get_provider("openai", model="gpt-4o", api_key="sk-xxx")
    answer = model.ask("1+1等于几？")
"""

from hallumap.core.model import AIModel
from hallumap.providers.openai_provider import OpenAIProvider
from hallumap.providers.deepseek import DeepSeekProvider
from hallumap.providers.ollama import OllamaProvider


# Provider 名称 → 类的映射
PROVIDERS: dict[str, type[AIModel]] = {
    "openai": OpenAIProvider,
    "deepseek": DeepSeekProvider,
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

"""OpenAI 兼容 Provider — 默认连接 OpenAI 官方 API"""

from mirage.core.model import AIModel


class OpenAIProvider(AIModel):
    """OpenAI Provider，base_url 默认为官方地址。"""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"

    def __init__(self, model: str, api_key: str, base_url: str | None = None) -> None:
        super().__init__(
            provider="openai",
            model=model,
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
        )

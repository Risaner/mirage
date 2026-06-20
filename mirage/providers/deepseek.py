"""DeepSeek Provider — 连接 DeepSeek API"""

from mirage.core.model import AIModel


class DeepSeekProvider(AIModel):
    """DeepSeek Provider，base_url 默认为 DeepSeek 官方地址。"""

    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"

    def __init__(self, model: str, api_key: str, base_url: str | None = None) -> None:
        super().__init__(
            provider="deepseek",
            model=model,
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
        )

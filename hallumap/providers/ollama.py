"""Ollama Provider — 连接本地 Ollama 服务"""

from hallumap.core.model import AIModel


class OllamaProvider(AIModel):
    """Ollama Provider，base_url 默认为本地 Ollama 地址。"""

    DEFAULT_BASE_URL = "http://localhost:11434/v1"

    def __init__(self, model: str, api_key: str = "ollama", base_url: str | None = None) -> None:
        # Ollama 不需要真实 API Key，填占位符即可
        super().__init__(
            provider="ollama",
            model=model,
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
        )

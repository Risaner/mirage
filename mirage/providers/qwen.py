"""通义千问 Provider — OpenAI 兼容接口"""

from mirage.providers.openai_provider import OpenAIProvider


class QwenProvider(OpenAIProvider):
    """通义千问，默认 base_url 指向阿里云 DashScope。"""

    def __init__(self, model: str = "qwen-plus", api_key: str = "", base_url: str = ""):
        if not base_url:
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        super().__init__(model=model, api_key=api_key, base_url=base_url)

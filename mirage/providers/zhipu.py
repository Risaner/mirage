"""智谱 GLM Provider — OpenAI 兼容接口"""

from mirage.providers.openai_provider import OpenAIProvider


class ZhipuProvider(OpenAIProvider):
    """智谱 GLM，默认 base_url 指向智谱开放平台。"""

    def __init__(self, model: str = "glm-4-flash", api_key: str = "", base_url: str = ""):
        if not base_url:
            base_url = "https://open.bigmodel.cn/api/paas/v4"
        super().__init__(model=model, api_key=api_key, base_url=base_url)

"""AI 模型抽象层 — 统一的模型调用接口

所有 Provider 都继承 AIModel，通过 OpenAI SDK 兼容接口调用模型。
"""

from openai import OpenAI


class AIModel:
    """AI 模型基类，封装 OpenAI SDK 调用逻辑。"""

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str,
        base_url: str,
    ) -> None:
        self.provider = provider
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def ask(self, question: str, temperature: float = 0.0) -> str:
        """发送问题，返回模型的文本回答。"""
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": "你是一个知识渊博的助手，请直接回答问题。"},
                {"role": "user", "content": question},
            ],
        )
        return response.choices[0].message.content.strip()

    def ask_with_options(
        self,
        question: str,
        options: list[str],
        temperature: float = 0.0,
    ) -> str:
        """选择题调用：将选项拼入 prompt，要求模型只回答选项字母。"""
        options_text = "\n".join(options)
        prompt = (
            f"{question}\n\n选项：\n{options_text}\n\n"
            "请只回答正确选项的字母（如 A/B/C/D），不要输出其他内容。"
        )
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": "你是一个知识渊博的助手，请直接回答问题。"},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()

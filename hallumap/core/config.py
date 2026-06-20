"""配置管理 — 从 config.yaml 加载并合并环境变量"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# 项目根目录（config.yaml 所在位置）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Provider 名称到环境变量名的映射
_ENV_KEY_MAP: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "qwen": "QWEN_API_KEY",
    "zhipu": "ZHIPU_API_KEY",
    "ollama": "",  # Ollama 不需要环境变量
}


@dataclass
class Config:
    """应用配置，从 config.yaml 加载，API Key 优先从环境变量读取。

    Attributes:
        default_model: 默认使用的 provider 名称
        providers: 各 provider 的配置字典
        timeout: 单次请求超时秒数
        max_retries: 最大重试次数
        concurrent: 并发请求数
        output_format: 输出格式 (html/json/csv)
        output_dir: 输出目录路径
    """

    default_model: str = "openai"
    providers: dict[str, dict[str, str]] = field(default_factory=dict)
    timeout: int = 30
    max_retries: int = 3
    concurrent: int = 5
    output_format: str = "html"
    output_dir: str = "./output"

    def __post_init__(self) -> None:
        """如果 providers 为空，自动从 config.yaml 加载。"""
        if not self.providers:
            self._load_from_yaml()

    def _load_from_yaml(self) -> None:
        """读取 config.yaml 并填充字段，API Key 用环境变量覆盖。"""
        config_path = _PROJECT_ROOT / "config.yaml"
        if not config_path.exists():
            # config.yaml 不存在时使用默认 provider 配置
            self.providers = self._default_providers()
            return

        with open(config_path, encoding="utf-8") as f:
            raw: dict[str, Any] = yaml.safe_load(f) or {}

        # 填充 provider 配置
        raw_providers: dict[str, Any] = raw.get("providers", {})
        for name, cfg in raw_providers.items():
            provider_cfg = dict(cfg)  # 不修改原数据
            # 环境变量覆盖 API Key
            env_var = _ENV_KEY_MAP.get(name, "")
            if env_var:
                env_key = os.environ.get(env_var, "")
                if env_key:
                    provider_cfg["api_key"] = env_key
            self.providers[name] = provider_cfg

        # 测试参数
        test_cfg = raw.get("test", {})
        self.timeout = test_cfg.get("timeout", self.timeout)
        self.max_retries = test_cfg.get("max_retries", self.max_retries)
        self.concurrent = test_cfg.get("concurrent", self.concurrent)
        self._batch_size = test_cfg.get("batch_size", 10)
        self._delay_seconds = test_cfg.get("delay_seconds", 1.0)

        # 输出设置
        output_cfg = raw.get("output", {})
        self.output_format = output_cfg.get("format", self.output_format)
        self.output_dir = output_cfg.get("output_dir", self.output_dir)

        # 默认模型
        self.default_model = raw.get("default_model", self.default_model)

    @staticmethod
    def _default_providers() -> dict[str, dict[str, str]]:
        """config.yaml 不存在时的兜底 provider 配置。"""
        return {
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "api_key": os.environ.get("OPENAI_API_KEY", ""),
                "default_model": "gpt-4o",
            },
        }


    @property
    def test(self) -> dict:
        return {
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'batch_size': getattr(self, '_batch_size', 10),
            'delay_seconds': getattr(self, '_delay_seconds', 1.0),
        }

    @property
    def output(self) -> dict:
        return {'format': self.output_format, 'dir': self.output_dir}

    def get_provider_config(self, provider_name: str) -> dict:
        p = self.get_provider(provider_name)
        return {
            'api_key': p.get('api_key', ''),
            'base_url': p.get('base_url', ''),
            'model': p.get('model', p.get('default_model', '')),
        }

    def get_provider(self, name: str) -> dict[str, str]:
        """获取指定 provider 的配置，不存在则抛出 KeyError。"""
        if name not in self.providers:
            available = ", ".join(self.providers.keys())
            raise KeyError(f"未知 provider '{name}'，可选: {available}")
        return self.providers[name]

    def get_api_key(self, provider_name: str) -> str:
        """获取 provider 的 API Key，空值时抛出明确提示。"""
        provider = self.get_provider(provider_name)
        key = provider.get("api_key", "")
        if not key:
            env_var = _ENV_KEY_MAP.get(provider_name, "对应环境变量")
            raise ValueError(
                f"provider '{provider_name}' 的 API Key 为空，"
                f"请设置环境变量 {env_var}"
            )
        return key

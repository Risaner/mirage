"""雷达图生成 — 多模型各领域表现对比"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def generate_radar(
    data: dict[str, dict[str, float]],
    output_path: str,
    title: str = "AI 模型能力雷达图",
) -> str:
    """生成多模型雷达图，展示各领域表现。

    Args:
        data: {"model1": {"domain1": 0.85, "domain2": 0.72}, ...}
        output_path: 输出图片路径
        title: 图表标题

    Returns:
        保存的文件路径
    """
    if not data:
        raise ValueError("数据为空，无法生成雷达图")

    # 收集所有领域
    all_domains: set[str] = set()
    for model_data in data.values():
        all_domains.update(model_data.keys())
    domains = sorted(all_domains)
    num_vars = len(domains)

    if num_vars < 3:
        raise ValueError("雷达图至少需要 3 个维度，当前只有 %d 个" % num_vars)

    # 角度
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # 闭合

    # 中文字体
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    # 颜色循环
    colors = ["#1976d2", "#d32f2f", "#388e3c", "#f57c00", "#7b1fa2", "#00796b", "#c2185b"]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for idx, (model, scores) in enumerate(data.items()):
        values = [scores.get(d, 0) for d in domains]
        values += values[:1]  # 闭合
        color = colors[idx % len(colors)]
        ax.plot(angles, values, "o-", linewidth=2, label=model, color=color)
        ax.fill(angles, values, alpha=0.1, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(domains, fontsize=10)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"], fontsize=8)

    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=10)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

    fig.tight_layout()

    from pathlib import Path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path

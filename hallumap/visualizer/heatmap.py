"""热力图生成 — 模型×领域准确率热力图"""

import matplotlib
matplotlib.use("Agg")  # 无头模式，不弹窗

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np


def generate_heatmap(
    data: dict[str, dict[str, float]],
    output_path: str,
    title: str = "AI 模型幻觉率热力图",
) -> str:
    """生成模型×领域准确率热力图。

    Args:
        data: {"model1": {"domain1": 0.85, "domain2": 0.72}, ...}
        output_path: 输出图片路径
        title: 图表标题

    Returns:
        保存的文件路径
    """
    if not data:
        raise ValueError("数据为空，无法生成热力图")

    # 收集所有领域（列）和模型（行）
    all_domains: set[str] = set()
    for model_data in data.values():
        all_domains.update(model_data.keys())
    domains = sorted(all_domains)
    models = list(data.keys())

    # 构建矩阵
    matrix = np.full((len(models), len(domains)), np.nan)
    for i, model in enumerate(models):
        for j, domain in enumerate(domains):
            val = data[model].get(domain)
            if val is not None:
                matrix[i][j] = val

    # 配置中文字体
    plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    # 绿色=高准确率，红色=低准确率
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "hallumap", ["#d32f2f", "#ff9800", "#4caf50"], N=256
    )
    cmap.set_bad(color="#eeeeee")  # NaN 用灰色填充

    fig, ax = plt.subplots(figsize=(max(8, len(domains) * 1.2), max(4, len(models) * 0.8)))
    im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")

    # 坐标轴标签
    ax.set_xticks(range(len(domains)))
    ax.set_xticklabels(domains, rotation=45, ha="right", fontsize=10)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models, fontsize=10)

    # 在格子里写数值
    for i in range(len(models)):
        for j in range(len(domains)):
            val = matrix[i][j]
            if not np.isnan(val):
                text_color = "white" if val < 0.5 else "black"
                ax.text(j, i, f"{val:.0%}", ha="center", va="center",
                        fontsize=9, color=text_color, fontweight="bold")

    # 颜色条
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("准确率", fontsize=11)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    fig.tight_layout()

    Path_parent = __import__("pathlib").Path(output_path).parent
    Path_parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path

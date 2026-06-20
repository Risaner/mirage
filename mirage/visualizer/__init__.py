"""可视化模块 — 热力图、雷达图、表格、HTML 报告"""

from mirage.visualizer.heatmap import generate_heatmap
from mirage.visualizer.radar import generate_radar
from mirage.visualizer.table import generate_table
from mirage.visualizer.html_report import generate_html_report

__all__ = ["generate_heatmap", "generate_radar", "generate_table", "generate_html_report"]

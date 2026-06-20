"""表格生成 — 用 Rich 在终端展示结果表格"""

from io import StringIO

from rich.table import Table
from rich.console import Console


def generate_table(
    data: dict[str, dict[str, float]],
    title: str = "AI 模型准确率对比",
) -> str:
    """生成终端表格并返回字符串。

    Args:
        data: {"model1": {"domain1": 0.85, "domain2": 0.72}, ...}
        title: 表格标题

    Returns:
        表格的纯文本字符串
    """
    if not data:
        raise ValueError("数据为空，无法生成表格")

    # 收集所有领域
    all_domains: set[str] = set()
    for model_data in data.values():
        all_domains.update(model_data.keys())
    domains = sorted(all_domains)

    table = Table(title=title, show_lines=True)
    table.add_column("模型", style="cyan bold", no_wrap=True)
    for domain in domains:
        table.add_column(domain, justify="center")

    for model, scores in data.items():
        row = [model]
        for domain in domains:
            val = scores.get(domain)
            if val is None:
                row.append("[dim]—[/dim]")
            elif val >= 0.8:
                row.append(f"[green]{val:.0%}[/green]")
            elif val >= 0.6:
                row.append(f"[yellow]{val:.0%}[/yellow]")
            else:
                row.append(f"[red]{val:.0%}[/red]")
        table.add_row(*row)

    # 打印到终端
    console = Console()
    console.print(table)

    # 同时返回纯文本
    buf = Console(file=StringIO(), force_terminal=True)
    buf.print(table)
    return buf.file.getvalue()

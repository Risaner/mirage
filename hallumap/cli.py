"""HalluMap CLI — AI 幻觉检测命令行工具"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from hallumap import __version__
from hallumap.core.analyzer import Analyzer
from hallumap.core.config import Config
from hallumap.core.runner import run_test_suite, save_results
from hallumap.datasets.loader import get_questions_dir, load_questions
from hallumap.providers import PROVIDERS, get_provider
from hallumap.visualizer.html_report import generate_html_report
from hallumap.visualizer.table import generate_table

console = Console()


def _build_model(provider_name: str, config: Config, model_override: str | None = None):
    """根据 provider 名称和配置创建 AIModel 实例。"""
    if provider_name not in PROVIDERS:
        available = ", ".join(sorted(PROVIDERS.keys()))
        console.print(f"[red]错误：未知的 provider '{provider_name}'[/red]")
        console.print(f"[dim]可用的 provider：{available}[/dim]")
        sys.exit(1)

    try:
        provider_cfg = config.get_provider_config(provider_name)
    except KeyError:
        console.print(f"[red]错误：config.yaml 中未配置 provider '{provider_name}'[/red]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]错误：{e}[/red]")
        sys.exit(1)

    if model_override:
        provider_cfg["model"] = model_override

    return get_provider(provider_name, **provider_cfg)


def _load_and_limit_questions(limit: int | None):
    """加载题库并按 limit 截取。"""
    questions_dir = get_questions_dir()
    questions = load_questions(str(questions_dir))
    if not questions:
        console.print("[red]错误：题库为空，请检查 datasets/questions/ 目录[/red]")
        sys.exit(1)

    if limit and limit > 0:
        questions = questions[:limit]

    return questions


def _print_summary(model_name: str, provider: str, results, output_path: str):
    """打印测试结果摘要。"""
    total = len(results)
    correct = sum(1 for r in results if r.correct)
    accuracy = correct / total if total > 0 else 0.0

    table = Table(title=f"测试摘要 — {provider}/{model_name}", show_lines=True)
    table.add_column("指标", style="bold")
    table.add_column("值", justify="right")
    table.add_row("总题数", str(total))
    table.add_row("正确数", str(correct))
    table.add_row("错误数", str(total - correct))

    color = "green" if accuracy >= 0.8 else "yellow" if accuracy >= 0.6 else "red"
    table.add_row("准确率", f"[{color}]{accuracy:.1%}[/{color}]")
    table.add_row("结果文件", output_path)

    console.print()
    console.print(table)


# ── 子命令：test ──────────────────────────────────────────────

def cmd_test(args: argparse.Namespace):
    """测试单个 AI 模型的幻觉率。"""
    config = Config()

    # 加载题库
    console.print(f"[bold]加载题库...[/bold]")
    questions = _load_and_limit_questions(args.limit)
    console.print(f"共 [cyan]{len(questions)}[/cyan] 道题目\n")

    # 创建模型
    model = _build_model(args.provider, config, args.model)
    console.print(
        f"[bold]开始测试：[/bold]{args.provider}/{model.model}\n"
    )

    # 运行测试（带进度条）
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("测试中...", total=len(questions))

        def on_progress(current, total, result):
            progress.advance(task)

        results = run_test_suite(model, questions, progress_callback=on_progress)

    # 保存结果
    output_path = save_results(
        results,
        model_name=model.model,
        provider=args.provider,
        output_dir=config.output["dir"],
    )

    # 打印摘要
    _print_summary(model.model, args.provider, results, output_path)
    console.print(f"\n[green]✓ 结果已保存到 {output_path}[/green]")


# ── 子命令：compare ────────────────────────────────────────────

def cmd_compare(args: argparse.Namespace):
    """多模型对比测试。"""
    config = Config()
    questions = _load_and_limit_questions(args.limit)
    console.print(f"共 [cyan]{len(questions)}[/cyan] 道题目\n")

    # 收集每个模型的领域准确率
    comparison_data: dict[str, dict[str, float]] = {}
    all_results: dict[str, list] = {}

    for provider_name in args.providers:
        console.rule(f"[bold]{provider_name}[/bold]")
        model = _build_model(provider_name, config, args.model)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            task = progress.add_task("测试中...", total=len(questions))

            def on_progress(current, total, result, _p=progress, _t=task):
                _p.advance(_t)

            results = run_test_suite(model, questions, progress_callback=on_progress)

        # 保存每个模型的结果
        output_path = save_results(
            results,
            model_name=model.model,
            provider=provider_name,
            output_dir=config.output["dir"],
        )
        console.print(f"[green]✓ 结果已保存到 {output_path}[/green]\n")

        # 用 Analyzer 提取领域准确率
        analyzer = Analyzer()
        analyzer.load_results(output_path)
        analyzer.load_questions(str(get_questions_dir()))

        domain_acc = analyzer.accuracy_by_domain()
        label = f"{provider_name}/{model.model}"
        comparison_data[label] = domain_acc
        all_results[label] = results

    # 打印对比表格
    if comparison_data:
        console.rule("[bold]对比结果[/bold]")
        generate_table(comparison_data, title="AI 模型准确率对比")

        # 打印总准确率汇总
        summary_table = Table(title="总准确率汇总", show_lines=True)
        summary_table.add_column("模型", style="bold")
        summary_table.add_column("正确数", justify="right")
        summary_table.add_column("总题数", justify="right")
        summary_table.add_column("准确率", justify="right")

        for label, results in all_results.items():
            total = len(results)
            correct = sum(1 for r in results if r.correct)
            acc = correct / total if total > 0 else 0.0
            color = "green" if acc >= 0.8 else "yellow" if acc >= 0.6 else "red"
            summary_table.add_row(
                label, str(correct), str(total), f"[{color}]{acc:.1%}[/{color}]"
            )

        console.print()
        console.print(summary_table)


# ── 子命令：report ─────────────────────────────────────────────

def cmd_report(args: argparse.Namespace):
    """从已保存的 JSON 结果生成 HTML 报告。"""
    results_path = Path(args.results_json)
    if not results_path.exists():
        console.print(f"[red]错误：文件不存在 '{results_path}'[/red]")
        sys.exit(1)

    console.print(f"[bold]分析结果文件...[/bold] {results_path}")

    analyzer = Analyzer()
    analyzer.load_results(str(results_path))
    analyzer.load_questions(str(get_questions_dir()))

    summary = analyzer.summary()

    # 输出路径：与输入同目录，扩展名改为 .html
    output_path = results_path.with_suffix(".html")
    generate_html_report(summary, str(output_path))

    console.print(f"\n[green]✓ HTML 报告已生成：[/green]{output_path}")


# ── 子命令：dataset stats ─────────────────────────────────────

def cmd_dataset_stats(args: argparse.Namespace):
    """显示题库统计信息。"""
    questions = _load_and_limit_questions(None)

    # 按领域统计
    domain_counts: dict[str, int] = {}
    subdomain_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    difficulty_counts: dict[str, int] = {}

    for q in questions:
        domain_counts[q.domain] = domain_counts.get(q.domain, 0) + 1
        subdomain_counts[q.subdomain] = subdomain_counts.get(q.subdomain, 0) + 1
        type_counts[q.question_type] = type_counts.get(q.question_type, 0) + 1
        difficulty_counts[q.difficulty] = difficulty_counts.get(q.difficulty, 0) + 1

    # 题库总览
    console.print(
        Panel(
            f"[bold]总题数：[/bold]{len(questions)}",
            title="📊 题库统计",
            border_style="cyan",
        )
    )

    # 领域分布
    domain_table = Table(title="按领域分布", show_lines=True)
    domain_table.add_column("领域", style="bold")
    domain_table.add_column("题数", justify="right")
    domain_table.add_column("占比", justify="right")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        pct = count / len(questions) * 100
        domain_table.add_row(domain, str(count), f"{pct:.1f}%")
    console.print(domain_table)

    # 题型分布
    type_table = Table(title="按题型分布")
    type_table.add_column("题型", style="bold")
    type_table.add_column("题数", justify="right")
    for qtype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        type_table.add_row(qtype, str(count))
    console.print(type_table)

    # 难度分布
    diff_table = Table(title="按难度分布")
    diff_table.add_column("难度", style="bold")
    diff_table.add_column("题数", justify="right")
    for diff, count in sorted(difficulty_counts.items(), key=lambda x: -x[1]):
        diff_table.add_row(diff, str(count))
    console.print(diff_table)


# ── 参数解析 ───────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hallumap",
        description="HalluMap — AI 幻觉检测器与幻觉地图",
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # ── test ──
    p_test = subparsers.add_parser("test", help="测试单个 AI 模型")
    p_test.add_argument("provider", help="Provider 名称 (openai, deepseek, ollama ...)")
    p_test.add_argument("--model", help="模型名称（覆盖 config 默认值）")
    p_test.add_argument("--limit", type=int, help="只测试前 N 道题")
    p_test.add_argument("--config", help="自定义配置文件路径（暂未实现）")
    p_test.set_defaults(func=cmd_test)

    # ── compare ──
    p_compare = subparsers.add_parser("compare", help="多模型横向对比")
    p_compare.add_argument(
        "providers",
        nargs="+",
        help="要对比的 provider 列表",
    )
    p_compare.add_argument("--model", help="模型名称（所有 provider 共用）")
    p_compare.add_argument("--limit", type=int, help="只测试前 N 道题")
    p_compare.set_defaults(func=cmd_compare)

    # ── report ──
    p_report = subparsers.add_parser("report", help="从 JSON 结果生成 HTML 报告")
    p_report.add_argument("results_json", help="结果 JSON 文件路径")
    p_report.set_defaults(func=cmd_report)

    # ── dataset ──
    p_dataset = subparsers.add_parser("dataset", help="题库管理")
    sub_dataset = p_dataset.add_subparsers(dest="dataset_cmd")
    sub_dataset.add_parser("stats", help="显示题库统计").set_defaults(func=cmd_dataset_stats)

    return parser


def main(argv: list[str] | None = None):
    """CLI 入口。"""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # dataset 子命令需要额外检查
    if args.command == "dataset" and not getattr(args, "dataset_cmd", None):
        parser.parse_args(["dataset", "--help"])
        sys.exit(0)

    # 执行对应子命令
    if hasattr(args, "func"):
        try:
            args.func(args)
        except KeyboardInterrupt:
            console.print("\n[yellow]用户中断[/yellow]")
            sys.exit(130)
        except Exception as e:
            console.print(f"\n[red]错误：{e}[/red]")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

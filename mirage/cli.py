"""Mirage CLI 鈥?AI 骞昏妫€娴嬪懡浠よ宸ュ叿"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from mirage import __version__
from mirage.core.analyzer import Analyzer
from mirage.core.config import Config
from mirage.core.runner import run_test_suite, save_results
from mirage.datasets.loader import get_questions_dir, load_questions
from mirage.providers import PROVIDERS, get_provider
from mirage.visualizer.html_report import generate_html_report
from mirage.visualizer.table import generate_table

console = Console()


def _build_model(provider_name: str, config: Config, model_override: str | None = None):
    """鏍规嵁 provider 鍚嶇О鍜岄厤缃垱寤?AIModel 瀹炰緥銆?""
    if provider_name not in PROVIDERS:
        available = ", ".join(sorted(PROVIDERS.keys()))
        console.print(f"[red]閿欒锛氭湭鐭ョ殑 provider '{provider_name}'[/red]")
        console.print(f"[dim]鍙敤鐨?provider锛歿available}[/dim]")
        sys.exit(1)

    try:
        provider_cfg = config.get_provider_config(provider_name)
    except KeyError:
        console.print(f"[red]閿欒锛歝onfig.yaml 涓湭閰嶇疆 provider '{provider_name}'[/red]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]閿欒锛歿e}[/red]")
        sys.exit(1)

    if model_override:
        provider_cfg["model"] = model_override

    return get_provider(provider_name, **provider_cfg)


def _load_and_limit_questions(limit: int | None):
    """鍔犺浇棰樺簱骞舵寜 limit 鎴彇銆?""
    questions_dir = get_questions_dir()
    questions = load_questions(str(questions_dir))
    if not questions:
        console.print("[red]閿欒锛氶搴撲负绌猴紝璇锋鏌?datasets/questions/ 鐩綍[/red]")
        sys.exit(1)

    if limit and limit > 0:
        questions = questions[:limit]

    return questions


def _print_summary(model_name: str, provider: str, results, output_path: str):
    """鎵撳嵃娴嬭瘯缁撴灉鎽樿銆?""
    total = len(results)
    correct = sum(1 for r in results if r.correct)
    accuracy = correct / total if total > 0 else 0.0

    table = Table(title=f"娴嬭瘯鎽樿 鈥?{provider}/{model_name}", show_lines=True)
    table.add_column("鎸囨爣", style="bold")
    table.add_column("鍊?, justify="right")
    table.add_row("鎬婚鏁?, str(total))
    table.add_row("姝ｇ‘鏁?, str(correct))
    table.add_row("閿欒鏁?, str(total - correct))

    color = "green" if accuracy >= 0.8 else "yellow" if accuracy >= 0.6 else "red"
    table.add_row("鍑嗙‘鐜?, f"[{color}]{accuracy:.1%}[/{color}]")
    table.add_row("缁撴灉鏂囦欢", output_path)

    console.print()
    console.print(table)


# 鈹€鈹€ 瀛愬懡浠わ細test 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def cmd_test(args: argparse.Namespace):
    """娴嬭瘯鍗曚釜 AI 妯″瀷鐨勫够瑙夌巼銆?""
    config = Config()

    # 鍔犺浇棰樺簱
    console.print(f"[bold]鍔犺浇棰樺簱...[/bold]")
    questions = _load_and_limit_questions(args.limit)
    console.print(f"鍏?[cyan]{len(questions)}[/cyan] 閬撻鐩甛n")

    # 鍒涘缓妯″瀷
    model = _build_model(args.provider, config, args.model)
    console.print(
        f"[bold]寮€濮嬫祴璇曪細[/bold]{args.provider}/{model.model}\n"
    )

    # 杩愯娴嬭瘯锛堝甫杩涘害鏉★級
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task = progress.add_task("娴嬭瘯涓?..", total=len(questions))

        def on_progress(current, total, result):
            progress.advance(task)

        results = run_test_suite(model, questions, progress_callback=on_progress)

    # 淇濆瓨缁撴灉
    output_path = save_results(
        results,
        model_name=model.model,
        provider=args.provider,
        output_dir=config.output["dir"],
    )

    # 鎵撳嵃鎽樿
    _print_summary(model.model, args.provider, results, output_path)
    console.print(f"\n[green]鉁?缁撴灉宸蹭繚瀛樺埌 {output_path}[/green]")


# 鈹€鈹€ 瀛愬懡浠わ細compare 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def cmd_compare(args: argparse.Namespace):
    """澶氭ā鍨嬪姣旀祴璇曘€?""
    config = Config()
    questions = _load_and_limit_questions(args.limit)
    console.print(f"鍏?[cyan]{len(questions)}[/cyan] 閬撻鐩甛n")

    # 鏀堕泦姣忎釜妯″瀷鐨勯鍩熷噯纭巼
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
            task = progress.add_task("娴嬭瘯涓?..", total=len(questions))

            def on_progress(current, total, result, _p=progress, _t=task):
                _p.advance(_t)

            results = run_test_suite(model, questions, progress_callback=on_progress)

        # 淇濆瓨姣忎釜妯″瀷鐨勭粨鏋?
        output_path = save_results(
            results,
            model_name=model.model,
            provider=provider_name,
            output_dir=config.output["dir"],
        )
        console.print(f"[green]鉁?缁撴灉宸蹭繚瀛樺埌 {output_path}[/green]\n")

        # 鐢?Analyzer 鎻愬彇棰嗗煙鍑嗙‘鐜?
        analyzer = Analyzer()
        analyzer.load_results(output_path)
        analyzer.load_questions(str(get_questions_dir()))

        domain_acc = analyzer.accuracy_by_domain()
        label = f"{provider_name}/{model.model}"
        comparison_data[label] = domain_acc
        all_results[label] = results

    # 鎵撳嵃瀵规瘮琛ㄦ牸
    if comparison_data:
        console.rule("[bold]瀵规瘮缁撴灉[/bold]")
        generate_table(comparison_data, title="AI 妯″瀷鍑嗙‘鐜囧姣?)

        # 鎵撳嵃鎬诲噯纭巼姹囨€?
        summary_table = Table(title="鎬诲噯纭巼姹囨€?, show_lines=True)
        summary_table.add_column("妯″瀷", style="bold")
        summary_table.add_column("姝ｇ‘鏁?, justify="right")
        summary_table.add_column("鎬婚鏁?, justify="right")
        summary_table.add_column("鍑嗙‘鐜?, justify="right")

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


# 鈹€鈹€ 瀛愬懡浠わ細report 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def cmd_report(args: argparse.Namespace):
    """浠庡凡淇濆瓨鐨?JSON 缁撴灉鐢熸垚 HTML 鎶ュ憡銆?""
    results_path = Path(args.results_json)
    if not results_path.exists():
        console.print(f"[red]閿欒锛氭枃浠朵笉瀛樺湪 '{results_path}'[/red]")
        sys.exit(1)

    console.print(f"[bold]鍒嗘瀽缁撴灉鏂囦欢...[/bold] {results_path}")

    analyzer = Analyzer()
    analyzer.load_results(str(results_path))
    analyzer.load_questions(str(get_questions_dir()))

    summary = analyzer.summary()

    # 杈撳嚭璺緞锛氫笌杈撳叆鍚岀洰褰曪紝鎵╁睍鍚嶆敼涓?.html
    output_path = results_path.with_suffix(".html")
    generate_html_report(summary, str(output_path))

    console.print(f"\n[green]鉁?HTML 鎶ュ憡宸茬敓鎴愶細[/green]{output_path}")


# 鈹€鈹€ 瀛愬懡浠わ細dataset stats 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def cmd_dataset_stats(args: argparse.Namespace):
    """鏄剧ず棰樺簱缁熻淇℃伅銆?""
    questions = _load_and_limit_questions(None)

    # 鎸夐鍩熺粺璁?
    domain_counts: dict[str, int] = {}
    subdomain_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    difficulty_counts: dict[str, int] = {}

    for q in questions:
        domain_counts[q.domain] = domain_counts.get(q.domain, 0) + 1
        subdomain_counts[q.subdomain] = subdomain_counts.get(q.subdomain, 0) + 1
        type_counts[q.question_type] = type_counts.get(q.question_type, 0) + 1
        difficulty_counts[q.difficulty] = difficulty_counts.get(q.difficulty, 0) + 1

    # 棰樺簱鎬昏
    console.print(
        Panel(
            f"[bold]鎬婚鏁帮細[/bold]{len(questions)}",
            title="馃搳 棰樺簱缁熻",
            border_style="cyan",
        )
    )

    # 棰嗗煙鍒嗗竷
    domain_table = Table(title="鎸夐鍩熷垎甯?, show_lines=True)
    domain_table.add_column("棰嗗煙", style="bold")
    domain_table.add_column("棰樻暟", justify="right")
    domain_table.add_column("鍗犳瘮", justify="right")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        pct = count / len(questions) * 100
        domain_table.add_row(domain, str(count), f"{pct:.1f}%")
    console.print(domain_table)

    # 棰樺瀷鍒嗗竷
    type_table = Table(title="鎸夐鍨嬪垎甯?)
    type_table.add_column("棰樺瀷", style="bold")
    type_table.add_column("棰樻暟", justify="right")
    for qtype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        type_table.add_row(qtype, str(count))
    console.print(type_table)

    # 闅惧害鍒嗗竷
    diff_table = Table(title="鎸夐毦搴﹀垎甯?)
    diff_table.add_column("闅惧害", style="bold")
    diff_table.add_column("棰樻暟", justify="right")
    for diff, count in sorted(difficulty_counts.items(), key=lambda x: -x[1]):
        diff_table.add_row(diff, str(count))
    console.print(diff_table)


# 鈹€鈹€ 鍙傛暟瑙ｆ瀽 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mirage",
        description="Mirage 鈥?AI 骞昏妫€娴嬪櫒涓庡够瑙夊湴鍥?,
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="鍙敤鍛戒护")

    # 鈹€鈹€ test 鈹€鈹€
    p_test = subparsers.add_parser("test", help="娴嬭瘯鍗曚釜 AI 妯″瀷")
    p_test.add_argument("provider", help="Provider 鍚嶇О (openai, deepseek, ollama ...)")
    p_test.add_argument("--model", help="妯″瀷鍚嶇О锛堣鐩?config 榛樿鍊硷級")
    p_test.add_argument("--limit", type=int, help="鍙祴璇曞墠 N 閬撻")
    p_test.add_argument("--config", help="鑷畾涔夐厤缃枃浠惰矾寰勶紙鏆傛湭瀹炵幇锛?)
    p_test.set_defaults(func=cmd_test)

    # 鈹€鈹€ compare 鈹€鈹€
    p_compare = subparsers.add_parser("compare", help="澶氭ā鍨嬫í鍚戝姣?)
    p_compare.add_argument(
        "providers",
        nargs="+",
        help="瑕佸姣旂殑 provider 鍒楄〃",
    )
    p_compare.add_argument("--model", help="妯″瀷鍚嶇О锛堟墍鏈?provider 鍏辩敤锛?)
    p_compare.add_argument("--limit", type=int, help="鍙祴璇曞墠 N 閬撻")
    p_compare.set_defaults(func=cmd_compare)

    # 鈹€鈹€ report 鈹€鈹€
    p_report = subparsers.add_parser("report", help="浠?JSON 缁撴灉鐢熸垚 HTML 鎶ュ憡")
    p_report.add_argument("results_json", help="缁撴灉 JSON 鏂囦欢璺緞")
    p_report.set_defaults(func=cmd_report)

    # 鈹€鈹€ dataset 鈹€鈹€
    p_dataset = subparsers.add_parser("dataset", help="棰樺簱绠＄悊")
    sub_dataset = p_dataset.add_subparsers(dest="dataset_cmd")
    sub_dataset.add_parser("stats", help="鏄剧ず棰樺簱缁熻").set_defaults(func=cmd_dataset_stats)

    return parser


def main(argv: list[str] | None = None):
    """CLI 鍏ュ彛銆?""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # dataset 瀛愬懡浠ら渶瑕侀澶栨鏌?
    if args.command == "dataset" and not getattr(args, "dataset_cmd", None):
        parser.parse_args(["dataset", "--help"])
        sys.exit(0)

    # 鎵ц瀵瑰簲瀛愬懡浠?
    if hasattr(args, "func"):
        try:
            args.func(args)
        except KeyboardInterrupt:
            console.print("\n[yellow]鐢ㄦ埛涓柇[/yellow]")
            sys.exit(130)
        except Exception as e:
            console.print(f"\n[red]閿欒锛歿e}[/red]")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()


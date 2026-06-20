"""HTML 报告生成 — 自包含单页 HTML，内嵌 CSS/JS 和 SVG 热力图"""

import html
from pathlib import Path


def _build_heatmap_svg(
    data: dict[str, dict[str, float]], width: int = 800, height: int = 400
) -> str:
    """生成内嵌 SVG 热力图。"""
    if not data:
        return "<p>无数据</p>"

    all_domains: set[str] = set()
    for model_data in data.values():
        all_domains.update(model_data.keys())
    domains = sorted(all_domains)
    models = list(data.keys())

    cell_w = max(60, (width - 120) // max(len(domains), 1))
    cell_h = max(36, 280 // max(len(models), 1))
    left_margin = 120
    top_margin = 40
    svg_w = left_margin + len(domains) * cell_w + 20
    svg_h = top_margin + len(models) * cell_h + 20

    def _color(val: float) -> str:
        """准确率→颜色：红(0)→橙→绿(1)"""
        if val < 0.5:
            r, g = 211, int(47 + (val / 0.5) * (153 - 47))
        else:
            r = int(211 - ((val - 0.5) / 0.5) * (211 - 76))
            g = int(153 + ((val - 0.5) / 0.5) * (127 - 153))
        return f"rgb({r},{g},47)"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'style="font-family:Microsoft YaHei,SimHei,sans-serif">'
    ]

    # 列标题（领域）
    for j, domain in enumerate(domains):
        x = left_margin + j * cell_w + cell_w // 2
        parts.append(
            f'<text x="{x}" y="{top_margin - 8}" text-anchor="middle" '
            f'font-size="12" fill="#333">{html.escape(domain)}</text>'
        )

    # 行标题（模型）+ 单元格
    for i, model in enumerate(models):
        y = top_margin + i * cell_h
        parts.append(
            f'<text x="{left_margin - 8}" y="{y + cell_h // 2 + 4}" '
            f'text-anchor="end" font-size="12" fill="#333">{html.escape(model)}</text>'
        )
        for j, domain in enumerate(domains):
            val = data[model].get(domain)
            x = left_margin + j * cell_w
            if val is not None:
                color = _color(val)
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{cell_w - 2}" height="{cell_h - 2}" '
                    f'rx="4" fill="{color}"/>'
                )
                text_color = "white" if val < 0.5 else "black"
                parts.append(
                    f'<text x="{x + cell_w // 2 - 1}" y="{y + cell_h // 2 + 4}" '
                    f'text-anchor="middle" font-size="11" fill="{text_color}" '
                    f'font-weight="bold">{val:.0%}</text>'
                )
            else:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{cell_w - 2}" height="{cell_h - 2}" '
                    f'rx="4" fill="#eee"/>'
                )

    parts.append("</svg>")
    return "\n".join(parts)


def _build_results_table(results: list[dict]) -> str:
    """构建结果 HTML 表格。"""
    if not results:
        return "<p>无结果数据</p>"

    rows = []
    for r in results:
        correct = r.get("correct", False)
        status_class = "pass" if correct else "fail"
        status_text = "✓" if correct else "✗"
        rows.append(
            f'<tr class="{status_class}">'
            f'<td>{html.escape(r.get("question_id", ""))}</td>'
            f'<td>{html.escape(r.get("domain", ""))}</td>'
            f'<td>{html.escape(r.get("model_answer", "")[:80])}</td>'
            f'<td>{html.escape(r.get("expected_answer", ""))}</td>'
            f'<td class="status">{status_text}</td>'
            f"</tr>"
        )

    return (
        '<table class="results-table">'
        "<thead><tr><th>题号</th><th>领域</th><th>模型回答</th><th>正确答案</th><th>状态</th></tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table>"
    )


def _build_error_cases(errors: list[dict]) -> str:
    """构建幻觉案例展示区域。"""
    if not errors:
        return "<p>无幻觉案例</p>"

    cards = []
    for e in errors:
        cards.append(
            '<div class="error-card">'
            f'<div class="error-header">#{html.escape(e.get("question_id", ""))} '
            f'<span class="domain-tag">{html.escape(e.get("domain", ""))}</span></div>'
            f'<div class="error-body">'
            f'<p><strong>模型回答：</strong>{html.escape(str(e.get("model_answer", "")))}</p>'
            f'<p><strong>正确答案：</strong>{html.escape(str(e.get("expected_answer", "")))}</p>'
            f'<p><strong>置信度：</strong>{e.get("confidence", 0):.0%}</p>'
            f"</div></div>"
        )
    return "\n".join(cards)


def generate_html_report(
    analyzer_results: dict,
    output_path: str,
) -> str:
    """生成自包含 HTML 报告。

    Args:
        analyzer_results: Analyzer.summary() 的返回值
        output_path: 输出 HTML 文件路径

    Returns:
        保存的文件路径
    """
    model = analyzer_results.get("model", "未知模型")
    accuracy = analyzer_results.get("accuracy", 0)
    total = analyzer_results.get("total_questions", 0)
    correct = analyzer_results.get("correct", 0)

    # 构建热力图数据
    domain_data = analyzer_results.get("accuracy_by_domain", {})
    heatmap_data = {model: domain_data}
    heatmap_svg = _build_heatmap_svg(heatmap_data)

    # 结果表格（取 top_errors 作为幻觉案例）
    top_errors = analyzer_results.get("top_errors", [])
    hallucination_by_type = analyzer_results.get("hallucination_by_type", {})
    difficulty_data = analyzer_results.get("accuracy_by_difficulty", {})

    # 幻觉类型分布
    hallucination_items = "".join(
        f'<li>{html.escape(k)}：<strong>{v}</strong> 次</li>'
        for k, v in hallucination_by_type.items()
    )

    # 难度分布
    difficulty_items = "".join(
        f'<li>{html.escape(k)}：<strong>{v:.0%}</strong></li>'
        for k, v in difficulty_data.items()
    )

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HalluMap — {html.escape(model)} 幻觉报告</title>
<style>
  :root {{
    --color-bg: #fafafa;
    --color-surface: #ffffff;
    --color-primary: #1976d2;
    --color-success: #4caf50;
    --color-danger: #d32f2f;
    --color-text: #212121;
    --color-muted: #757575;
    --radius: 8px;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: "Microsoft YaHei", "SimHei", sans-serif;
    background: var(--color-bg);
    color: var(--color-text);
    line-height: 1.6;
    padding: 2rem;
  }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{ font-size: 2rem; margin-bottom: 0.5rem; }}
  .subtitle {{ color: var(--color-muted); margin-bottom: 2rem; }}
  .stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }}
  .stat-card {{
    background: var(--color-surface);
    border-radius: var(--radius);
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }}
  .stat-value {{ font-size: 2rem; font-weight: bold; }}
  .stat-value.good {{ color: var(--color-success); }}
  .stat-value.bad {{ color: var(--color-danger); }}
  .stat-label {{ color: var(--color-muted); font-size: 0.9rem; }}
  .section {{
    background: var(--color-surface);
    border-radius: var(--radius);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }}
  .section h2 {{
    font-size: 1.3rem;
    margin-bottom: 1rem;
    border-bottom: 2px solid var(--color-primary);
    padding-bottom: 0.5rem;
  }}
  .heatmap-container {{ text-align: center; overflow-x: auto; }}
  table.results-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }}
  table.results-table th {{
    background: #f5f5f5;
    padding: 0.6rem;
    text-align: left;
    border-bottom: 2px solid #ddd;
  }}
  table.results-table td {{
    padding: 0.5rem 0.6rem;
    border-bottom: 1px solid #eee;
  }}
  tr.pass .status {{ color: var(--color-success); font-weight: bold; }}
  tr.fail .status {{ color: var(--color-danger); font-weight: bold; }}
  .error-card {{
    border: 1px solid #e0e0e0;
    border-left: 4px solid var(--color-danger);
    border-radius: var(--radius);
    padding: 1rem;
    margin-bottom: 0.8rem;
  }}
  .error-header {{
    font-weight: bold;
    margin-bottom: 0.5rem;
  }}
  .domain-tag {{
    background: #e3f2fd;
    color: var(--color-primary);
    padding: 0.1rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: normal;
  }}
  .error-body p {{ margin-bottom: 0.3rem; }}
  ul {{ padding-left: 1.5rem; }}
  li {{ margin-bottom: 0.3rem; }}
  .two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }}
  @media (max-width: 700px) {{
    .two-col {{ grid-template-columns: 1fr; }}
    body {{ padding: 1rem; }}
  }}
</style>
</head>
<body>
<div class="container">
  <h1>🗺️ HalluMap 幻觉报告</h1>
  <p class="subtitle">模型：{html.escape(model)} | 生成时间：{html.escape(analyzer_results.get("timestamp", ""))}</p>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-value {"good" if accuracy >= 0.8 else "bad"}">{accuracy:.1%}</div>
      <div class="stat-label">总准确率</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{total}</div>
      <div class="stat-label">测试题目数</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" style="color:var(--color-success)">{correct}</div>
      <div class="stat-label">正确</div>
    </div>
    <div class="stat-card">
      <div class="stat-value" style="color:var(--color-danger)">{total - correct}</div>
      <div class="stat-label">错误</div>
    </div>
  </div>

  <div class="section">
    <h2>🔥 领域准确率热力图</h2>
    <div class="heatmap-container">{heatmap_svg}</div>
  </div>

  <div class="two-col">
    <div class="section">
      <h2>📊 幻觉类型分布</h2>
      <ul>{hallucination_items or "<li>无数据</li>"}</ul>
    </div>
    <div class="section">
      <h2>📈 难度准确率</h2>
      <ul>{difficulty_items or "<li>无数据</li>"}</ul>
    </div>
  </div>

  <div class="section">
    <h2>⚠️ 幻觉案例 Top {len(top_errors)}</h2>
    {_build_error_cases(top_errors)}
  </div>
</div>
</body>
</html>"""

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return output_path

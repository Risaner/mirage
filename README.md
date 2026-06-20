# HalluMap

> 一行命令测试任何 AI 模型的幻觉率，热力图展示各领域表现。

系统性检测 AI 模型在不同知识领域的幻觉率，生成可视化的「幻觉地图」，支持多模型横向对比。

## 核心功能

- **多模型支持** — OpenAI / DeepSeek / 通义千问 / 智谱 / Ollama，统一 OpenAI SDK 调用
- **多题型评判** — 选择题精确匹配、填空题模糊匹配、简答题 LLM 辅助评判
- **幻觉地图** — 热力图 + 雷达图，直观展示每个模型在哪些领域最容易编造
- **中文优先** — 题库以中文为主，覆盖中国学生常见知识盲区
- **可扩展题库** — JSON 格式题目，社区可提交新题目

## 快速开始

### 安装

```bash
git clone https://github.com/Risaner/hallumap.git
cd hallumap
pip install -e .
```

### 配置

```bash
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入你的 API Key
```

也可以通过环境变量设置 API Key：

```bash
export HALLUMAP_DEEPSEEK_API_KEY="sk-xxx"
export HALLUMAP_OPENAI_API_KEY="sk-xxx"
```

### 使用

```bash
# 查看帮助
hallumap --help

# 测试单个模型
hallumap test deepseek --limit 10

# 多模型对比
hallumap compare deepseek qwen --limit 20

# 查看题库统计
hallumap dataset stats

# 从已有结果生成 HTML 报告
hallumap report results/deepseek_deepseek-chat_20260620.json
```

## 架构

```
hallumap/
├── core/              # 核心引擎
│   ├── model.py       # AI 模型抽象层
│   ├── runner.py      # 测试运行器（批量执行）
│   ├── analyzer.py    # 统计分析器
│   └── config.py      # 配置管理
├── providers/         # AI 模型 Provider
│   ├── openai_provider.py
│   ├── deepseek.py
│   ├── qwen.py
│   ├── zhipu.py
│   └── ollama.py
├── datasets/          # 题库系统
│   ├── loader.py      # 题库加载器
│   └── questions/     # JSON 题库文件
├── judges/            # 评判系统
│   ├── exact_match.py # 精确匹配
│   ├── fuzzy_match.py # 模糊匹配
│   ├── regex_judge.py # 正则提取
│   └── llm_judge.py   # LLM 辅助评判
├── visualizer/        # 可视化
│   ├── heatmap.py     # 热力图
│   ├── radar.py       # 雷达图
│   ├── table.py       # 终端表格
│   └── html_report.py # HTML 交互报告
└── cli.py             # 命令行入口
```

**数据流：** CLI -> 运行器加载题库 -> 逐题调用模型 -> 评判器判定 -> 收集结果 -> 可视化输出

## 题库

题目存放在 `hallumap/datasets/questions/`，按领域分为 JSON 文件：

| 领域 | 文件 | 题数 |
|------|------|------|
| 历史 | `history.json` | 30 |
| 科学 | `science.json` | 30 |
| 数学 | `math.json` | 30 |
| 计算机 | `cs.json` | 30 |
| 文学 | `literature.json` | 20 |
| 地理 | `geography.json` | 20 |
| 常识 | `common.json` | 20 |
| **合计** | | **180** |

题目格式：

```json
{
  "id": "hist_001",
  "domain": "history",
  "subdomain": "中国史",
  "question": "秦始皇统一六国的年份是？",
  "question_type": "choice",
  "options": ["A. 公元前230年", "B. 公元前221年", "C. 公元前210年", "D. 公元前206年"],
  "answer": "B",
  "answer_aliases": ["公元前221年", "221BC"],
  "difficulty": "easy",
  "hallucination_type": "numerical",
  "source": "《史记·秦始皇本纪》"
}
```

## 幻觉分类体系

| 类型 | 定义 | 示例 |
|------|------|------|
| 事实捏造 | 编造不存在的事实 | "爱因斯坦于1955年获得诺贝尔和平奖" |
| 张冠李戴 | 把A的事说成B的 | "《百年孤独》是马尔克斯的处女作" |
| 数字幻觉 | 编造具体的数字/日期 | "中国有35个省级行政区" |
| 逻辑幻觉 | 推理过程正确但前提错误 | "因为地球是平的，所以..." |
| 语境幻觉 | 特定语境下给出错误答案 | "Python的list是不可变的" |
| 过度自信 | 对不确定的事给出确定答案 | "这个问题的答案绝对是X" |

## 开发

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ --cov=hallumap --cov-report=term-missing
```

## 贡献指南

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feat/新功能`
3. 提交改动：`git commit -m "feat: 添加xxx"`
4. 推送分支：`git push origin feat/新功能`
5. 提交 Pull Request

**添加新题库：** 在 `hallumap/datasets/questions/` 下新建 JSON 文件，遵循题目格式即可。

**添加新 Provider：** 在 `hallumap/providers/` 下新建文件，继承 `AIModel` 并注册到 `__init__.py`。

## License

[MIT](LICENSE)

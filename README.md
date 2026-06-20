# Mirage

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
git clone https://github.com/Risaner/mirage.git
cd mirage
pip install -e .
```

### 配置

```bash
cp config.yaml.example config.yaml
# 编辑 config.yaml，填入你的 API Key
```

也可以通过环境变量设置 API Key：

```bash
export MIRAGE_DEEPSEEK_API_KEY="sk-xxx"
export MIRAGE_OPENAI_API_KEY="sk-xxx"
```

### 使用

```bash
# 查看帮助
mirage --help

# 测试单个模型
mirage test deepseek --limit 10

# 多模型对比
mirage compare deepseek qwen --limit 20

# 查看题库统计
mirage dataset stats

# 从已有结果生成 HTML 报告
mirage report results/deepseek_deepseek-chat_20260620.json
```

## 架构

```
mirage/
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

题目来自三个权威公开数据集，共 **1740 道**经过人工校验的题目：

| 数据集 | 来源 | 题数 | 特点 |
|--------|------|------|------|
| [HalluQA](https://github.com/OpenMOSS/HalluQA) | 复旦大学 MOSS 团队 | 450 | 中文幻觉评测，正确/错误答案配对 |
| [TruthfulQA](https://github.com/sylinrl/TruthfulQA) | Anthropic/牛津大学 | 790 | 对抗性设计，37 个类别，专门诱导 AI 说出"听起来对但实际错"的答案 |
| [HaluEval](https://github.com/RUCAIBox/HaluEval) | 中国人民大学 | 500 | 正确答案与幻觉答案配对，知识问答场景 |

**为什么用这些数据集而不是 AI 生成的题？**
- TruthfulQA 是对抗性设计——题目故意选那些 AI 最容易编造答案的领域（误区、阴谋论、法律、健康等）
- HalluQA 专门测试中文 LLM 的幻觉行为，有 450 道人工标注的题目
- HaluEval 的每道题都有"正确答案 vs AI 编造的答案"配对，直接暴露幻觉模式

题目存放在 `mirage/datasets/questions/`：

```json
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
pytest tests/ --cov=mirage --cov-report=term-missing
```

## 贡献指南

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feat/新功能`
3. 提交改动：`git commit -m "feat: 添加xxx"`
4. 推送分支：`git push origin feat/新功能`
5. 提交 Pull Request

**添加新题库：** 在 `mirage/datasets/questions/` 下新建 JSON 文件，遵循题目格式即可。

**添加新 Provider：** 在 `mirage/providers/` 下新建文件，继承 `AIModel` 并注册到 `__init__.py`。

## License

[MIT](LICENSE)

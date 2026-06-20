"""题库加载器 — 从 JSON 文件加载测试题目"""

from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class Question:
    """单道测试题目"""
    id: str
    domain: str
    subdomain: str
    question: str
    question_type: str  # "choice" / "fill" / "short_answer"
    options: list = field(default_factory=list)
    answer: str = ""
    answer_aliases: list = field(default_factory=list)
    difficulty: str = "medium"
    hallucination_type: str = "fabrication"
    source: str = ""
    tags: list = field(default_factory=list)


def get_questions_dir() -> Path:
    """返回题目目录路径"""
    return Path(__file__).parent / "questions"


def load_questions(questions_dir: str) -> list[Question]:
    """从 questions_dir 加载所有 .json 文件，返回 Question 列表"""
    questions: list[Question] = []
    for json_file in Path(questions_dir).glob("*.json"):
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            questions.append(Question(**item))
    return questions

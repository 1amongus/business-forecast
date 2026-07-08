from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class CategoryScore:
    category_name: str
    score: float  # 1-5
    reasoning: str = ""
    question_scores: List[float] = field(default_factory=list)


@dataclass
class Evaluation:
    article_filename: str
    company: str = ""
    overall_score: float = 0.0
    category_scores: List[CategoryScore] = field(default_factory=list)
    summary: str = ""
    model_used: str = ""
    evaluated_at: datetime = field(default_factory=datetime.now)

    @property
    def score_label(self) -> str:
        if self.overall_score >= 4.5:
            return "Excellent"
        elif self.overall_score >= 3.5:
            return "Strong"
        elif self.overall_score >= 2.5:
            return "Moderate"
        elif self.overall_score >= 1.5:
            return "Weak"
        return "Poor"

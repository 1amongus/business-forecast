from dataclasses import dataclass, field
from typing import List


@dataclass
class Question:
    text: str
    weight: float = 1.0


@dataclass
class Category:
    name: str
    description: str = ""
    questions: List[Question] = field(default_factory=list)
    weight: float = 1.0

    @property
    def question_count(self) -> int:
        return len(self.questions)

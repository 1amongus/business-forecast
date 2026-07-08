from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Article:
    filename: str
    title: str = ""
    content: str = ""
    company: str = ""
    source_path: str = ""
    added_at: datetime = field(default_factory=datetime.now)

    @property
    def preview(self) -> str:
        """First 200 chars of content."""
        return self.content[:200].strip() + "..." if len(self.content) > 200 else self.content

    @property
    def word_count(self) -> int:
        return len(self.content.split())

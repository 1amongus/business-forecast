"""Manages articles stored as .md files."""

import re
from pathlib import Path
from datetime import datetime
from typing import List

from PySide6.QtCore import QStandardPaths

from ..models import Article


def _data_dir() -> Path:
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _articles_dir() -> Path:
    path = _data_dir() / "articles"
    path.mkdir(parents=True, exist_ok=True)
    return path


class ArticleStore:
    def __init__(self):
        self._dir = _articles_dir()

    @property
    def articles_directory(self) -> Path:
        return self._dir

    def load_articles(self) -> List[Article]:
        articles = []
        for f in sorted(self._dir.glob("*.md")):
            articles.append(self._parse_article(f))
        return articles

    def add_article(self, source_path: str) -> Article:
        """Copy an .md file into the articles directory."""
        src = Path(source_path)
        if not src.exists() or src.suffix.lower() != ".md":
            raise ValueError(f"Invalid file: {source_path}")

        dest = self._dir / src.name
        counter = 1
        while dest.exists():
            dest = self._dir / f"{src.stem}_{counter}.md"
            counter += 1

        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        return self._parse_article(dest)

    def remove_article(self, filename: str) -> bool:
        path = self._dir / filename
        if path.exists():
            path.unlink()
            return True
        return False

    def get_article_content(self, filename: str) -> str:
        path = self._dir / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def _parse_article(self, path: Path) -> Article:
        content = path.read_text(encoding="utf-8")
        title = self._extract_title(content, path.stem)
        company = self._extract_company(content, title)
        return Article(
            filename=path.name,
            title=title,
            content=content,
            company=company,
            source_path=str(path),
            added_at=datetime.fromtimestamp(path.stat().st_mtime),
        )

    @staticmethod
    def _extract_title(content: str, fallback: str) -> str:
        """Extract title from first H1 heading or first line."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
            if line and not line.startswith("---"):
                return line[:100]
        return fallback

    @staticmethod
    def _extract_company(content: str, title: str) -> str:
        """Try to extract company name from content."""
        # Simple heuristic: look for patterns like "Company Inc." or "Company Corp."
        patterns = [
            r"([A-Z][A-Za-z&\s]+(?:Inc\.|Corp\.|Co\.|Ltd\.|LLC|Group|Holdings))",
            r"([A-Z][A-Za-z]+)\s+(?:reported|announced|said|plans|expects)",
        ]
        for pattern in patterns:
            match = re.search(pattern, content[:500])
            if match:
                return match.group(1).strip()
        # Fall back to title
        return title.split(":")[0].split("—")[0].strip()[:50]

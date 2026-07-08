"""Manages scoring categories stored as .md files with YAML frontmatter."""

import yaml
from pathlib import Path
from typing import List

from PySide6.QtCore import QStandardPaths

from ..models import Category, Question


def _data_dir() -> Path:
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _categories_dir() -> Path:
    path = _data_dir() / "categories"
    path.mkdir(parents=True, exist_ok=True)
    return path


DEFAULT_CATEGORIES = [
    Category(
        name="Low Cost Producer",
        description="The company wins because it produces at the lowest cost",
        questions=[
            Question("How did you become a low cost producer?"),
            Question("Can you commit to volumes?"),
            Question("Can a competitor beat you on volumes?"),
        ],
    ),
    Category(
        name="Brand Marketing",
        description="The company wins because of its brand image and marketing",
        questions=[
            Question("How did you create this image?"),
            Question("How will you protect that image?"),
        ],
    ),
    Category(
        name="Becoming the Middle Man",
        description="The company wins by being an essential intermediary",
        questions=[
            Question("Do you have the expertise?"),
            Question("Do you have the cash?"),
        ],
    ),
    Category(
        name="New Technology",
        description="The company wins through technological innovation",
        questions=[
            Question("Does it work?"),
            Question("Does the market care?"),
            Question("Can you protect it?"),
        ],
    ),
]

# The root question that determines which category applies
ROOT_QUESTION = "Why do customers buy from this company?"


class CategoryStore:
    def __init__(self):
        self._dir = _categories_dir()

    def load_categories(self) -> List[Category]:
        categories = []
        for f in sorted(self._dir.glob("*.md")):
            cat = self._parse_category_file(f)
            if cat:
                categories.append(cat)
        return categories

    def ensure_defaults(self):
        """Seed default categories if none exist."""
        if not list(self._dir.glob("*.md")):
            for cat in DEFAULT_CATEGORIES:
                self.save_category(cat)

    def save_category(self, category: Category) -> None:
        """Save category as .md with YAML frontmatter."""
        filename = category.name.lower().replace(" ", "_").replace("&", "and") + ".md"
        path = self._dir / filename

        frontmatter = {
            "name": category.name,
            "description": category.description,
            "weight": category.weight,
        }

        lines = ["---"]
        lines.append(yaml.dump(frontmatter, default_flow_style=False).strip())
        lines.append("---")
        lines.append("")
        lines.append(f"# {category.name}")
        lines.append("")
        if category.description:
            lines.append(f"{category.description}")
            lines.append("")
        lines.append("## Questions")
        lines.append("")
        for q in category.questions:
            weight_str = f" (weight: {q.weight})" if q.weight != 1.0 else ""
            lines.append(f"- {q.text}{weight_str}")

        path.write_text("\n".join(lines), encoding="utf-8")

    def remove_category(self, name: str) -> bool:
        filename = name.lower().replace(" ", "_").replace("&", "and") + ".md"
        path = self._dir / filename
        if path.exists():
            path.unlink()
            return True
        # Try matching by name
        for f in self._dir.glob("*.md"):
            cat = self._parse_category_file(f)
            if cat and cat.name == name:
                f.unlink()
                return True
        return False

    def add_category_from_file(self, source_path: str) -> Category:
        """Import a category from an external .md file."""
        src = Path(source_path)
        if not src.exists():
            raise ValueError(f"File not found: {source_path}")

        dest = self._dir / src.name
        counter = 1
        while dest.exists():
            dest = self._dir / f"{src.stem}_{counter}.md"
            counter += 1

        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        cat = self._parse_category_file(dest)
        if not cat:
            cat = Category(name=src.stem.replace("_", " ").title())
        return cat

    def get_category_raw(self, name: str) -> str:
        """Get the raw .md content of a category for editing."""
        for f in sorted(self._dir.glob("*.md")):
            cat = self._parse_category_file(f)
            if cat and cat.name == name:
                return f.read_text(encoding="utf-8")
        return ""

    def save_category_raw(self, name: str, content: str) -> bool:
        """Save raw .md content for a category, re-parsing it."""
        for f in sorted(self._dir.glob("*.md")):
            cat = self._parse_category_file(f)
            if cat and cat.name == name:
                f.write_text(content, encoding="utf-8")
                return True
        # New file
        filename = name.lower().replace(" ", "_").replace("&", "and") + ".md"
        path = self._dir / filename
        path.write_text(content, encoding="utf-8")
        return True

    def _parse_category_file(self, path: Path) -> Category:
        """Parse a category .md file with optional YAML frontmatter."""
        content = path.read_text(encoding="utf-8")
        name = path.stem.replace("_", " ").title()
        description = ""
        weight = 1.0
        questions = []

        # Parse YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    meta = yaml.safe_load(parts[1])
                    if isinstance(meta, dict):
                        name = meta.get("name", name)
                        description = meta.get("description", "")
                        weight = float(meta.get("weight", 1.0))
                    content = parts[2]
                except yaml.YAMLError:
                    pass

        # Parse questions from bullet points
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                q_text = line[2:].strip()
                q_weight = 1.0
                # Check for weight annotation
                if "(weight:" in q_text:
                    import re
                    match = re.search(r"\(weight:\s*([\d.]+)\)", q_text)
                    if match:
                        q_weight = float(match.group(1))
                        q_text = re.sub(r"\s*\(weight:\s*[\d.]+\)", "", q_text)
                if q_text:
                    questions.append(Question(text=q_text, weight=q_weight))

        return Category(name=name, description=description, questions=questions, weight=weight)

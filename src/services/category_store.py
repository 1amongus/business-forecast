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
        name="Leadership & Management",
        description="Quality and track record of executive leadership",
        questions=[
            Question("Does the CEO have a strong track record of delivering results?"),
            Question("Is there evidence of strategic vision and long-term planning?"),
            Question("Are there signs of effective cost management and operational efficiency?"),
        ],
    ),
    Category(
        name="Market Position",
        description="Competitive advantage and market share",
        questions=[
            Question("Does the company have a defensible competitive moat?"),
            Question("Is the company gaining or losing market share?"),
            Question("How strong is brand recognition and customer loyalty?"),
        ],
    ),
    Category(
        name="Financial Health",
        description="Revenue growth, profitability, and balance sheet strength",
        questions=[
            Question("Is revenue growing consistently year over year?"),
            Question("Are profit margins expanding or stable?"),
            Question("Is the debt-to-equity ratio manageable?"),
        ],
    ),
    Category(
        name="Innovation & Adaptability",
        description="R&D investment and ability to pivot",
        questions=[
            Question("Is the company investing meaningfully in R&D or new products?"),
            Question("Can the company adapt quickly to market shifts?"),
            Question("Is there evidence of successful product launches or pivots?"),
        ],
    ),
    Category(
        name="Industry Tailwinds",
        description="External factors and macro trends supporting growth",
        questions=[
            Question("Is the industry experiencing secular growth?"),
            Question("Are regulatory changes favorable or unfavorable?"),
            Question("Is there rising demand for the company's products/services?"),
        ],
    ),
]


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

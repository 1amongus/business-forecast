# Business-Forecast

A desktop app that evaluates company success potential by analyzing WSJ articles using a local SLM (Ollama). Users define scoring categories and questions, then the AI reads articles and produces a structured success score (1–5).

## Tech Stack

- **Python 3.12** + **PySide6** (Qt 6)
- **QML** UI with custom dark theme
- **Ollama** for local SLM inference
- No servers, no databases — everything is local `.md` files

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## How It Works

1. **Upload Articles** — Drop WSJ articles (`.md` files) into the app
2. **Define Categories** — Create scoring categories (e.g., "Leadership", "Market Position")
3. **Add Questions** — Each category has evaluation questions
4. **Analyze** — The SLM reads articles and scores each category 1–5
5. **Review** — See per-category scores, overall score, and AI reasoning

## Architecture

```
main.py                     # Entry point
src/
├── models/                 # Article, Category, Question, Evaluation
├── services/               # ArticleStore, EvaluationEngine, OllamaClient
├── controllers/            # Qt controllers bridging UI ↔ services
└── ui/qml/                 # QML pages and components
tests/                      # pytest suite
```

## File Formats

All data stored as `.md` files:
- Articles: `data/articles/*.md`
- Categories: `data/categories/*.md` (YAML frontmatter + questions)
- Evaluations: `data/evaluations/*.md` (scores + reasoning)

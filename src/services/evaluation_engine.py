"""Evaluation engine that uses Ollama to score companies from articles."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from PySide6.QtCore import QObject, Signal, Slot, QUrl, QSettings, QStandardPaths
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from ..models import Article, Category, Evaluation, CategoryScore


def _evaluations_dir() -> Path:
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)) / "evaluations"
    path.mkdir(parents=True, exist_ok=True)
    return path


class EvaluationEngine(QObject):
    evaluationComplete = Signal(object)  # Evaluation
    evaluationError = Signal(str)
    progressUpdate = Signal(int, int)  # current, total

    def __init__(self, parent=None):
        super().__init__(parent)
        self._network = QNetworkAccessManager(self)
        self._settings = QSettings()
        self._pending_categories = []
        self._current_article = None
        self._current_scores = []
        self._current_idx = 0

    @property
    def model(self) -> str:
        return self._settings.value("slm/model", "phi3:mini")

    @property
    def base_url(self) -> str:
        return self._settings.value("slm/baseUrl", "http://localhost:11434")

    @property
    def temperature(self) -> float:
        return float(self._settings.value("slm/temperature", 0.3))

    @property
    def max_tokens(self) -> int:
        return int(self._settings.value("slm/maxTokens", 512))

    def evaluate(self, article: Article, categories: List[Category]):
        """Start evaluating an article against all categories."""
        if not categories:
            self.evaluationError.emit("No categories defined.")
            return

        self._current_article = article
        self._pending_categories = list(categories)
        self._current_scores = []
        self._current_idx = 0
        self.progressUpdate.emit(0, len(categories))
        self._evaluate_next_category()

    def _evaluate_next_category(self):
        if self._current_idx >= len(self._pending_categories):
            self._finalize_evaluation()
            return

        category = self._pending_categories[self._current_idx]
        prompt = self._build_prompt(self._current_article, category)

        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert business analyst. Evaluate companies based on articles and score them precisely. Always respond in valid JSON format."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
            "format": "json",
        }).encode("utf-8")

        request = QNetworkRequest(QUrl(f"{self.base_url}/api/chat"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setTransferTimeout(120000)  # 2 min timeout

        reply = self._network.post(request, payload)
        reply.finished.connect(lambda: self._handle_category_response(reply))

    def _handle_category_response(self, reply: QNetworkReply):
        category = self._pending_categories[self._current_idx]

        if reply.error() != QNetworkReply.NetworkError.NoError:
            self._current_scores.append(CategoryScore(
                category_name=category.name,
                score=0.0,
                reasoning=f"Error: {reply.errorString()}",
            ))
        else:
            try:
                data = json.loads(reply.readAll().data().decode("utf-8"))
                content = data.get("message", {}).get("content", "{}")
                result = json.loads(content)
                score = float(result.get("score", 0))
                score = max(1.0, min(5.0, score))
                reasoning = result.get("reasoning", "No reasoning provided.")
                q_scores = result.get("question_scores", [])

                self._current_scores.append(CategoryScore(
                    category_name=category.name,
                    score=score,
                    reasoning=reasoning,
                    question_scores=[float(s) for s in q_scores],
                ))
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                self._current_scores.append(CategoryScore(
                    category_name=category.name,
                    score=0.0,
                    reasoning=f"Parse error: {e}",
                ))

        reply.deleteLater()
        self._current_idx += 1
        self.progressUpdate.emit(self._current_idx, len(self._pending_categories))
        self._evaluate_next_category()

    def _finalize_evaluation(self):
        valid_scores = [s for s in self._current_scores if s.score > 0]
        if valid_scores:
            total_weight = sum(
                cat.weight for cat, s in zip(self._pending_categories, self._current_scores) if s.score > 0
            )
            if total_weight > 0:
                overall = sum(
                    s.score * cat.weight
                    for cat, s in zip(self._pending_categories, self._current_scores) if s.score > 0
                ) / total_weight
            else:
                overall = sum(s.score for s in valid_scores) / len(valid_scores)
        else:
            overall = 0.0

        evaluation = Evaluation(
            article_filename=self._current_article.filename,
            company=self._current_article.company,
            overall_score=round(overall, 2),
            category_scores=self._current_scores,
            summary=f"Evaluated {len(valid_scores)}/{len(self._current_scores)} categories successfully.",
            model_used=self.model,
            evaluated_at=datetime.now(),
        )

        self._save_evaluation(evaluation)
        self.evaluationComplete.emit(evaluation)
        print(f"[EvaluationEngine] {evaluation.company}: {evaluation.overall_score}/5 ({evaluation.score_label})")

    def _save_evaluation(self, evaluation: Evaluation):
        """Save evaluation as .md file."""
        filename = f"{evaluation.article_filename.replace('.md', '')}_eval.md"
        path = _evaluations_dir() / filename

        lines = [
            f"# Evaluation: {evaluation.company}",
            "",
            f"**Overall Score: {evaluation.overall_score}/5 ({evaluation.score_label})**",
            f"- Article: {evaluation.article_filename}",
            f"- Model: {evaluation.model_used}",
            f"- Date: {evaluation.evaluated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Category Scores",
            "",
        ]
        for cs in evaluation.category_scores:
            lines.append(f"### {cs.category_name}: {cs.score}/5")
            lines.append("")
            lines.append(f"{cs.reasoning}")
            lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")

    def load_evaluations(self) -> List[Evaluation]:
        """Load all saved evaluations."""
        evaluations = []
        eval_dir = _evaluations_dir()
        for f in sorted(eval_dir.glob("*_eval.md"), reverse=True):
            ev = self._parse_evaluation(f)
            if ev:
                evaluations.append(ev)
        return evaluations

    def _parse_evaluation(self, path: Path) -> Optional[Evaluation]:
        """Basic parse of evaluation .md files."""
        try:
            content = path.read_text(encoding="utf-8")
            import re
            company_match = re.search(r"# Evaluation: (.+)", content)
            score_match = re.search(r"\*\*Overall Score: ([\d.]+)/5", content)
            article_match = re.search(r"- Article: (.+)", content)
            model_match = re.search(r"- Model: (.+)", content)

            return Evaluation(
                article_filename=article_match.group(1).strip() if article_match else path.stem,
                company=company_match.group(1).strip() if company_match else "Unknown",
                overall_score=float(score_match.group(1)) if score_match else 0.0,
                model_used=model_match.group(1).strip() if model_match else "",
            )
        except Exception:
            return None

    def _build_prompt(self, article: Article, category: Category) -> str:
        questions_text = "\n".join(f"  {i+1}. {q.text}" for i, q in enumerate(category.questions))
        return f"""Analyze the following article about "{article.company}" and evaluate the company on the category "{category.name}".

Category description: {category.description}

Questions to consider:
{questions_text}

Article content:
---
{article.content[:3000]}
---

Respond with a JSON object:
{{
  "score": <number 1-5, where 1=Very Poor, 2=Poor, 3=Average, 4=Good, 5=Excellent>,
  "reasoning": "<2-3 sentence explanation of why you gave this score>",
  "question_scores": [<score 1-5 for each question>]
}}"""

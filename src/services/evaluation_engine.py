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


def _load_guide() -> str:
    """Load the category classification guide for the SLM."""
    guide_path = Path(__file__).parent.parent.parent / "guides" / "category_classification.md"
    if guide_path.exists():
        return guide_path.read_text(encoding="utf-8")
    return ""


ROOT_QUESTION = "Why do customers buy from this company?"


class EvaluationEngine(QObject):
    evaluationComplete = Signal(object)  # Evaluation
    evaluationError = Signal(str)
    progressUpdate = Signal(int, int)  # current, total
    # New: step-by-step feedback signals
    stepStarted = Signal(str, str)  # step_type, question_text
    stepCompleted = Signal(str, str, str, float)  # step_type, question, answer, score
    rootAnswered = Signal(str, str)  # category_name, evidence

    def __init__(self, parent=None):
        super().__init__(parent)
        self._network = QNetworkAccessManager(self)
        self._settings = QSettings()
        self._pending_categories = []
        self._current_article = None
        self._current_scores = []
        self._current_idx = 0
        self._determined_category = None
        self._question_idx = 0
        self._current_question_scores = []
        self._current_question_answers = []

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
        """Start evaluating an article — step by step with visual feedback."""
        if not categories:
            self.evaluationError.emit("No categories defined.")
            return

        self._current_article = article
        self._pending_categories = list(categories)
        self._current_scores = []
        self._current_idx = 0
        self._determined_category = None
        self._question_idx = 0
        self._current_question_scores = []
        self._current_question_answers = []

        total_steps = 1 + sum(len(c.questions) for c in categories)  # root + all questions
        self.progressUpdate.emit(0, total_steps)

        # Step 1: Ask the root question
        self.stepStarted.emit("root", ROOT_QUESTION)
        self._ask_root_question()

    def _ask_root_question(self):
        """Ask: Why do customers buy from this company? → determine category."""
        guide = _load_guide()
        category_names = ", ".join(f'"{c.name}"' for c in self._pending_categories)

        system_prompt = "You are an expert business analyst. Classify companies into categories based on their competitive advantage. Always respond in valid JSON format."
        if guide:
            system_prompt += f"\n\nUse this classification guide:\n\n{guide}"

        prompt = f"""Read this article about "{self._current_article.company}" and answer the question:

"{ROOT_QUESTION}"

Based on the answer, determine which of these categories best describes why customers buy:
{category_names}

Article:
---
{self._current_article.content[:3000]}
---

Respond in JSON:
{{
  "answer": "<1-2 sentence answer to why customers buy>",
  "category": "<best matching category name from the list>",
  "evidence": "<direct quote or paraphrase from the article that supports your answer>"
}}"""

        self._send_request(prompt, self._handle_root_response, system_override=system_prompt)

    def _handle_root_response(self, reply: QNetworkReply):
        if reply.error() != QNetworkReply.NetworkError.NoError:
            # Fallback: evaluate all categories
            self.stepCompleted.emit("root", ROOT_QUESTION, f"Error: {reply.errorString()}", 0.0)
            self._determined_category = None
            self._start_category_evaluation()
            reply.deleteLater()
            return

        try:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            content = data.get("message", {}).get("content", "{}")
            result = json.loads(content)

            answer = result.get("answer", "Unable to determine.")
            category_name = result.get("category", "")
            evidence = result.get("evidence", "")

            # Find the matching category
            matched = None
            for cat in self._pending_categories:
                if cat.name.lower() == category_name.lower():
                    matched = cat
                    break

            if not matched:
                # Fuzzy match
                for cat in self._pending_categories:
                    if category_name.lower() in cat.name.lower() or cat.name.lower() in category_name.lower():
                        matched = cat
                        break

            self._determined_category = matched
            self.stepCompleted.emit("root", ROOT_QUESTION, answer, 0.0)
            self.rootAnswered.emit(matched.name if matched else "Unknown", evidence)

        except (json.JSONDecodeError, ValueError, KeyError):
            self._determined_category = None
            self.stepCompleted.emit("root", ROOT_QUESTION, "Could not parse response.", 0.0)

        reply.deleteLater()
        self._start_category_evaluation()

    def _start_category_evaluation(self):
        """Start evaluating questions for the determined category (or all)."""
        if self._determined_category:
            # Evaluate only the determined category's questions in detail
            self._evaluate_category_questions(self._determined_category)
        else:
            # Fallback: evaluate first category
            if self._pending_categories:
                self._evaluate_category_questions(self._pending_categories[0])
            else:
                self._finalize_evaluation()

    def _evaluate_category_questions(self, category: Category):
        """Evaluate each question in a category one by one."""
        self._current_category = category
        self._question_idx = 0
        self._current_question_scores = []
        self._current_question_answers = []
        self._evaluate_next_question()

    def _evaluate_next_question(self):
        """Process the next question in the current category."""
        category = self._current_category
        if self._question_idx >= len(category.questions):
            # All questions done for this category
            self._finalize_category()
            return

        question = category.questions[self._question_idx]
        self.stepStarted.emit("question", question.text)

        prompt = f"""Analyze this article about "{self._current_article.company}" for the category "{category.name}".

Answer this specific question: "{question.text}"

Article:
---
{self._current_article.content[:3000]}
---

Respond in JSON:
{{
  "answer": "<concise 1-2 sentence answer based on the article>",
  "score": <number 1-5 where 1=Very Poor, 5=Excellent>,
  "evidence": "<exact quote or close paraphrase from the article that supports your answer>"
}}"""

        self._send_request(prompt, self._handle_question_response)

    def _handle_question_response(self, reply: QNetworkReply):
        category = self._current_category
        question = category.questions[self._question_idx]

        answer = "Error"
        score = 0.0
        evidence = ""

        if reply.error() != QNetworkReply.NetworkError.NoError:
            answer = f"Error: {reply.errorString()}"
        else:
            try:
                data = json.loads(reply.readAll().data().decode("utf-8"))
                content = data.get("message", {}).get("content", "{}")
                result = json.loads(content)
                answer = result.get("answer", "No answer.")
                score = max(1.0, min(5.0, float(result.get("score", 0))))
                evidence = result.get("evidence", "")
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                answer = f"Parse error: {e}"

        reply.deleteLater()

        self._current_question_scores.append(score)
        self._current_question_answers.append({
            "question": question.text,
            "answer": answer,
            "score": score,
            "evidence": evidence,
        })

        self.stepCompleted.emit("question", question.text, answer, score)

        # Update progress
        completed_steps = 1 + len(self._current_question_answers)
        total_steps = 1 + len(category.questions)
        self.progressUpdate.emit(completed_steps, total_steps)

        self._question_idx += 1
        self._evaluate_next_question()

    def _finalize_category(self):
        """Finalize scores for the evaluated category and compute overall."""
        category = self._current_category
        valid_scores = [s for s in self._current_question_scores if s > 0]
        avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

        reasoning_parts = []
        for qa in self._current_question_answers:
            reasoning_parts.append(f"Q: {qa['question']} → {qa['answer']} ({qa['score']}/5)")

        self._current_scores.append(CategoryScore(
            category_name=category.name,
            score=round(avg_score, 2),
            reasoning="\n".join(reasoning_parts),
            question_scores=self._current_question_scores,
        ))

        self._finalize_evaluation()

    def _finalize_evaluation(self):
        valid_scores = [s for s in self._current_scores if s.score > 0]
        if valid_scores:
            overall = sum(s.score for s in valid_scores) / len(valid_scores)
        else:
            overall = 0.0

        evaluation = Evaluation(
            article_filename=self._current_article.filename,
            company=self._current_article.company,
            overall_score=round(overall, 2),
            category_scores=self._current_scores,
            summary=f"Category: {self._determined_category.name if self._determined_category else 'Unknown'}. "
                    f"Evaluated {len(self._current_question_answers)} questions.",
            model_used=self.model,
            evaluated_at=datetime.now(),
        )

        self._save_evaluation(evaluation)
        self.evaluationComplete.emit(evaluation)
        print(f"[EvaluationEngine] {evaluation.company}: {evaluation.overall_score}/5 ({evaluation.score_label})")

    def _send_request(self, prompt: str, handler, system_override: str = None):
        """Send a request to Ollama."""
        system_msg = system_override or "You are an expert business analyst. Evaluate companies based on articles. Always respond in valid JSON format."
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_msg},
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
        request.setTransferTimeout(120000)

        reply = self._network.post(request, payload)
        reply.finished.connect(lambda: handler(reply))

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
            f"- Category: {self._determined_category.name if self._determined_category else 'N/A'}",
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

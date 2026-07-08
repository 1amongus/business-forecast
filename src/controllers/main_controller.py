"""Main controller orchestrating articles, categories, and evaluations."""

from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl

from ..services.article_store import ArticleStore
from ..services.category_store import CategoryStore
from ..services.evaluation_engine import EvaluationEngine
from ..models import Evaluation


class MainController(QObject):
    articlesChanged = Signal()
    categoriesChanged = Signal()
    evaluationsChanged = Signal()
    evaluationProgress = Signal(int, int)
    isEvaluatingChanged = Signal()
    errorOccurred = Signal(str)
    evaluationDone = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._article_store = ArticleStore()
        self._category_store = CategoryStore()
        self._eval_engine = EvaluationEngine(self)

        self._articles = []
        self._categories = []
        self._evaluations = []
        self._is_evaluating = False
        self._current_evaluation = {}

        # Seed defaults
        self._category_store.ensure_defaults()

        # Connect signals
        self._eval_engine.evaluationComplete.connect(self._on_evaluation_complete)
        self._eval_engine.evaluationError.connect(self._on_evaluation_error)
        self._eval_engine.progressUpdate.connect(self._on_progress)

        # Load initial data
        self._refresh_all()

    # --- Properties ---
    def _get_articles(self) -> list:
        return self._articles

    articles = Property("QVariant", _get_articles, notify=articlesChanged)

    def _get_categories(self) -> list:
        return self._categories

    categories = Property("QVariant", _get_categories, notify=categoriesChanged)

    def _get_evaluations(self) -> list:
        return self._evaluations

    evaluations = Property("QVariant", _get_evaluations, notify=evaluationsChanged)

    def _get_is_evaluating(self) -> bool:
        return self._is_evaluating

    isEvaluating = Property(bool, _get_is_evaluating, notify=isEvaluatingChanged)

    def _get_current_evaluation(self) -> dict:
        return self._current_evaluation

    currentEvaluation = Property("QVariant", _get_current_evaluation, notify=evaluationDone)

    # --- Article Slots ---
    @Slot(str)
    def addArticle(self, file_url: str):
        """Add an article from file path or URL."""
        path = QUrl(file_url).toLocalFile() if file_url.startswith("file") else file_url
        try:
            self._article_store.add_article(path)
            self._refresh_articles()
            print(f"[Main] Added article: {path}")
        except Exception as e:
            self.errorOccurred.emit(str(e))

    @Slot(str)
    def removeArticle(self, filename: str):
        self._article_store.remove_article(filename)
        self._refresh_articles()

    @Slot(str, result=str)
    def getArticleContent(self, filename: str) -> str:
        return self._article_store.get_article_content(filename)

    # --- Category Slots ---
    @Slot(str)
    def addCategoryFile(self, file_url: str):
        """Import a category from a .md file."""
        path = QUrl(file_url).toLocalFile() if file_url.startswith("file") else file_url
        try:
            self._category_store.add_category_from_file(path)
            self._refresh_categories()
            print(f"[Main] Added category file: {path}")
        except Exception as e:
            self.errorOccurred.emit(str(e))

    @Slot(str)
    def removeCategory(self, name: str):
        self._category_store.remove_category(name)
        self._refresh_categories()

    @Slot()
    def resetCategories(self):
        """Reset to default categories."""
        cat_dir = self._category_store._dir
        for f in cat_dir.glob("*.md"):
            f.unlink()
        self._category_store.ensure_defaults()
        self._refresh_categories()

    # --- Evaluation Slots ---
    @Slot(str)
    def evaluateArticle(self, filename: str):
        """Run SLM evaluation on a specific article."""
        if self._is_evaluating:
            return

        article = next((a for a in self._article_store.load_articles() if a.filename == filename), None)
        if not article:
            self.errorOccurred.emit(f"Article not found: {filename}")
            return

        categories = self._category_store.load_categories()
        if not categories:
            self.errorOccurred.emit("No categories defined. Add categories first.")
            return

        self._is_evaluating = True
        self.isEvaluatingChanged.emit()
        print(f"[Main] Evaluating: {article.title} ({len(categories)} categories)")

        self._eval_engine.evaluate(article, categories)

    @Slot()
    def refreshEvaluations(self):
        self._refresh_evaluations()

    # --- Internal ---
    def _on_evaluation_complete(self, evaluation):
        self._is_evaluating = False
        self.isEvaluatingChanged.emit()

        self._current_evaluation = {
            "company": evaluation.company,
            "overallScore": evaluation.overall_score,
            "scoreLabel": evaluation.score_label,
            "articleFilename": evaluation.article_filename,
            "modelUsed": evaluation.model_used,
            "categoryScores": [
                {
                    "name": cs.category_name,
                    "score": cs.score,
                    "reasoning": cs.reasoning,
                }
                for cs in evaluation.category_scores
            ],
        }
        self.evaluationDone.emit()
        self._refresh_evaluations()

    def _on_evaluation_error(self, error: str):
        self._is_evaluating = False
        self.isEvaluatingChanged.emit()
        self.errorOccurred.emit(error)

    def _on_progress(self, current: int, total: int):
        self.evaluationProgress.emit(current, total)

    def _refresh_all(self):
        self._refresh_articles()
        self._refresh_categories()
        self._refresh_evaluations()

    def _refresh_articles(self):
        raw = self._article_store.load_articles()
        self._articles = [
            {"filename": a.filename, "title": a.title, "company": a.company,
             "preview": a.preview, "wordCount": a.word_count}
            for a in raw
        ]
        self.articlesChanged.emit()

    def _refresh_categories(self):
        raw = self._category_store.load_categories()
        self._categories = [
            {"name": c.name, "description": c.description,
             "questionCount": c.question_count, "weight": c.weight}
            for c in raw
        ]
        self.categoriesChanged.emit()

    def _refresh_evaluations(self):
        raw = self._eval_engine.load_evaluations()
        self._evaluations = [
            {"company": e.company, "overallScore": e.overall_score,
             "scoreLabel": e.score_label, "articleFilename": e.article_filename,
             "modelUsed": e.model_used}
            for e in raw
        ]
        self.evaluationsChanged.emit()

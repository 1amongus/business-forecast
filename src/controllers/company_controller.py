"""Controller for company extraction from articles."""

from PySide6.QtCore import QObject, Property, Signal, Slot

from ..services.company_extractor import CompanyExtractor
from ..services.article_store import ArticleStore


class CompanyController(QObject):
    companiesChanged = Signal()
    extractingChanged = Signal()
    extractionStatusChanged = Signal(str)  # status message

    def __init__(self, article_store: ArticleStore, parent=None):
        super().__init__(parent)
        self._article_store = article_store
        self._extractor = CompanyExtractor(self)
        self._companies = {}  # filename -> list of company dicts
        self._is_extracting = False
        self._pending_count = 0
        self._completed_count = 0

        self._extractor.extractionComplete.connect(self._on_complete)
        self._extractor.extractionError.connect(self._on_error)

    # --- Properties ---
    def _get_companies(self) -> dict:
        return self._companies

    companies = Property("QVariant", _get_companies, notify=companiesChanged)

    def _get_is_extracting(self) -> bool:
        return self._is_extracting

    isExtracting = Property(bool, _get_is_extracting, notify=extractingChanged)

    # --- Slots ---
    @Slot(str)
    def extractFromArticle(self, filename: str):
        """Extract companies from a single article (fast regex)."""
        articles = self._article_store.load_articles()
        article = next((a for a in articles if a.filename == filename), None)
        if not article:
            self.extractionStatusChanged.emit(f"Article not found: {filename}")
            return

        self.extractionStatusChanged.emit(f"Extracting companies from: {article.title}...")
        self._extractor.extract(article, deep=False)

    @Slot(str)
    def deepExtractFromArticle(self, filename: str):
        """Extract companies using SLM (slower, more accurate)."""
        articles = self._article_store.load_articles()
        article = next((a for a in articles if a.filename == filename), None)
        if not article:
            self.extractionStatusChanged.emit(f"Article not found: {filename}")
            return

        self._is_extracting = True
        self._pending_count = 1
        self._completed_count = 0
        self.extractingChanged.emit()
        self.extractionStatusChanged.emit(f"🧠 Deep scan (SLM): {article.title}...")
        self._extractor.extract(article, deep=True)

    @Slot()
    def extractFromAll(self):
        """Extract companies from all articles (fast regex)."""
        articles = self._article_store.load_articles()
        if not articles:
            self.extractionStatusChanged.emit("No articles found.")
            return

        self.extractionStatusChanged.emit(f"⚡ Fast-extracting companies from {len(articles)} articles...")
        self._extractor.extract_batch(articles, deep=False)
        self.extractionStatusChanged.emit(f"✅ Done — processed {len(articles)} articles")

    @Slot(str, result="QVariant")
    def getCompaniesForArticle(self, filename: str) -> list:
        """Get extracted companies for a specific article."""
        return self._companies.get(filename, [])

    @Slot(result="QVariant")
    def getAllSubjects(self) -> list:
        """Get all primary subject companies across all articles."""
        subjects = []
        seen = set()
        for filename, companies in self._companies.items():
            for c in companies:
                if c["role"] == "subject" and c["name"] not in seen:
                    subjects.append({**c, "articleFilename": filename})
                    seen.add(c["name"])
        return subjects

    # --- Internal ---
    def _on_complete(self, filename: str, companies: list):
        self._companies[filename] = companies
        self._completed_count += 1
        self.companiesChanged.emit()

        status = f"✅ {filename}: {len(companies)} companies found"
        if self._completed_count >= self._pending_count:
            self._is_extracting = False
            self.extractingChanged.emit()
            status += f" — All done ({self._completed_count} articles processed)"

        self.extractionStatusChanged.emit(status)

    def _on_error(self, filename: str, error: str):
        self._companies[filename] = [{"name": "Extraction failed", "ticker": "", "role": "error", "description": error}]
        self._completed_count += 1
        self.companiesChanged.emit()

        if self._completed_count >= self._pending_count:
            self._is_extracting = False
            self.extractingChanged.emit()

        self.extractionStatusChanged.emit(f"❌ {filename}: {error}")

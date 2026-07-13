"""Company extraction service — fast heuristic + optional SLM deep scan."""

import json
import re
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QObject, Signal, QSettings, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from ..models import Article


# Common suffixes that identify company names
_COMPANY_SUFFIXES = r'(?:Inc\.?|Corp\.?|Co\.?|Ltd\.?|LLC|L\.P\.|Group|Holdings|Technologies|Therapeutics|Pharma|Semiconductor|Motors|Energy|Financial|Capital|Partners|Enterprises|Systems|Networks|Dynamics|Labs|Biotech|Studios|Media|Airlines|Airways|Brands)'
_COMPANY_PATTERN = re.compile(
    rf'([A-Z][A-Za-z&\.\'\-]+(?:\s+[A-Z][A-Za-z&\.\'\-]+){{0,4}}\s+{_COMPANY_SUFFIXES})',
)
# Pattern for "Company reported/announced/said" style
_VERB_PATTERN = re.compile(
    r'([A-Z][A-Za-z&\.\'\-]+(?:\s+[A-Z][A-Za-z&\.\'\-]+){0,3})\s+(?:reported|announced|said|plans|expects|unveiled|launched|disclosed|revealed|agreed|acquired|raised|posted|earned|generated|sold|bought)',
)
# Ticker pattern: (AAPL), (NVDA), (TSM)
_TICKER_PATTERN = re.compile(r'\(([A-Z]{1,5})\)')
# Title-based: extract from "# Title" or WSJ filename pattern
_TITLE_COMPANY_PATTERN = re.compile(r"(?:WSJ\s*-\s*)?(.+?)(?:\s+(?:Shares?|Stock|Reports?|Posts?|Plans?|Announces?|Sees?|Faces?|Bets?|Moves?|Looks?|Wins?|Cuts?|Gets?|Is|Are|Has|Had|Will|Could|May|Surges?|Drops?|Falls?|Rises?|Soars?|Slides?|Climbs?))", re.IGNORECASE)


def _fast_extract(article: Article) -> List[dict]:
    """Fast regex-based company extraction — runs instantly."""
    text = article.content[:3000]
    title = article.title
    companies = {}  # name -> dict

    # 1. Extract from title first (likely the subject)
    title_match = _TITLE_COMPANY_PATTERN.match(title)
    subject_name = None
    if title_match:
        subject_name = title_match.group(1).strip().rstrip(" -—")
        if len(subject_name) > 2:
            companies[subject_name] = {
                "name": subject_name, "ticker": "", "role": "subject", "description": ""
            }

    # 2. Find companies with suffixes (Inc., Corp., etc.)
    for match in _COMPANY_PATTERN.finditer(text):
        name = match.group(1).strip()
        if name not in companies and len(name) > 3:
            companies[name] = {
                "name": name, "ticker": "", "role": "mentioned", "description": ""
            }

    # 3. Find "Company said/announced" patterns
    for match in _VERB_PATTERN.finditer(text[:1500]):
        name = match.group(1).strip()
        if len(name) > 2 and name not in ("The", "A", "An", "Its", "This", "That", "We", "They", "He", "She"):
            if name not in companies:
                # If found in first 500 chars, likely the subject
                role = "subject" if match.start() < 500 and not subject_name else "mentioned"
                companies[name] = {
                    "name": name, "ticker": "", "role": role, "description": ""
                }

    # 4. Extract tickers and associate with nearby company names
    for match in _TICKER_PATTERN.finditer(text):
        ticker = match.group(1)
        # Find the closest company name before this ticker
        before = text[max(0, match.start()-80):match.start()]
        for name in reversed(list(companies.keys())):
            if name in before:
                companies[name]["ticker"] = ticker
                break

    # 5. Promote first company found to subject if none set
    result = list(companies.values())
    has_subject = any(c["role"] == "subject" for c in result)
    if result and not has_subject:
        result[0]["role"] = "subject"

    return result


class CompanyInfo:
    """Extracted company information."""
    def __init__(self, name: str, ticker: str = "", role: str = "subject",
                 description: str = ""):
        self.name = name
        self.ticker = ticker
        self.role = role
        self.description = description

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ticker": self.ticker,
            "role": self.role,
            "description": self.description,
        }


class CompanyExtractor(QObject):
    """Extracts companies from articles — fast mode (regex) or deep mode (SLM)."""
    extractionComplete = Signal(str, list)  # filename, list of CompanyInfo dicts
    extractionError = Signal(str, str)  # filename, error message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._network = QNetworkAccessManager(self)
        self._settings = QSettings()
        self._queue = []
        self._is_processing = False

    @property
    def model(self) -> str:
        return self._settings.value("slm/model", "phi3:mini")

    @property
    def base_url(self) -> str:
        return self._settings.value("slm/baseUrl", "http://localhost:11434")

    @property
    def temperature(self) -> float:
        return float(self._settings.value("slm/temperature", 0.2))

    def extract(self, article: Article, deep: bool = False):
        """Extract companies from a single article. Fast mode by default."""
        if deep:
            self._queue.append(article)
            if not self._is_processing:
                self._process_next()
        else:
            companies = _fast_extract(article)
            if companies:
                self.extractionComplete.emit(article.filename, companies)
                print(f"[CompanyExtractor] FAST {article.filename}: {len(companies)} companies — primary: {companies[0]['name']}")
            else:
                self.extractionError.emit(article.filename, "No companies found")

    def extract_batch(self, articles: List[Article], deep: bool = False):
        """Extract companies from all articles. Fast mode by default."""
        if deep:
            self._queue.extend(articles)
            if not self._is_processing:
                self._process_next()
        else:
            for article in articles:
                self.extract(article, deep=False)

    def _process_next(self):
        if not self._queue:
            self._is_processing = False
            return

        self._is_processing = True
        article = self._queue.pop(0)
        self._current_article = article

        # Use first 2000 chars for extraction (enough context, faster response)
        text_sample = article.content[:2000]

        prompt = f"""Read this article and identify ALL companies mentioned. For each company, determine:
1. The company name (official name)
2. Stock ticker symbol (if known, otherwise "")
3. Role in the article: "subject" (the main company being discussed), "competitor", "partner", "customer", "mentioned" (briefly referenced)
4. A one-line description of what the company does

Article:
---
{text_sample}
---

Respond in JSON:
{{
  "companies": [
    {{
      "name": "<company name>",
      "ticker": "<stock ticker or empty string>",
      "role": "<subject|competitor|partner|customer|mentioned>",
      "description": "<what the company does, 1 sentence>"
    }}
  ]
}}

Important: List the PRIMARY subject company first. Include ALL companies mentioned, even briefly."""

        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a financial analyst. Extract company information from articles accurately. Always respond in valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": 1024,
            },
            "format": "json",
        }).encode("utf-8")

        request = QNetworkRequest(QUrl(f"{self.base_url}/api/chat"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        request.setTransferTimeout(90000)

        reply = self._network.post(request, payload)
        reply.finished.connect(lambda: self._handle_response(reply))

    def _handle_response(self, reply: QNetworkReply):
        article = self._current_article

        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.extractionError.emit(article.filename, reply.errorString())
            reply.deleteLater()
            self._process_next()
            return

        try:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            content = data.get("message", {}).get("content", "{}")
            result = json.loads(content)

            companies = []
            for c in result.get("companies", []):
                info = CompanyInfo(
                    name=c.get("name", "Unknown"),
                    ticker=c.get("ticker", ""),
                    role=c.get("role", "mentioned"),
                    description=c.get("description", ""),
                )
                companies.append(info.to_dict())

            if companies:
                self.extractionComplete.emit(article.filename, companies)
                print(f"[CompanyExtractor] {article.filename}: found {len(companies)} companies — primary: {companies[0]['name']}")
            else:
                self.extractionError.emit(article.filename, "No companies found in article")

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.extractionError.emit(article.filename, f"Parse error: {e}")

        reply.deleteLater()
        self._process_next()

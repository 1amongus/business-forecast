"""PDF-to-Markdown ingestion service.

Reads PDF files from a watched folder, extracts text, and saves as .md files
into the articles directory. Tracks which files have been processed.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import fitz  # PyMuPDF

from PySide6.QtCore import QStandardPaths


def _data_dir() -> Path:
    path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _articles_dir() -> Path:
    path = _data_dir() / "articles"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _manifest_path() -> Path:
    return _data_dir() / "ingestion_manifest.json"


def _load_manifest() -> dict:
    path = _manifest_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"processed": [], "source_folder": "", "last_run": None}


def _save_manifest(manifest: dict) -> None:
    path = _manifest_path()
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    doc = fitz.open(str(pdf_path))
    pages = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages.append(text)
    doc.close()
    return "\n\n".join(pages)


def pdf_to_markdown(pdf_path: Path) -> str:
    """Convert a PDF to a clean markdown document."""
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text.strip():
        return ""

    # Clean up the text
    lines = raw_text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            continue
        # Skip common PDF artifacts
        if re.match(r"^(Page \d+|https?://|www\.|©|\d+/\d+/\d+)$", line):
            continue
        cleaned.append(line)

    text = "\n".join(cleaned).strip()

    # Try to extract title from filename or first line
    title = _extract_title_from_filename(pdf_path.stem)

    md = f"# {title}\n\n"
    md += f"*Source: {pdf_path.name}*\n"
    md += f"*Ingested: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    md += "---\n\n"
    md += text

    return md


def _extract_title_from_filename(stem: str) -> str:
    """Extract a clean title from WSJ-style filenames."""
    # Pattern: "WSJ - Title Here - WSJ - 2026-07-08 HHMMSS"
    match = re.match(r"^WSJ\s*-\s*(.+?)\s*-\s*WSJ\s*-\s*\d{4}", stem)
    if match:
        return match.group(1).strip()
    # Fallback: strip common prefixes
    title = stem.replace("WSJ - ", "").replace(" - WSJ", "")
    # Remove trailing timestamps
    title = re.sub(r"\s*-?\s*\d{4}-\d{2}-\d{2}\s*\d*$", "", title)
    return title.strip() or stem


class IngestionService:
    def __init__(self, source_folder: str = ""):
        self._manifest = _load_manifest()
        if source_folder:
            self._manifest["source_folder"] = source_folder
            _save_manifest(self._manifest)

    @property
    def source_folder(self) -> str:
        return self._manifest.get("source_folder", "")

    @source_folder.setter
    def source_folder(self, value: str):
        self._manifest["source_folder"] = value
        _save_manifest(self._manifest)

    @property
    def processed_files(self) -> List[str]:
        return self._manifest.get("processed", [])

    @property
    def last_run(self) -> str:
        return self._manifest.get("last_run", "Never")

    def scan_new_files(self) -> List[str]:
        """Find PDFs in source folder that haven't been processed yet."""
        folder = Path(self.source_folder)
        if not folder.exists():
            return []

        processed = set(self._manifest.get("processed", []))
        new_files = []
        for pdf in sorted(folder.glob("*.pdf")):
            if pdf.name not in processed:
                new_files.append(pdf.name)

        return new_files

    def process_files(self, filenames: List[str] = None) -> List[Tuple[str, bool, str]]:
        """Process PDF files into .md articles.
        
        Returns list of (filename, success, output_name_or_error).
        """
        folder = Path(self.source_folder)
        if not folder.exists():
            return [("", False, f"Source folder not found: {self.source_folder}")]

        if filenames is None:
            filenames = self.scan_new_files()

        results = []
        for filename in filenames:
            pdf_path = folder / filename
            if not pdf_path.exists():
                results.append((filename, False, "File not found"))
                continue

            try:
                md_content = pdf_to_markdown(pdf_path)
                if not md_content.strip():
                    results.append((filename, False, "No text extracted"))
                    continue

                # Save as .md in articles dir
                md_name = pdf_path.stem[:80] + ".md"
                md_name = re.sub(r'[<>:"/\\|?*]', '_', md_name)
                output_path = _articles_dir() / md_name

                counter = 1
                while output_path.exists():
                    output_path = _articles_dir() / f"{pdf_path.stem[:75]}_{counter}.md"
                    counter += 1

                output_path.write_text(md_content, encoding="utf-8")

                # Mark as processed
                if filename not in self._manifest["processed"]:
                    self._manifest["processed"].append(filename)

                results.append((filename, True, output_path.name))

            except Exception as e:
                results.append((filename, False, str(e)))

        self._manifest["last_run"] = datetime.now().isoformat()
        _save_manifest(self._manifest)
        return results

    def get_stats(self) -> dict:
        """Get ingestion statistics."""
        folder = Path(self.source_folder) if self.source_folder else None
        total_pdfs = len(list(folder.glob("*.pdf"))) if folder and folder.exists() else 0
        processed = len(self._manifest.get("processed", []))
        pending = total_pdfs - processed

        return {
            "sourceFolder": self.source_folder,
            "totalPdfs": total_pdfs,
            "processed": processed,
            "pending": max(0, pending),
            "lastRun": self.last_run,
        }

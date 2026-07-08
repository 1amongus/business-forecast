"""Controller for PDF ingestion pipeline."""

from PySide6.QtCore import QObject, Property, Signal, Slot

from ..services.ingestion_service import IngestionService


class IngestionController(QObject):
    statsChanged = Signal()
    pendingFilesChanged = Signal()
    processingChanged = Signal()
    resultsChanged = Signal()

    def __init__(self, default_folder: str = "", parent=None):
        super().__init__(parent)
        self._service = IngestionService(default_folder)
        self._is_processing = False
        self._pending_files = []
        self._results = []
        self._stats = self._service.get_stats()

        # Auto-scan on init
        self._refresh_pending()

    # --- Properties ---
    def _get_stats(self) -> dict:
        return self._stats

    stats = Property("QVariant", _get_stats, notify=statsChanged)

    def _get_pending_files(self) -> list:
        return self._pending_files

    pendingFiles = Property("QVariant", _get_pending_files, notify=pendingFilesChanged)

    def _get_is_processing(self) -> bool:
        return self._is_processing

    isProcessing = Property(bool, _get_is_processing, notify=processingChanged)

    def _get_results(self) -> list:
        return self._results

    results = Property("QVariant", _get_results, notify=resultsChanged)

    # --- Slots ---
    @Slot()
    def scan(self):
        """Scan source folder for new PDF files."""
        self._refresh_pending()
        self._stats = self._service.get_stats()
        self.statsChanged.emit()

    @Slot()
    def processAll(self):
        """Process all pending PDF files into .md articles."""
        if self._is_processing:
            return

        self._is_processing = True
        self.processingChanged.emit()

        raw_results = self._service.process_files()
        self._results = [
            {"filename": r[0], "success": r[1], "output": r[2]}
            for r in raw_results
        ]
        self.resultsChanged.emit()

        self._is_processing = False
        self.processingChanged.emit()

        self._refresh_pending()
        self._stats = self._service.get_stats()
        self.statsChanged.emit()

        success_count = sum(1 for r in raw_results if r[1])
        print(f"[Ingestion] Processed {success_count}/{len(raw_results)} files")

    @Slot(str)
    def setSourceFolder(self, folder: str):
        """Update the source folder path."""
        from PySide6.QtCore import QUrl
        path = QUrl(folder).toLocalFile() if folder.startswith("file") else folder
        self._service.source_folder = path
        self.scan()

    @Slot(str)
    def processSingle(self, filename: str):
        """Process a single PDF file."""
        if self._is_processing:
            return

        self._is_processing = True
        self.processingChanged.emit()

        raw_results = self._service.process_files([filename])
        self._results = [
            {"filename": r[0], "success": r[1], "output": r[2]}
            for r in raw_results
        ]
        self.resultsChanged.emit()

        self._is_processing = False
        self.processingChanged.emit()

        self._refresh_pending()
        self._stats = self._service.get_stats()
        self.statsChanged.emit()

    def _refresh_pending(self):
        self._pending_files = [
            {"name": f} for f in self._service.scan_new_files()
        ]
        self.pendingFilesChanged.emit()

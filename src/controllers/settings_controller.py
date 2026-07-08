"""Settings controller for SLM configuration."""

from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl, QSettings
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import json


class SettingsController(QObject):
    settingsChanged = Signal()
    modelsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = QSettings()
        self._network = QNetworkAccessManager(self)
        self._available_models = []

    def _get_model(self) -> str:
        return self._settings.value("slm/model", "phi3:mini")

    model = Property(str, _get_model, notify=settingsChanged)

    def _get_base_url(self) -> str:
        return self._settings.value("slm/baseUrl", "http://localhost:11434")

    baseUrl = Property(str, _get_base_url, notify=settingsChanged)

    def _get_temperature(self) -> float:
        return float(self._settings.value("slm/temperature", 0.3))

    temperature = Property(float, _get_temperature, notify=settingsChanged)

    def _get_max_tokens(self) -> int:
        return int(self._settings.value("slm/maxTokens", 512))

    maxTokens = Property(int, _get_max_tokens, notify=settingsChanged)

    def _get_available_models(self) -> list:
        return self._available_models

    availableModels = Property("QVariant", _get_available_models, notify=modelsChanged)

    @Slot(str)
    def setModel(self, value: str):
        self._settings.setValue("slm/model", value)
        self.settingsChanged.emit()

    @Slot(str)
    def setBaseUrl(self, value: str):
        self._settings.setValue("slm/baseUrl", value)
        self.settingsChanged.emit()

    @Slot(float)
    def setTemperature(self, value: float):
        self._settings.setValue("slm/temperature", max(0.0, min(2.0, value)))
        self.settingsChanged.emit()

    @Slot(int)
    def setMaxTokens(self, value: int):
        self._settings.setValue("slm/maxTokens", max(32, min(4096, value)))
        self.settingsChanged.emit()

    @Slot()
    def fetchModels(self):
        base_url = self._get_base_url()
        request = QNetworkRequest(QUrl(f"{base_url}/api/tags"))
        reply = self._network.get(request)
        reply.finished.connect(lambda: self._handle_models(reply))

    def _handle_models(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = json.loads(reply.readAll().data().decode("utf-8"))
            models = data.get("models", [])
            self._available_models = [
                {"name": m["name"], "size": f"{m.get('size', 0) / 1e9:.1f} GB"}
                for m in models
            ]
        else:
            self._available_models = [{"name": "Cannot reach Ollama", "size": ""}]
        self.modelsChanged.emit()
        reply.deleteLater()

"""Business Forecast — Company Success Predictor."""

import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from src.controllers.main_controller import MainController
from src.controllers.settings_controller import SettingsController
from src.controllers.ingestion_controller import IngestionController
from src.controllers.company_controller import CompanyController


def main():
    QCoreApplication.setOrganizationName("BusinessForecast")
    QCoreApplication.setApplicationName("Business Forecast")
    QCoreApplication.setApplicationVersion("1.0.0")

    app = QGuiApplication(sys.argv)
    QQuickStyle.setStyle("Material")

    # Controllers
    main_controller = MainController()
    settings_controller = SettingsController()
    ingestion_controller = IngestionController(default_folder=r"Q:\WSJ")
    company_controller = CompanyController(main_controller._article_store)

    # QML
    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()
    ctx.setContextProperty("mainController", main_controller)
    ctx.setContextProperty("settingsController", settings_controller)
    ctx.setContextProperty("ingestionController", ingestion_controller)
    ctx.setContextProperty("companyController", company_controller)

    qml_dir = Path(__file__).parent / "src" / "ui" / "qml"
    qml_file = qml_dir / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        print("[main] ERROR: Failed to load QML")
        sys.exit(1)

    print("[main] Business Forecast started")
    print(f"[main] Data: {main_controller._article_store.articles_directory.parent}")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

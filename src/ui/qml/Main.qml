import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "pages"

ApplicationWindow {
    id: root
    visible: true
    width: 1200
    height: 800
    title: "Business Forecast — Company Success Predictor"
    color: "#0f1117"

    Material.theme: Material.Dark
    Material.accent: "#f59e0b"

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Sidebar navigation
        Rectangle {
            Layout.fillHeight: true
            Layout.preferredWidth: 200
            color: "#0a0c10"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 6

                Label {
                    text: "⚡ Business\n   Forecast"
                    font.pixelSize: 17
                    font.bold: true
                    color: "#f59e0b"
                    padding: 12
                }

                Rectangle { Layout.fillWidth: true; height: 1; color: "#1f2937" }

                Repeater {
                    model: [
                        {icon: "📥", label: "Ingest"},
                        {icon: "📰", label: "Articles"},
                        {icon: "📋", label: "Categories"},
                        {icon: "🔍", label: "Evaluate"},
                        {icon: "📊", label: "Results"},
                        {icon: "⚙️", label: "Settings"}
                    ]
                    delegate: Button {
                        Layout.fillWidth: true
                        text: modelData.icon + "  " + modelData.label
                        flat: true
                        highlighted: stackView.currentIndex === index
                        font.pixelSize: 13
                        onClicked: stackView.currentIndex = index
                    }
                }

                Item { Layout.fillHeight: true }

                Label {
                    text: "Powered by Ollama"
                    font.pixelSize: 9
                    color: "#4b5563"
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }

        // Main content
        StackLayout {
            id: stackView
            Layout.fillWidth: true
            Layout.fillHeight: true

            IngestionPage {}
            ArticlesPage {}
            CategoriesPage {}
            EvaluatePage {}
            ResultsPage {}
            SettingsPage {}
        }
    }
}

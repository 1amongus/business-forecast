import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Page {
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            Label { text: "📰 Articles"; font.pixelSize: 22; font.bold: true; color: "#f9fafb"; Layout.fillWidth: true }
            Button {
                text: "➕ Add Article (.md)"
                highlighted: true
                onClicked: articleDialog.open()
            }
        }

        Label {
            text: "Upload WSJ articles as .md files. The AI will analyze these to score companies."
            color: "#9ca3af"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        Label {
            text: "No articles yet. Click 'Add Article' to get started."
            color: "#6b7280"
            font.italic: true
            visible: !mainController || mainController.articles.length === 0
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 8
            model: mainController ? mainController.articles : []

            delegate: Rectangle {
                required property var modelData
                required property int index
                width: ListView.view.width
                height: 90
                radius: 10
                color: "#1f2937"
                border.color: index === ListView.view.currentIndex ? "#f59e0b" : "#374151"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 4

                    RowLayout {
                        Layout.fillWidth: true
                        Label { text: modelData.title; font.bold: true; color: "#f9fafb"; font.pixelSize: 13; Layout.fillWidth: true; elide: Text.ElideRight }
                        Label { text: modelData.wordCount + " words"; color: "#6b7280"; font.pixelSize: 10 }
                        Button {
                            text: "🔍"
                            flat: true
                            implicitWidth: 28; implicitHeight: 28
                            onClicked: { stackView.currentIndex = 2 }
                        }
                        Button {
                            text: "🗑️"
                            flat: true
                            implicitWidth: 28; implicitHeight: 28
                            onClicked: { if (mainController) mainController.removeArticle(modelData.filename) }
                        }
                    }
                    Label { text: "🏢 " + modelData.company; color: "#f59e0b"; font.pixelSize: 11 }
                    Label { text: modelData.preview; color: "#9ca3af"; font.pixelSize: 10; elide: Text.ElideRight; Layout.fillWidth: true }
                }
            }
        }
    }

    FileDialog {
        id: articleDialog
        title: "Select article (.md)"
        nameFilters: ["Markdown files (*.md)", "All files (*)"]
        onAccepted: { if (mainController) mainController.addArticle(selectedFile.toString()) }
    }
}

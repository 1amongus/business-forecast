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
            Label { text: "📋 Scoring Categories"; font.pixelSize: 22; font.bold: true; color: "#f9fafb"; Layout.fillWidth: true }
            Button {
                text: "➕ Import Category (.md)"
                highlighted: true
                onClicked: categoryDialog.open()
            }
            Button {
                text: "↺ Reset Defaults"
                onClicked: { if (mainController) mainController.resetCategories() }
            }
        }

        Label {
            text: "Each category contains questions the AI uses to evaluate companies. Edit by replacing .md files."
            color: "#9ca3af"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 8
            model: mainController ? mainController.categories : []

            delegate: Rectangle {
                required property var modelData
                required property int index
                width: ListView.view.width
                height: 80
                radius: 10
                color: "#1f2937"
                border.color: "#374151"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 12

                    Rectangle {
                        width: 44; height: 44; radius: 22
                        color: "#292524"
                        Label { anchors.centerIn: parent; text: (index + 1).toString(); font.bold: true; color: "#f59e0b"; font.pixelSize: 16 }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Label { text: modelData.name; font.bold: true; color: "#f9fafb"; font.pixelSize: 13 }
                        Label { text: modelData.description; color: "#9ca3af"; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
                        Label { text: modelData.questionCount + " questions • weight: " + modelData.weight.toFixed(1); color: "#6b7280"; font.pixelSize: 10 }
                    }

                    Button {
                        text: "🗑️"
                        flat: true
                        implicitWidth: 28; implicitHeight: 28
                        onClicked: { if (mainController) mainController.removeCategory(modelData.name) }
                    }
                }
            }
        }
    }

    FileDialog {
        id: categoryDialog
        title: "Select category file (.md)"
        nameFilters: ["Markdown files (*.md)"]
        onAccepted: { if (mainController) mainController.addCategoryFile(selectedFile.toString()) }
    }
}

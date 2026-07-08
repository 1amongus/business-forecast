import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Page {
    id: categoriesPage
    property string editingCategory: ""
    property string editingContent: ""

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

        // Root question banner
        Rectangle {
            Layout.fillWidth: true
            height: 52
            radius: 8
            color: "#292524"
            border.color: "#f59e0b"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8
                Label { text: "🔑"; font.pixelSize: 16 }
                Label {
                    text: "Root Question: Why do customers buy from this company?"
                    color: "#fbbf24"
                    font.bold: true
                    font.pixelSize: 13
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
            }
        }

        Label {
            text: "Categories are determined by the answer to the root question above. Click ✏️ to edit a category's .md file directly."
            color: "#9ca3af"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        // Category list (hidden when editing)
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 8
            visible: editingCategory === ""
            model: mainController ? mainController.categories : []

            delegate: Rectangle {
                required property var modelData
                required property int index
                width: ListView.view.width
                height: col.implicitHeight + 24
                radius: 10
                color: "#1f2937"
                border.color: "#374151"

                ColumnLayout {
                    id: col
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 12
                    spacing: 6

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8

                        Rectangle {
                            width: 36; height: 36; radius: 18
                            color: "#292524"
                            Label { anchors.centerIn: parent; text: (index + 1).toString(); font.bold: true; color: "#f59e0b"; font.pixelSize: 14 }
                        }

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Label { text: modelData.name; font.bold: true; color: "#f9fafb"; font.pixelSize: 13 }
                            Label { text: modelData.description; color: "#9ca3af"; font.pixelSize: 11; elide: Text.ElideRight; Layout.fillWidth: true }
                        }

                        Button {
                            text: "✏️"
                            flat: true
                            implicitWidth: 30; implicitHeight: 28
                            onClicked: {
                                if (mainController) {
                                    editingCategory = modelData.name
                                    editingContent = mainController.getCategoryContent(modelData.name)
                                }
                            }
                        }
                        Button {
                            text: "🗑️"
                            flat: true
                            implicitWidth: 30; implicitHeight: 28
                            onClicked: { if (mainController) mainController.removeCategory(modelData.name) }
                        }
                    }

                    // Show questions inline
                    Repeater {
                        model: modelData.questions || []
                        Label {
                            required property var modelData
                            text: "  • " + modelData
                            color: "#d1d5db"
                            font.pixelSize: 11
                            wrapMode: Text.WordWrap
                            Layout.fillWidth: true
                            Layout.leftMargin: 44
                        }
                    }
                }
            }
        }

        // Inline editor (shown when editing)
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12
            visible: editingCategory !== ""

            RowLayout {
                Layout.fillWidth: true
                Label { text: "✏️ Editing: " + editingCategory; font.bold: true; color: "#fbbf24"; font.pixelSize: 14; Layout.fillWidth: true }
                Button {
                    text: "💾 Save"
                    highlighted: true
                    onClicked: {
                        if (mainController) mainController.saveCategoryContent(editingCategory, editorArea.text)
                        editingCategory = ""
                        editingContent = ""
                    }
                }
                Button {
                    text: "❌ Cancel"
                    onClicked: { editingCategory = ""; editingContent = "" }
                }
            }

            Label {
                text: "Edit the Markdown below. Use YAML frontmatter for name/description/weight, and bullet points (- ) for questions."
                color: "#6b7280"
                font.pixelSize: 11
                wrapMode: Text.WordWrap
                Layout.fillWidth: true
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.fillHeight: true

                TextArea {
                    id: editorArea
                    text: editingContent
                    font.family: "Consolas"
                    font.pixelSize: 12
                    color: "#e5e7eb"
                    background: Rectangle { color: "#111827"; radius: 8; border.color: "#374151" }
                    wrapMode: TextEdit.Wrap
                    selectByMouse: true
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

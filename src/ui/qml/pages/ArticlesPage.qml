import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Page {
    id: articlesPage
    property string selectedArticle: ""
    property var selectedCompanies: []

    function refreshCompanies() {
        if (companyController && selectedArticle !== "")
            selectedCompanies = companyController.getCompaniesForArticle(selectedArticle)
        else
            selectedCompanies = []
    }

    onSelectedArticleChanged: refreshCompanies()

    Connections {
        target: companyController || null
        function onCompaniesChanged() { refreshCompanies() }
        function onExtractionStatusChanged(msg) { statusLabel.text = msg }
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            Label { text: "📰 Articles"; font.pixelSize: 22; font.bold: true; color: "#f9fafb"; Layout.fillWidth: true }
            Button {
                text: "🏢 Extract Companies (All)"
                enabled: companyController && !companyController.isExtracting && mainController && mainController.articles.length > 0
                onClicked: { if (companyController) companyController.extractFromAll() }
            }
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

        // Extraction status
        RowLayout {
            Layout.fillWidth: true
            visible: companyController && (companyController.isExtracting || statusLabel.text !== "")
            spacing: 8
            BusyIndicator {
                running: companyController ? companyController.isExtracting : false
                visible: running
                Layout.preferredWidth: 20; Layout.preferredHeight: 20
            }
            Label {
                id: statusLabel
                text: ""
                color: "#9ca3af"
                font.pixelSize: 11
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }
        }

        Label {
            text: "No articles yet. Click 'Add Article' or use the Ingest page to import PDFs."
            color: "#6b7280"
            font.italic: true
            visible: !mainController || mainController.articles.length === 0
        }

        // Split view: article list + company detail
        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Horizontal

            // Article list
            ListView {
                SplitView.fillWidth: true
                SplitView.minimumWidth: 400
                clip: true
                spacing: 8
                model: mainController ? mainController.articles : []

                delegate: Rectangle {
                    required property var modelData
                    required property int index
                    width: ListView.view.width
                    height: 90
                    radius: 10
                    color: selectedArticle === modelData.filename ? "#292524" : "#1f2937"
                    border.color: selectedArticle === modelData.filename ? "#f59e0b" : "#374151"

                    MouseArea {
                        anchors.fill: parent
                        onClicked: { selectedArticle = modelData.filename }
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 4

                        RowLayout {
                            Layout.fillWidth: true
                            Label { text: modelData.title; font.bold: true; color: "#f9fafb"; font.pixelSize: 13; Layout.fillWidth: true; elide: Text.ElideRight }
                            Label { text: modelData.wordCount + " words"; color: "#6b7280"; font.pixelSize: 10 }
                            Button {
                                text: "🏢"
                                flat: true
                                implicitWidth: 28; implicitHeight: 28
                                ToolTip.text: "Extract companies"
                                onClicked: {
                                    selectedArticle = modelData.filename
                                    if (companyController) companyController.extractFromArticle(modelData.filename)
                                }
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

            // Company detail panel (right side)
            Rectangle {
                SplitView.preferredWidth: 300
                SplitView.minimumWidth: 200
                color: "#111827"
                radius: 8
                visible: selectedArticle !== ""

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8

                    Label {
                        text: "🏢 Companies Identified"
                        font.bold: true; color: "#f9fafb"; font.pixelSize: 14
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Label {
                            text: selectedArticle !== "" ? "File: " + selectedArticle : ""
                            color: "#6b7280"; font.pixelSize: 9
                            elide: Text.ElideMiddle
                            Layout.fillWidth: true
                        }
                        Button {
                            text: "🧠"
                            flat: true
                            implicitWidth: 28; implicitHeight: 24
                            ToolTip.text: "Deep scan with SLM (slower)"
                            visible: selectedArticle !== ""
                            onClicked: {
                                if (companyController) companyController.deepExtractFromArticle(selectedArticle)
                            }
                        }
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        spacing: 6
                        model: selectedCompanies

                        delegate: Rectangle {
                            required property var modelData
                            required property int index
                            width: ListView.view.width
                            height: companyCol.implicitHeight + 16
                            radius: 8
                            color: modelData.role === "subject" ? "#292524" : "#1f2937"
                            border.color: modelData.role === "subject" ? "#f59e0b" : "#374151"

                            ColumnLayout {
                                id: companyCol
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.margins: 8
                                spacing: 2

                                RowLayout {
                                    Layout.fillWidth: true
                                    Label {
                                        text: modelData.name
                                        font.bold: true
                                        color: modelData.role === "subject" ? "#fbbf24" : "#e5e7eb"
                                        font.pixelSize: 12
                                    }
                                    Label {
                                        text: modelData.ticker ? ("(" + modelData.ticker + ")") : ""
                                        color: "#9ca3af"
                                        font.pixelSize: 10
                                        visible: modelData.ticker !== ""
                                    }
                                    Item { Layout.fillWidth: true }
                                    Rectangle {
                                        width: roleLabel.implicitWidth + 8; height: 18; radius: 4
                                        color: {
                                            if (modelData.role === "subject") return "#422006"
                                            if (modelData.role === "competitor") return "#450a0a"
                                            if (modelData.role === "partner") return "#052e16"
                                            return "#1e293b"
                                        }
                                        Label {
                                            id: roleLabel
                                            anchors.centerIn: parent
                                            text: modelData.role
                                            font.pixelSize: 9
                                            color: "#d1d5db"
                                        }
                                    }
                                }
                                Label {
                                    text: modelData.description
                                    color: "#9ca3af"
                                    font.pixelSize: 10
                                    wrapMode: Text.WordWrap
                                    Layout.fillWidth: true
                                    visible: modelData.description !== ""
                                }
                            }
                        }
                    }

                    // Empty state for company panel
                    Label {
                        text: "Click 🏢 on an article to extract companies."
                        color: "#6b7280"
                        font.italic: true
                        font.pixelSize: 11
                        visible: selectedCompanies.length === 0
                        wrapMode: Text.WordWrap
                        Layout.fillWidth: true
                    }
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

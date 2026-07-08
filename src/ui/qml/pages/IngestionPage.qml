import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

Page {
    Component.onCompleted: { if (ingestionController) ingestionController.scan() }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        Label { text: "📥 PDF Ingestion Pipeline"; font.pixelSize: 22; font.bold: true; color: "#f9fafb" }

        Label {
            text: "Convert PDF articles from your WSJ folder into .md files for analysis."
            color: "#9ca3af"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        // Source folder config
        GroupBox {
            title: "Source Folder"
            Layout.fillWidth: true

            RowLayout {
                anchors.fill: parent
                spacing: 12

                TextField {
                    id: folderField
                    text: ingestionController ? (ingestionController.stats.sourceFolder || "") : ""
                    placeholderText: "e.g. Q:\\WSJ"
                    Layout.fillWidth: true
                }
                Button {
                    text: "📂 Browse"
                    onClicked: folderDialog.open()
                }
                Button {
                    text: "✅ Set & Scan"
                    highlighted: true
                    onClicked: {
                        if (ingestionController) ingestionController.setSourceFolder(folderField.text)
                    }
                }
            }
        }

        // Stats cards
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Rectangle {
                Layout.fillWidth: true; height: 70; radius: 10; color: "#1f2937"
                ColumnLayout {
                    anchors.centerIn: parent
                    Label { text: ingestionController ? ingestionController.stats.totalPdfs.toString() : "0"; font.pixelSize: 28; font.bold: true; color: "#f59e0b"; Layout.alignment: Qt.AlignHCenter }
                    Label { text: "Total PDFs"; font.pixelSize: 11; color: "#9ca3af"; Layout.alignment: Qt.AlignHCenter }
                }
            }
            Rectangle {
                Layout.fillWidth: true; height: 70; radius: 10; color: "#1f2937"
                ColumnLayout {
                    anchors.centerIn: parent
                    Label { text: ingestionController ? ingestionController.stats.processed.toString() : "0"; font.pixelSize: 28; font.bold: true; color: "#34d399"; Layout.alignment: Qt.AlignHCenter }
                    Label { text: "Processed"; font.pixelSize: 11; color: "#9ca3af"; Layout.alignment: Qt.AlignHCenter }
                }
            }
            Rectangle {
                Layout.fillWidth: true; height: 70; radius: 10; color: "#1f2937"
                ColumnLayout {
                    anchors.centerIn: parent
                    Label { text: ingestionController ? ingestionController.stats.pending.toString() : "0"; font.pixelSize: 28; font.bold: true; color: "#f87171"; Layout.alignment: Qt.AlignHCenter }
                    Label { text: "Pending"; font.pixelSize: 11; color: "#9ca3af"; Layout.alignment: Qt.AlignHCenter }
                }
            }
        }

        // Actions
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Button {
                text: "🔄 Scan for New Files"
                onClicked: { if (ingestionController) ingestionController.scan() }
            }
            Button {
                text: "⚡ Process All Pending"
                highlighted: true
                enabled: ingestionController && !ingestionController.isProcessing && ingestionController.pendingFiles.length > 0
                onClicked: { if (ingestionController) ingestionController.processAll() }
            }
            BusyIndicator {
                running: ingestionController ? ingestionController.isProcessing : false
                visible: running
                Layout.preferredWidth: 32; Layout.preferredHeight: 32
            }
            Item { Layout.fillWidth: true }
            Label {
                text: "Last run: " + (ingestionController ? (ingestionController.stats.lastRun || "Never") : "Never")
                color: "#6b7280"
                font.pixelSize: 10
            }
        }

        // Pending files list
        Label {
            text: "Pending Files (" + (ingestionController ? ingestionController.pendingFiles.length : 0) + ")"
            font.bold: true; color: "#d1d5db"; font.pixelSize: 13
            visible: ingestionController && ingestionController.pendingFiles.length > 0
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 4
            visible: ingestionController && ingestionController.pendingFiles.length > 0

            model: ingestionController ? ingestionController.pendingFiles : []

            delegate: Rectangle {
                required property var modelData
                required property int index
                width: ListView.view.width
                height: 36
                radius: 6
                color: index % 2 === 0 ? "#1f2937" : "#111827"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 8
                    spacing: 8

                    Label { text: "📄"; font.pixelSize: 12 }
                    Label { text: modelData.name; color: "#e5e7eb"; font.pixelSize: 11; Layout.fillWidth: true; elide: Text.ElideMiddle }
                    Button {
                        text: "▶"
                        flat: true
                        implicitWidth: 28; implicitHeight: 24
                        onClicked: { if (ingestionController) ingestionController.processSingle(modelData.name) }
                    }
                }
            }
        }

        // Results
        Label {
            text: "Last Batch Results"
            font.bold: true; color: "#d1d5db"; font.pixelSize: 13
            visible: ingestionController && ingestionController.results.length > 0
        }

        ListView {
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(contentHeight, 150)
            clip: true
            spacing: 4
            visible: ingestionController && ingestionController.results.length > 0

            model: ingestionController ? ingestionController.results : []

            delegate: Rectangle {
                required property var modelData
                required property int index
                width: ListView.view.width
                height: 32
                radius: 4
                color: modelData.success ? "#052e16" : "#450a0a"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 6
                    Label { text: modelData.success ? "✅" : "❌"; font.pixelSize: 11 }
                    Label { text: modelData.filename; color: "#e5e7eb"; font.pixelSize: 10; Layout.fillWidth: true; elide: Text.ElideMiddle }
                    Label { text: modelData.output; color: "#9ca3af"; font.pixelSize: 9; elide: Text.ElideMiddle; Layout.preferredWidth: 200 }
                }
            }
        }

        // Empty state
        Label {
            text: ingestionController && ingestionController.stats.sourceFolder
                ? "✅ All files processed! Add new PDFs to the source folder and click Scan."
                : "Set a source folder above to begin scanning for PDFs."
            color: "#6b7280"
            font.italic: true
            visible: !ingestionController || ingestionController.pendingFiles.length === 0
        }
    }

    FolderDialog {
        id: folderDialog
        title: "Select WSJ articles folder"
        onAccepted: {
            folderField.text = selectedFolder.toString().replace("file:///", "")
            if (ingestionController) ingestionController.setSourceFolder(folderField.text)
        }
    }
}

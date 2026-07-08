import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        RowLayout {
            Layout.fillWidth: true
            Label { text: "📊 Evaluation History"; font.pixelSize: 22; font.bold: true; color: "#f9fafb"; Layout.fillWidth: true }
            Button {
                text: "↻ Refresh"
                onClicked: { if (mainController) mainController.refreshEvaluations() }
            }
        }

        Label {
            text: "No evaluations yet. Go to Evaluate tab to score a company."
            color: "#6b7280"
            font.italic: true
            visible: !mainController || mainController.evaluations.length === 0
        }

        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            spacing: 8
            model: mainController ? mainController.evaluations : []

            delegate: Rectangle {
                required property var modelData
                required property int index
                width: ListView.view.width
                height: 72
                radius: 10
                color: "#1f2937"

                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 16

                    // Score circle
                    Rectangle {
                        width: 50; height: 50; radius: 25
                        color: {
                            if (modelData.overallScore >= 4) return "#064e3b"
                            if (modelData.overallScore >= 3) return "#422006"
                            return "#450a0a"
                        }
                        Label {
                            anchors.centerIn: parent
                            text: modelData.overallScore.toFixed(1)
                            font.bold: true; font.pixelSize: 18
                            color: {
                                if (modelData.overallScore >= 4) return "#34d399"
                                if (modelData.overallScore >= 3) return "#fbbf24"
                                return "#f87171"
                            }
                        }
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Label { text: modelData.company; font.bold: true; color: "#f9fafb"; font.pixelSize: 14 }
                        Label { text: modelData.scoreLabel + " • " + modelData.modelUsed; color: "#9ca3af"; font.pixelSize: 11 }
                    }

                    Label { text: modelData.articleFilename; color: "#6b7280"; font.pixelSize: 10 }
                }
            }
        }
    }
}

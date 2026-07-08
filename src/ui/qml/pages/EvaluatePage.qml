import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        Label { text: "🔍 Evaluate Company"; font.pixelSize: 22; font.bold: true; color: "#f9fafb" }

        Label {
            text: "Select an article to evaluate. The AI will score the company across all categories."
            color: "#9ca3af"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        // Article selector
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            ComboBox {
                id: articleSelector
                Layout.fillWidth: true
                model: {
                    if (!mainController || !mainController.articles) return []
                    var names = []
                    for (var i = 0; i < mainController.articles.length; i++) {
                        names.push(mainController.articles[i].company + " — " + mainController.articles[i].title)
                    }
                    return names
                }
            }

            Button {
                text: "⚡ Evaluate"
                highlighted: true
                enabled: mainController && mainController.articles.length > 0 && !mainController.isEvaluating
                onClicked: {
                    if (mainController && articleSelector.currentIndex >= 0) {
                        mainController.evaluateArticle(mainController.articles[articleSelector.currentIndex].filename)
                    }
                }
            }

            BusyIndicator {
                running: mainController ? mainController.isEvaluating : false
                visible: running
                Layout.preferredWidth: 32
                Layout.preferredHeight: 32
            }
        }

        // Progress
        ProgressBar {
            id: progressBar
            Layout.fillWidth: true
            visible: mainController ? mainController.isEvaluating : false
            from: 0
            to: 1
            value: 0

            Connections {
                target: mainController || null
                function onEvaluationProgress(current, total) {
                    progressBar.to = total
                    progressBar.value = current
                }
            }
        }

        // Current evaluation result
        Frame {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: mainController && mainController.currentEvaluation.overallScore !== undefined

            ScrollView {
                anchors.fill: parent
                contentWidth: availableWidth

                ColumnLayout {
                    width: parent.width
                    spacing: 16

                    // Big score display
                    Rectangle {
                        Layout.fillWidth: true
                        height: 100
                        radius: 12
                        color: {
                            var score = mainController ? (mainController.currentEvaluation.overallScore || 0) : 0
                            if (score >= 4) return "#064e3b"
                            if (score >= 3) return "#1c1917"
                            return "#450a0a"
                        }

                        RowLayout {
                            anchors.centerIn: parent
                            spacing: 20

                            Label {
                                text: (mainController ? (mainController.currentEvaluation.overallScore || 0) : 0).toFixed(1)
                                font.pixelSize: 48
                                font.bold: true
                                color: {
                                    var score = mainController ? (mainController.currentEvaluation.overallScore || 0) : 0
                                    if (score >= 4) return "#34d399"
                                    if (score >= 3) return "#fbbf24"
                                    return "#f87171"
                                }
                            }
                            ColumnLayout {
                                Label { text: "/5"; font.pixelSize: 20; color: "#9ca3af" }
                                Label {
                                    text: mainController ? (mainController.currentEvaluation.scoreLabel || "") : ""
                                    font.pixelSize: 16; font.bold: true; color: "#f9fafb"
                                }
                            }
                            Item { Layout.fillWidth: true }
                            ColumnLayout {
                                Label { text: mainController ? (mainController.currentEvaluation.company || "") : ""; font.pixelSize: 16; color: "#f9fafb"; font.bold: true }
                                Label { text: "Model: " + (mainController ? (mainController.currentEvaluation.modelUsed || "") : ""); font.pixelSize: 11; color: "#6b7280" }
                            }
                        }
                    }

                    // Category breakdown
                    Repeater {
                        model: mainController ? (mainController.currentEvaluation.categoryScores || []) : []

                        delegate: Rectangle {
                            required property var modelData
                            required property int index
                            Layout.fillWidth: true
                            height: 80
                            radius: 8
                            color: "#1f2937"

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 12

                                // Score badge
                                Rectangle {
                                    width: 48; height: 48; radius: 8
                                    color: {
                                        if (modelData.score >= 4) return "#064e3b"
                                        if (modelData.score >= 3) return "#422006"
                                        return "#450a0a"
                                    }
                                    Label {
                                        anchors.centerIn: parent
                                        text: modelData.score.toFixed(1)
                                        font.bold: true; font.pixelSize: 16
                                        color: {
                                            if (modelData.score >= 4) return "#34d399"
                                            if (modelData.score >= 3) return "#fbbf24"
                                            return "#f87171"
                                        }
                                    }
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    Label { text: modelData.name; font.bold: true; color: "#f9fafb"; font.pixelSize: 12 }
                                    Label { text: modelData.reasoning; color: "#9ca3af"; font.pixelSize: 10; wrapMode: Text.WordWrap; Layout.fillWidth: true }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Empty state
        Label {
            text: mainController && mainController.articles.length === 0
                ? "📰 Add some articles first, then come back to evaluate."
                : "Select an article above and click Evaluate to get a score."
            color: "#6b7280"
            font.italic: true
            visible: !mainController || mainController.currentEvaluation.overallScore === undefined
            Layout.alignment: Qt.AlignHCenter
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    id: evaluatePage

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        Label { text: "🔍 Evaluate Company"; font.pixelSize: 22; font.bold: true; color: "#f9fafb" }

        Label {
            text: "Select an article. The AI will determine why customers buy, identify the category, then investigate each question step-by-step."
            color: "#9ca3af"
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
        }

        // Article selector + Evaluate button
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
        }

        // Progress bar
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

        // Step-by-step timeline
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: availableWidth

            ColumnLayout {
                width: parent.width
                spacing: 8

                // Live steps timeline
                Repeater {
                    model: mainController ? mainController.evalSteps : []

                    delegate: Rectangle {
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        height: stepCol.implicitHeight + 20
                        radius: 10
                        color: modelData.type === "root" ? "#1c1917" : "#1f2937"
                        border.color: {
                            if (modelData.status === "thinking") return "#f59e0b"
                            if (modelData.type === "root") return "#f59e0b"
                            if (modelData.score >= 4) return "#34d399"
                            if (modelData.score >= 3) return "#fbbf24"
                            if (modelData.score > 0) return "#f87171"
                            return "#374151"
                        }
                        border.width: modelData.status === "thinking" ? 2 : 1

                        ColumnLayout {
                            id: stepCol
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 12
                            spacing: 6

                            // Header row
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 8

                                // Step icon
                                Label {
                                    text: {
                                        if (modelData.status === "thinking") return "⏳"
                                        if (modelData.type === "root") return "🔑"
                                        if (modelData.score >= 4) return "✅"
                                        if (modelData.score >= 3) return "⚠️"
                                        if (modelData.score > 0) return "❌"
                                        return "✅"
                                    }
                                    font.pixelSize: 16
                                }

                                // Step label
                                Label {
                                    text: modelData.type === "root" ? "ROOT QUESTION" : ("Q" + index)
                                    font.bold: true
                                    font.pixelSize: 10
                                    color: modelData.type === "root" ? "#f59e0b" : "#6b7280"
                                }

                                // Question text
                                Label {
                                    text: modelData.question
                                    font.bold: true
                                    font.pixelSize: 12
                                    color: "#f9fafb"
                                    Layout.fillWidth: true
                                    wrapMode: Text.WordWrap
                                }

                                // Score badge
                                Rectangle {
                                    width: 44; height: 28; radius: 6
                                    visible: modelData.score > 0 && modelData.type !== "root"
                                    color: {
                                        if (modelData.score >= 4) return "#064e3b"
                                        if (modelData.score >= 3) return "#422006"
                                        return "#450a0a"
                                    }
                                    Label {
                                        anchors.centerIn: parent
                                        text: modelData.score > 0 ? modelData.score.toFixed(1) : ""
                                        font.bold: true; font.pixelSize: 13
                                        color: {
                                            if (modelData.score >= 4) return "#34d399"
                                            if (modelData.score >= 3) return "#fbbf24"
                                            return "#f87171"
                                        }
                                    }
                                }

                                // Thinking indicator
                                BusyIndicator {
                                    running: modelData.status === "thinking"
                                    visible: running
                                    Layout.preferredWidth: 24; Layout.preferredHeight: 24
                                }
                            }

                            // Answer (when done)
                            Label {
                                text: modelData.answer || ""
                                visible: modelData.answer !== ""
                                color: "#d1d5db"
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                                Layout.fillWidth: true
                                Layout.leftMargin: 32
                            }

                            // Category determination (root only)
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.leftMargin: 32
                                height: 32
                                radius: 6
                                color: "#292524"
                                visible: modelData.type === "root" && modelData.category !== ""

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    Label { text: "📂 Category:"; color: "#9ca3af"; font.pixelSize: 11 }
                                    Label { text: modelData.category; font.bold: true; color: "#f59e0b"; font.pixelSize: 12 }
                                    Item { Layout.fillWidth: true }
                                }
                            }

                            // Evidence highlight
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.leftMargin: 32
                                height: evidenceLabel.implicitHeight + 16
                                radius: 6
                                color: "#0f172a"
                                border.color: "#334155"
                                visible: modelData.evidence !== ""

                                Label {
                                    id: evidenceLabel
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    text: "📝 \"" + (modelData.evidence || "") + "\""
                                    color: "#94a3b8"
                                    font.italic: true
                                    font.pixelSize: 10
                                    wrapMode: Text.WordWrap
                                }
                            }
                        }
                    }
                }

                // Final score card (after completion)
                Rectangle {
                    Layout.fillWidth: true
                    height: 120
                    radius: 12
                    visible: mainController && mainController.currentEvaluation.overallScore !== undefined && !mainController.isEvaluating
                    color: {
                        var score = mainController ? (mainController.currentEvaluation.overallScore || 0) : 0
                        if (score >= 4) return "#064e3b"
                        if (score >= 3) return "#1c1917"
                        return "#450a0a"
                    }
                    border.color: "#f59e0b"
                    border.width: 2

                    RowLayout {
                        anchors.centerIn: parent
                        spacing: 24

                        ColumnLayout {
                            spacing: 0
                            Label {
                                text: "RECOMMENDATION SCORE"
                                font.pixelSize: 10
                                font.bold: true
                                color: "#9ca3af"
                                Layout.alignment: Qt.AlignHCenter
                            }
                            Label {
                                text: (mainController ? (mainController.currentEvaluation.overallScore || 0) : 0).toFixed(1) + " / 5"
                                font.pixelSize: 42
                                font.bold: true
                                Layout.alignment: Qt.AlignHCenter
                                color: {
                                    var score = mainController ? (mainController.currentEvaluation.overallScore || 0) : 0
                                    if (score >= 4) return "#34d399"
                                    if (score >= 3) return "#fbbf24"
                                    return "#f87171"
                                }
                            }
                        }

                        ColumnLayout {
                            spacing: 4
                            Label {
                                text: mainController ? (mainController.currentEvaluation.scoreLabel || "") : ""
                                font.pixelSize: 18; font.bold: true; color: "#f9fafb"
                            }
                            Label {
                                text: mainController ? (mainController.currentEvaluation.company || "") : ""
                                font.pixelSize: 13; color: "#d1d5db"
                            }
                            Label {
                                text: "Model: " + (mainController ? (mainController.currentEvaluation.modelUsed || "") : "")
                                font.pixelSize: 10; color: "#6b7280"
                            }
                        }
                    }
                }

                // Empty state
                Label {
                    text: mainController && mainController.articles.length === 0
                        ? "📰 Add some articles first (use the Ingest page), then come back to evaluate."
                        : "Select an article above and click Evaluate to begin the step-by-step analysis."
                    color: "#6b7280"
                    font.italic: true
                    visible: (!mainController || mainController.evalSteps.length === 0) && (!mainController || !mainController.isEvaluating)
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: 40
                }
            }
        }
    }
}

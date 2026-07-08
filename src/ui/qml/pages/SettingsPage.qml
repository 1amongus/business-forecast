import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Page {
    Component.onCompleted: { if (settingsController) settingsController.fetchModels() }

    ScrollView {
        anchors.fill: parent
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 20
            anchors.margins: 24

            Item { Layout.preferredHeight: 24 }

            Label { text: "⚙️ Settings"; font.pixelSize: 22; font.bold: true; color: "#f9fafb"; Layout.leftMargin: 24 }

            // SLM Model
            GroupBox {
                title: "🤖 AI Model (Ollama)"
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24

                ColumnLayout {
                    anchors.fill: parent
                    spacing: 12

                    RowLayout {
                        spacing: 12
                        Label { text: "Ollama URL:"; color: "#9ca3af" }
                        TextField {
                            id: urlField
                            text: settingsController ? settingsController.baseUrl : "http://localhost:11434"
                            Layout.fillWidth: true
                        }
                        Button {
                            text: "Save & Refresh"
                            onClicked: {
                                if (settingsController) {
                                    settingsController.setBaseUrl(urlField.text)
                                    settingsController.fetchModels()
                                }
                            }
                        }
                    }

                    RowLayout {
                        spacing: 12
                        Label { text: "Model:"; color: "#9ca3af" }
                        ComboBox {
                            id: modelCombo
                            Layout.fillWidth: true
                            model: {
                                if (!settingsController || !settingsController.availableModels) return []
                                var names = []
                                var m = settingsController.availableModels
                                for (var i = 0; i < m.length; i++) names.push(m[i].name + " (" + m[i].size + ")")
                                return names
                            }
                            onActivated: function(idx) {
                                if (settingsController && settingsController.availableModels && idx < settingsController.availableModels.length)
                                    settingsController.setModel(settingsController.availableModels[idx].name)
                            }
                        }
                    }

                    Label { text: "Active: " + (settingsController ? settingsController.model : ""); color: "#f59e0b"; font.pixelSize: 11 }
                }
            }

            // Output tuning
            GroupBox {
                title: "🎛️ Output Settings"
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24

                GridLayout {
                    anchors.fill: parent
                    columns: 3
                    rowSpacing: 12
                    columnSpacing: 16

                    Label { text: "Temperature:"; color: "#9ca3af" }
                    Slider {
                        id: tempSlider
                        from: 0.0; to: 2.0; stepSize: 0.1
                        value: settingsController ? settingsController.temperature : 0.3
                        Layout.fillWidth: true
                        onMoved: { if (settingsController) settingsController.setTemperature(value) }
                    }
                    Label { text: tempSlider.value.toFixed(1); color: "#f59e0b"; Layout.preferredWidth: 40 }

                    Label { text: "Max Tokens:"; color: "#9ca3af" }
                    Slider {
                        id: tokenSlider
                        from: 64; to: 4096; stepSize: 64
                        value: settingsController ? settingsController.maxTokens : 512
                        Layout.fillWidth: true
                        onMoved: { if (settingsController) settingsController.setMaxTokens(Math.round(value)) }
                    }
                    Label { text: Math.round(tokenSlider.value).toString(); color: "#f59e0b"; Layout.preferredWidth: 40 }
                }
            }

            // About
            GroupBox {
                title: "About"
                Layout.fillWidth: true
                Layout.leftMargin: 24
                Layout.rightMargin: 24

                Label {
                    text: "Business Forecast v1.0\n\nEvaluates company success potential by analyzing WSJ articles with local AI.\nAll data stored as .md files — no servers, no databases."
                    color: "#9ca3af"
                    wrapMode: Text.WordWrap
                }
            }

            Item { Layout.preferredHeight: 40 }
        }
    }
}

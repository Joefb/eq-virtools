import re
import pyttsx3
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QCheckBox
from PyQt6.QtCore import QSettings, Qt

class VoiceNotificationsApp(QWidget):
    def __init__(self, log_dir):
        super().__init__()
        self.setWindowTitle("Voice Notifications")
        self.log_dir = log_dir
        self.settings = QSettings("EverQuestTools", "VoiceNotifications")
        self.tts = pyttsx3.init()
        self.tts.setProperty('rate', 150)
        self.enabled = self.settings.value("enabled", False, type=bool)
        self.triggers = self.settings.value("triggers", {"Your root has broken": "Root has broken!", " resists your spell": "Spell resisted!"}, type=dict)
        self.log_file = None
        self.log_path = None
        self.log_position = 0
        self.setup_ui()

    def setup_ui(self):
        self.resize(400, 300)
        layout = QVBoxLayout()
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)

        # Toggle switch
        self.toggle = QCheckBox("Enable Voice Notifications")
        self.toggle.setChecked(self.enabled)
        self.toggle.stateChanged.connect(self.toggle_notifications)
        layout.addWidget(self.toggle)

        # Trigger table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Log Pattern", "Spoken Message"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.load_triggers()
        layout.addWidget(self.table)

        # Add trigger inputs
        input_layout = QHBoxLayout()
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter log pattern (e.g., Your root has broken)")
        input_layout.addWidget(self.pattern_input)
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter spoken message (e.g., Root has broken!)")
        input_layout.addWidget(self.message_input)
        layout.addLayout(input_layout)

        # Add and delete buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton("Add Trigger")
        add_button.clicked.connect(self.add_trigger)
        button_layout.addWidget(add_button)
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_trigger)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_triggers(self):
        self.table.setRowCount(0)
        for pattern, message in self.triggers.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(pattern))
            self.table.setItem(row, 1, QTableWidgetItem(message))

    def add_trigger(self):
        pattern = self.pattern_input.text().strip()
        message = self.message_input.text().strip()
        if pattern and message:
            self.triggers[pattern] = message
            self.settings.setValue("triggers", self.triggers)
            self.load_triggers()
            self.pattern_input.clear()
            self.message_input.clear()

    def delete_trigger(self):
        selected = self.table.selectedItems()
        if selected:
            pattern = selected[0].text()
            if pattern in self.triggers:
                del self.triggers[pattern]
                self.settings.setValue("triggers", self.triggers)
                self.load_triggers()

    def toggle_notifications(self, state):
        self.enabled = state == Qt.CheckState.Checked.value
        self.settings.setValue("enabled", self.enabled)

    def process_log_line(self, line):
        if not self.enabled:
            return
        for pattern, message in self.triggers.items():
            if pattern in line:
                print(f"Voice alert: {message}")
                self.tts.say(message)
                self.tts.runAndWait()
                break

    def update_log_info(self, log_file, log_path, log_position):
        if self.log_file and self.log_file != log_file:
            self.log_file.close()
        self.log_file = log_file
        self.log_path = log_path
        self.log_position = log_position

    def closeEvent(self, event):
        self.hide()
        event.accept()

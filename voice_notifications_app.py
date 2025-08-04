import re
import pyttsx3
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QCheckBox, QApplication
from PyQt6.QtCore import QSettings, Qt

class VoiceNotificationsApp(QWidget):
    def __init__(self, log_dir):
        super().__init__()
        self.setWindowTitle("Voice Notifications")
        self.log_dir = log_dir
        self.settings = QSettings("EverQuestTools", "VoiceNotifications")
        self.tts = pyttsx3.init()
        self.tts.setProperty('rate', 150)
        self.enabled = self.settings.value("voice_enabled", False, type=bool)
        self.triggers = self.settings.value("voice_triggers", {"Your root has broken": "Root has broken!", " resists your spell": "Spell resisted!"}, type=dict)
        self.log_file = None
        self.log_path = None
        self.log_position = 0
        self.setup_ui()
        self.update_main_app_settings()

    def setup_ui(self):
        self.resize(600, 500)
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
        self.table.setColumnWidth(0, 280)  # Log Pattern
        self.table.setColumnWidth(1, 280)  # Spoken Message
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemChanged.connect(self.update_trigger)
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
        self.table.itemChanged.disconnect(self.update_trigger)
        self.table.setRowCount(0)
        for pattern, message in self.triggers.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            pattern_item = QTableWidgetItem(pattern)
            pattern_item.setFlags(pattern_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, pattern_item)
            message_item = QTableWidgetItem(message)
            message_item.setFlags(message_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, message_item)
        self.table.itemChanged.connect(self.update_trigger)

    def add_trigger(self):
        pattern = self.pattern_input.text().strip()
        message = self.message_input.text().strip()
        if pattern and message:
            self.triggers[pattern] = message
            self.settings.setValue("voice_triggers", self.triggers)
            self.load_triggers()
            self.pattern_input.clear()
            self.message_input.clear()
            self.update_main_app_settings()

    def delete_trigger(self):
        selected = self.table.selectedItems()
        if selected:
            pattern = selected[0].text()
            if pattern in self.triggers:
                del self.triggers[pattern]
                self.settings.setValue("voice_triggers", self.triggers)
                self.load_triggers()
                self.update_main_app_settings()

    def update_trigger(self, item):
        row = item.row()
        pattern_item = self.table.item(row, 0)
        message_item = self.table.item(row, 1)
        if pattern_item and message_item:
            new_pattern = pattern_item.text().strip()
            new_message = message_item.text().strip()
            if new_pattern and new_message:
                # Find old pattern to update
                old_pattern = None
                for p, m in list(self.triggers.items()):
                    if m == self.table.item(row, 1).text() and p != new_pattern:
                        old_pattern = p
                        break
                if old_pattern and old_pattern in self.triggers:
                    del self.triggers[old_pattern]
                self.triggers[new_pattern] = new_message
                self.settings.setValue("voice_triggers", self.triggers)
                self.update_main_app_settings()

    def toggle_notifications(self, state):
        self.enabled = state == Qt.CheckState.Checked.value
        self.settings.setValue("voice_enabled", self.enabled)
        self.update_main_app_settings()

    def update_main_app_settings(self):
        from main import MainApp
        main_app = QApplication.instance().property("MainApp")
        if main_app:
            main_app.update_voice_settings(self.enabled, self.triggers)

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

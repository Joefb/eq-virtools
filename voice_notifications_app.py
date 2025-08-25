import re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QCheckBox, QApplication, QListWidget
from PyQt6.QtCore import QSettings, Qt, QThread, pyqtSignal
from gtts import gTTS
import pygame
import os
import time

class TTSThread(QThread):
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.temp_file = "temp.mp3"

    def run(self):
        try:
            tts = gTTS(text=self.text, lang='en', tld='com')
            tts.save(self.temp_file)
            pygame.mixer.init()
            pygame.mixer.music.load(self.temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
            os.remove(self.temp_file)
        except Exception as e:
            print(f"TTS error: {e}")

class VoiceNotificationsApp(QWidget):
    def __init__(self, log_dir):
        super().__init__()
        self.setWindowTitle("Voice Notifications")
        self.log_dir = log_dir
        self.settings = QSettings("./config/voice-notifications.ini", QSettings.Format.IniFormat)
        self.tts_thread = None
        self.enabled = self.settings.value("voice_enabled", False, type=bool)
        self.master_triggers = self.settings.value("master_triggers", {"Your root has broken": "Root has broken!", " resists your spell": "Spell resisted!"}, type=dict)
        self.triggers = {}  # Will be toon-specific later
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

        # Toon management screen
        self.toon_list = QListWidget()
        self.toon_list.addItem("No toons configured")  # Placeholder
        layout.addWidget(self.toon_list)

        button_layout = QHBoxLayout()
        add_toon_button = QPushButton("Add Toon")
        add_toon_button.clicked.connect(self.add_toon_placeholder)
        button_layout.addWidget(add_toon_button)
        triggers_button = QPushButton("Triggers")
        triggers_button.clicked.connect(self.show_master_triggers)
        button_layout.addWidget(triggers_button)
        layout.addLayout(button_layout)

        # Trigger table (hidden initially)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Log Pattern", "Spoken Message"])
        self.table.setColumnWidth(0, 280)
        self.table.setColumnWidth(1, 280)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemChanged.connect(self.update_trigger)
        self.table.hide()
        layout.addWidget(self.table)

        # Add trigger inputs (hidden initially)
        self.input_layout = QHBoxLayout()
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter log pattern (e.g., Your root has broken)")
        self.input_layout.addWidget(self.pattern_input)
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter spoken message (e.g., Root has broken!)")
        self.input_layout.addWidget(self.message_input)
        self.input_layout_widget = QWidget()
        self.input_layout_widget.setLayout(self.input_layout)
        self.input_layout_widget.hide()
        layout.addWidget(self.input_layout_widget)

        # Add and delete buttons (hidden initially)
        self.button_layout = QHBoxLayout()
        add_button = QPushButton("Add Trigger")
        add_button.clicked.connect(self.add_trigger)
        self.button_layout.addWidget(add_button)
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_trigger)
        self.button_layout.addWidget(delete_button)
        self.button_layout_widget = QWidget()
        self.button_layout_widget.setLayout(self.button_layout)
        self.button_layout_widget.hide()
        layout.addWidget(self.button_layout_widget)

        self.setLayout(layout)

    def add_toon_placeholder(self):
        print("Add Toon clicked (placeholder)")

    def show_master_triggers(self):
        self.toon_list.hide()
        self.findChild(QHBoxLayout).itemAt(0).widget().hide()  # Hide buttons
        self.table.show()
        self.input_layout_widget.show()
        self.button_layout_widget.show()
        self.load_triggers()

    def load_triggers(self):
        self.table.itemChanged.disconnect(self.update_trigger)
        self.table.setRowCount(0)
        for pattern, message in self.master_triggers.items():
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
            self.master_triggers[pattern] = message
            self.settings.beginGroup("master_triggers")
            self.settings.setValue(pattern, message)
            self.settings.endGroup()
            self.settings.sync()
            self.load_triggers()
            self.pattern_input.clear()
            self.message_input.clear()
            self.update_main_app_settings()

    def delete_trigger(self):
        selected = self.table.selectedItems()
        if selected:
            pattern = selected[0].text()
            if pattern in self.master_triggers:
                del self.master_triggers[pattern]
                self.settings.beginGroup("master_triggers")
                self.settings.remove(pattern)
                self.settings.endGroup()
                self.settings.sync()
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
                old_pattern = None
                for p, m in list(self.master_triggers.items()):
                    if m == self.table.item(row, 1).text() and p != new_pattern:
                        old_pattern = p
                        break
                if old_pattern and old_pattern in self.master_triggers:
                    del self.master_triggers[old_pattern]
                    self.settings.beginGroup("master_triggers")
                    self.settings.remove(old_pattern)
                    self.settings.endGroup()
                self.master_triggers[new_pattern] = new_message
                self.settings.beginGroup("master_triggers")
                self.settings.setValue(new_pattern, new_message)
                self.settings.endGroup()
                self.settings.sync()
                self.update_main_app_settings()

    def toggle_notifications(self, state):
        self.enabled = state == Qt.CheckState.Checked.value
        self.settings.setValue("voice_enabled", self.enabled)
        self.settings.sync()
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
                if self.tts_thread and self.tts_thread.isRunning():
                    self.tts_thread.wait()
                self.tts_thread = TTSThread(message)
                self.tts_thread.start()
                break

    def update_log_info(self, log_file, log_path, log_position):
        if self.log_file and self.log_file != log_file:
            self.log_file.close()
        self.log_file = log_file
        self.log_path = log_path
        self.log_position = log_position

    def closeEvent(self, event):
        if self.tts_thread and self.tts_thread.isRunning():
            self.tts_thread.wait()
        self.hide()
        event.accept()

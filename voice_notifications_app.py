from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QCheckBox, QLabel
from PyQt6.QtCore import QSettings, Qt, QThread
from gtts import gTTS
import pygame
import os
import re
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
        config_dir = os.path.abspath("./config")
        os.makedirs(config_dir, exist_ok=True)
        self.settings = QSettings(os.path.join(config_dir, "voice-notifications.ini"), QSettings.Format.IniFormat)
        self.tts_thread = None
        self.enabled = self.settings.value("voice_enabled", False, type=bool)
        self.master_triggers = {}
        self.settings.beginGroup("master_triggers")
        for key in self.settings.allKeys():
            self.master_triggers[key] = self.settings.value(key)
        self.settings.endGroup()
        if not self.master_triggers:
            self.master_triggers = {"Your root has broken": "Root has broken!", " resists your spell": "Spell resisted!"}
        self.log_file = None
        self.log_path = None
        self.log_position = 0
        self.setup_ui()

    def setup_ui(self):
        self.resize(600, 500)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(4)
        self.layout.setContentsMargins(4, 4, 4, 4)

        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable Voice Notifications")
        self.enable_checkbox.setChecked(self.enabled)
        self.enable_checkbox.stateChanged.connect(self.toggle_notifications)
        self.layout.addWidget(self.enable_checkbox)

        # Toon management screen
        self.toon_list = QListWidget()
        self.toon_list.addItem("No toons configured")
        self.layout.addWidget(self.toon_list)

        self.button_layout = QHBoxLayout()
        add_toon_button = QPushButton("Add Toon")
        add_toon_button.clicked.connect(self.add_toon_placeholder)
        self.button_layout.addWidget(add_toon_button)
        triggers_button = QPushButton("Triggers")
        triggers_button.clicked.connect(self.show_master_triggers)
        self.button_layout.addWidget(triggers_button)
        self.button_layout_widget = QWidget()
        self.button_layout_widget.setLayout(self.button_layout)
        self.layout.addWidget(self.button_layout_widget)

        # Trigger screen (hidden initially)
        self.trigger_layout = QVBoxLayout()
        self.trigger_header_layout = QHBoxLayout()
        self.back_button = QPushButton("<")
        self.back_button.setFixedWidth(30)
        self.back_button.clicked.connect(self.show_toon_list)
        self.trigger_header_layout.addWidget(self.back_button)
        self.trigger_title = QLabel("Master Trigger List")
        self.trigger_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.trigger_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.trigger_header_layout.addWidget(self.trigger_title)
        self.trigger_header_layout.addStretch()
        self.trigger_layout.addLayout(self.trigger_header_layout)

        # Search bar for trigger screen
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search log patterns (e.g., root)")
        self.search_input.textChanged.connect(self.filter_triggers)
        self.trigger_layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Log Pattern", "Spoken Message"])
        self.table.setColumnWidth(0, 280)
        self.table.setColumnWidth(1, 280)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemChanged.connect(self.update_trigger)
        self.trigger_layout.addWidget(self.table)

        self.input_layout = QHBoxLayout()
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Enter log pattern (e.g., Your root has broken)")
        self.input_layout.addWidget(self.pattern_input)
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Enter spoken message (e.g., Root has broken!)")
        self.input_layout.addWidget(self.message_input)
        self.input_layout_widget = QWidget()
        self.input_layout_widget.setLayout(self.input_layout)
        self.trigger_layout.addWidget(self.input_layout_widget)

        self.trigger_button_layout = QHBoxLayout()
        add_button = QPushButton("Add Trigger")
        add_button.clicked.connect(self.add_trigger)
        self.trigger_button_layout.addWidget(add_button)
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self.delete_trigger)
        self.trigger_button_layout.addWidget(delete_button)
        self.trigger_button_layout_widget = QWidget()
        self.trigger_button_layout_widget.setLayout(self.trigger_button_layout)
        self.trigger_layout.addWidget(self.trigger_button_layout_widget)

        self.trigger_layout_widget = QWidget()
        self.trigger_layout_widget.setLayout(self.trigger_layout)
        self.trigger_layout_widget.hide()
        self.layout.addWidget(self.trigger_layout_widget)

        self.setLayout(self.layout)
        self.load_triggers()

    def add_toon_placeholder(self):
        pass

    def show_master_triggers(self):
        self.toon_list.hide()
        self.button_layout_widget.hide()
        self.trigger_layout_widget.show()
        self.load_triggers()

    def show_toon_list(self):
        self.trigger_layout_widget.hide()
        self.toon_list.show()
        self.button_layout_widget.show()

    def load_triggers(self):
        self.table.itemChanged.disconnect(self.update_trigger)
        self.table.setRowCount(0)
        search_text = self.search_input.text().strip().lower()
        for pattern, message in self.master_triggers.items():
            if search_text in pattern.lower() or not search_text:
                row = self.table.rowCount()
                self.table.insertRow(row)
                pattern_item = QTableWidgetItem(pattern)
                pattern_item.setFlags(pattern_item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 0, pattern_item)
                message_item = QTableWidgetItem(message)
                message_item.setFlags(message_item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 1, message_item)
        self.table.itemChanged.connect(self.update_trigger)

    def filter_triggers(self):
        self.load_triggers()

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

    def update_trigger(self, item):
        row = item.row()
        pattern_item = self.table.item(row, 0)
        message_item = self.table.item(row, 1)
        if pattern_item and message_item:
            new_pattern = pattern_item.text().strip()
            new_message = message_item.text().strip()
            if new_pattern and new_message:
                old_pattern = next((p for p, m in self.master_triggers.items() if p != new_pattern and m == self.table.item(row, 1).text()), None)
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
                self.load_triggers()

    def toggle_notifications(self, state):
        self.enabled = state == Qt.CheckState.Checked.value
        self.settings.setValue("voice_enabled", self.enabled)
        self.settings.sync()

    def process_log_line(self, line):
        if not self.enabled:
            return
        for pattern, message in self.master_triggers.items():
            if pattern in line:
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

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QCheckBox, QLabel, QListWidget
from PyQt6.QtCore import QSettings, Qt, QThread
from gtts import gTTS
import pygame
import os
import re
import time
import urllib.parse

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
    def __init__(self, log_dir, toon_name="Unknown"):
        super().__init__()
        self.setWindowTitle("Voice Notifications")
        self.log_dir = log_dir if os.path.exists(log_dir) else "/app/logs"
        self.current_toon = toon_name
        config_dir = os.path.abspath("./config")
        os.makedirs(config_dir, exist_ok=True)
        self.settings = QSettings(os.path.join(config_dir, "voice-notifications.ini"), QSettings.Format.IniFormat)
        self.settings.remove("General")  # Clear stale [General] section
        self.tts_thread = None
        self.enabled = self.settings.value("voice_enabled", False, type=bool)
        self.master_triggers = {}
        self.settings.beginGroup("master_triggers")
        for key in self.settings.allKeys():
            decoded_key = self.decode_key(key)
            self.master_triggers[decoded_key] = self.settings.value(key)
        self.settings.endGroup()
        if not self.master_triggers:
            self.master_triggers = {
                "Your root has broken": "Root has broken!",
                " resists your spell": "Spell resisted!"
            }
            self.settings.beginGroup("master_triggers")
            for pattern, message in self.master_triggers.items():
                self.settings.setValue(self.encode_key(pattern), message)
            self.settings.endGroup()
            self.settings.sync()
        self.toons = []
        self.settings.beginGroup("toons")
        for key in self.settings.allKeys():
            self.toons.append(self.settings.value(key))
        self.settings.endGroup()
        self.toon_triggers = {}
        for toon in self.toons:
            self.toon_triggers[toon] = []
            self.settings.beginGroup(f"toon_triggers/{toon}")
            for key in self.settings.allKeys():
                self.toon_triggers[toon].append(self.decode_key(key))
            self.settings.endGroup()
        self.log_file = None
        self.log_path = None
        self.log_position = 0
        self.setup_ui()
        self.update_active_toon_label()

    def encode_key(self, key):
        """Replace spaces with underscores for QSettings keys."""
        return key.replace(" ", "_")

    def decode_key(self, key):
        """Replace underscores with spaces for trigger patterns."""
        return key.replace("_", " ")

    def update_active_toon_label(self):
        """Update the active toon label text."""
        self.active_toon_label.setText(f"Active Toon: {self.current_toon}")

    def setup_ui(self):
        self.resize(600, 600)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(4)
        self.layout.setContentsMargins(4, 4, 4, 4)

        ## HEADER ######
        # Voice Management Title 
        self.vn_management_label = QLabel("Voice Notification Management")
        self.vn_management_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vn_management_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.layout.addWidget(self.vn_management_label)

        # Active toon label
        self.active_toon_label = QLabel(f"Active Toon: {self.current_toon}")
        self.active_toon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_toon_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.active_toon_label)

        # Enable checkbox
        self.enable_checkbox = QCheckBox("Enable Voice Notifications")
        self.enable_checkbox.setChecked(self.enabled)
        self.enable_checkbox.stateChanged.connect(self.toggle_notifications)
        self.layout.addWidget(self.enable_checkbox)

        ## MAIN SCREEN ################
        # Toon profile title
        self.toon_list_title = QLabel("Toon Voice Notification Profiles")
        self.toon_list_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.layout.addWidget(self.toon_list_title)
        
        # Toon profile list
        self.toon_list = QListWidget()
        self.toon_list.itemDoubleClicked.connect(self.show_toon_triggers_ui)
        self.update_toon_list()
        self.layout.addWidget(self.toon_list)

        # Add toon input box
        self.toon_input = QLineEdit()
        self.toon_input.setPlaceholderText("Enter toon name to add (e.g., Bob)")
        self.layout.addWidget(self.toon_input)

        # Add/Delete buttons 
        self.add_toon_button_layout = QHBoxLayout()
        add_toon_submit_button = QPushButton("Add New Toon")
        add_toon_submit_button.clicked.connect(self.add_toon)
        self.add_toon_button_layout.addWidget(add_toon_submit_button)
        delete_toon_submit_button = QPushButton("Delete Toon")
        # delete_toon_submit_button.clicked.connect(self.delete_toon)
        self.add_toon_button_layout.addWidget(delete_toon_submit_button)
        self.add_toon_button_layout_widget = QWidget()
        self.add_toon_button_layout_widget.setLayout(self.add_toon_button_layout)
        self.layout.addWidget(self.add_toon_button_layout_widget)

        # Master trigger button
        triggers_button = QPushButton("Master Trigger List")
        triggers_button.clicked.connect(self.show_master_triggers)
        self.add_toon_button_layout.addWidget(triggers_button)
        self.button_layout_widget = QWidget()
        self.button_layout_widget.setLayout(self.add_toon_button_layout)
        self.layout.addWidget(self.button_layout_widget)

        ## MASTER TRIGGERS UI #################################
        # Master Trigger screen (hidden initially)
        self.trigger_layout = QVBoxLayout()
        self.trigger_header_layout = QHBoxLayout()
        self.back_button = QPushButton("<")
        self.back_button.setFixedWidth(30)
        self.back_button.clicked.connect(self.show_toon_list)
        self.trigger_header_layout.addWidget(self.back_button)
        self.trigger_header_layout.addStretch()
        self.trigger_layout.addLayout(self.trigger_header_layout)

        # Title
        self.trigger_title_layout = QHBoxLayout()
        self.trigger_title = QLabel("Master Trigger List")
        self.trigger_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.trigger_title_layout.addWidget(self.trigger_title)
        self.trigger_layout.addLayout(self.trigger_title_layout)

        # Search bar for trigger screen
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search log patterns (e.g., root)")
        self.search_input.textChanged.connect(self.filter_triggers)
        self.trigger_layout.addWidget(self.search_input)

        # Toon Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Log Pattern", "Spoken Message"])
        self.table.setColumnWidth(0, 280)
        self.table.setColumnWidth(1, 280)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemChanged.connect(self.update_trigger)
        self.trigger_layout.addWidget(self.table)

        # Toon input boxes
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

        # Toon buttons
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

        # TOON TRIGGERS UI ###################################
        # Add Toon Triggers screen (hidden initially)
        self.toon_triggers_layout = QVBoxLayout()
        self.toon_triggers_header_layout = QHBoxLayout()
        self.toon_triggers_back_button = QPushButton("<")
        self.toon_triggers_back_button.setFixedWidth(30)
        self.toon_triggers_back_button.clicked.connect(self.show_toon_list)
        self.toon_triggers_header_layout.addWidget(self.toon_triggers_back_button)
        self.toon_triggers_header_layout.addStretch()
        self.toon_triggers_layout.addLayout(self.toon_triggers_header_layout)

        # Title
        self.toon_triggers_title_layout = QHBoxLayout()
        self.toon_triggers_title = QLabel("Triggers for Toon")
        self.toon_triggers_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.toon_triggers_title_layout.addWidget(self.toon_triggers_title)
        self.toon_triggers_layout.addLayout(self.toon_triggers_title_layout)

        # Master triggers search bar
        self.master_triggers_search_input = QLineEdit()
        self.master_triggers_search_input.setPlaceholderText("Search master triggers (e.g., root)")
        self.master_triggers_search_input.textChanged.connect(self.filter_master_triggers)
        self.toon_triggers_layout.addWidget(self.master_triggers_search_input)

        self.master_triggers_table = QTableWidget()
        self.master_triggers_table.setColumnCount(2)
        self.master_triggers_table.setHorizontalHeaderLabels(["Log Pattern", "Spoken Message"])
        self.master_triggers_table.setColumnWidth(0, 280)
        self.master_triggers_table.setColumnWidth(1, 280)
        self.master_triggers_table.horizontalHeader().setStretchLastSection(True)
        self.master_triggers_table.cellDoubleClicked.connect(self.add_toon_trigger)
        self.toon_triggers_layout.addWidget(self.master_triggers_table)

        # Toon triggers search
        self.toon_triggers_search_input = QLineEdit()
        self.toon_triggers_search_input.setPlaceholderText("Search toon triggers (e.g., root)")
        self.toon_triggers_search_input.textChanged.connect(self.filter_toon_triggers)
        self.toon_triggers_layout.addWidget(self.toon_triggers_search_input)

        self.toon_triggers_table = QTableWidget()
        self.toon_triggers_table.setColumnCount(2)
        self.toon_triggers_table.setHorizontalHeaderLabels(["Log Pattern", "Spoken Message"])
        self.toon_triggers_table.setColumnWidth(0, 280)
        self.toon_triggers_table.setColumnWidth(1, 280)
        self.toon_triggers_table.horizontalHeader().setStretchLastSection(True)
        self.toon_triggers_table.cellDoubleClicked.connect(self.remove_toon_trigger)
        self.toon_triggers_layout.addWidget(self.toon_triggers_table)

        self.toon_triggers_layout_widget = QWidget()
        self.toon_triggers_layout_widget.setLayout(self.toon_triggers_layout)
        self.toon_triggers_layout_widget.hide()
        self.layout.addWidget(self.toon_triggers_layout_widget)

        self.current_toon_for_triggers = None
        self.setLayout(self.layout)
        self.load_triggers()

    def update_toon_list(self):
        self.toon_list.clear()
        if not self.toons:
            self.toon_list.addItem("No toons configured")
        else:
            for toon in self.toons:
                self.toon_list.addItem(toon)

    def show_master_triggers(self):
        self.toon_list.hide()
        self.button_layout_widget.hide()
        self.toon_input.hide() 
        self.toon_triggers_layout_widget.hide()
        self.toon_list_title.hide() 
        self.enable_checkbox.hide() 
        self.trigger_layout_widget.show()
        self.load_triggers()

    def show_toon_list(self):
        self.trigger_layout_widget.hide()
        self.toon_triggers_layout_widget.hide()
        self.toon_input.show() 
        self.toon_list.show()
        self.button_layout_widget.show()
        self.toon_list_title.show()
        self.enable_checkbox.show() 

    def show_toon_triggers_ui(self, item):
        toon_name = item.text()
        if toon_name == "No toons configured":
            return
        self.current_toon_for_triggers = toon_name
        self.toon_triggers_title.setText(f"Triggers for {toon_name}")
        self.toon_list.hide()
        self.toon_list_title.hide() 
        self.enable_checkbox.hide() 
        self.toon_input.hide()
        self.button_layout_widget.hide()
        self.trigger_layout_widget.hide()
        self.toon_triggers_layout_widget.show()
        self.load_master_triggers()
        self.load_toon_triggers()

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

    def load_master_triggers(self):
        self.master_triggers_table.setRowCount(0)
        search_text = self.master_triggers_search_input.text().strip().lower()
        for pattern, message in self.master_triggers.items():
            if search_text in pattern.lower() or not search_text:
                row = self.master_triggers_table.rowCount()
                self.master_triggers_table.insertRow(row)
                pattern_item = QTableWidgetItem(pattern)
                pattern_item.setFlags(pattern_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.master_triggers_table.setItem(row, 0, pattern_item)
                message_item = QTableWidgetItem(message)
                message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.master_triggers_table.setItem(row, 1, message_item)

    def filter_master_triggers(self):
        self.load_master_triggers()

    def load_toon_triggers(self):
        self.toon_triggers_table.setRowCount(0)
        search_text = self.toon_triggers_search_input.text().strip().lower()
        if self.current_toon_for_triggers in self.toon_triggers:
            for pattern in self.toon_triggers[self.current_toon_for_triggers]:
                if search_text in pattern.lower() or not search_text:
                    row = self.toon_triggers_table.rowCount()
                    self.toon_triggers_table.insertRow(row)
                    pattern_item = QTableWidgetItem(pattern)
                    pattern_item.setFlags(pattern_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.toon_triggers_table.setItem(row, 0, pattern_item)
                    message_item = QTableWidgetItem(self.master_triggers.get(pattern, ""))
                    message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.toon_triggers_table.setItem(row, 1, message_item)

    def filter_toon_triggers(self):
        self.load_toon_triggers()

    def add_toon(self):
        toon_name = self.toon_input.text().strip()
        if toon_name and toon_name not in self.toons:
            self.toons.append(toon_name)
            self.toon_triggers[toon_name] = []
            self.settings.beginGroup("toons")
            self.settings.setValue(str(len(self.toons)), toon_name)
            self.settings.endGroup()
            self.settings.sync()
            self.update_toon_list()
            self.toon_input.clear()
            self.show_toon_list()

    def add_trigger(self):
        pattern = self.pattern_input.text().strip()
        message = self.message_input.text().strip()
        if pattern and message:
            self.master_triggers[pattern] = message
            self.settings.beginGroup("master_triggers")
            self.settings.setValue(self.encode_key(pattern), message)
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
                self.settings.remove(self.encode_key(pattern))
                self.settings.endGroup()
                for toon in self.toon_triggers:
                    if pattern in self.toon_triggers[toon]:
                        self.toon_triggers[toon].remove(pattern)
                        self.settings.beginGroup(f"toon_triggers/{toon}")
                        self.settings.remove(self.encode_key(pattern))
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
                    self.settings.remove(self.encode_key(old_pattern))
                    self.settings.endGroup()
                    for toon in self.toon_triggers:
                        if old_pattern in self.toon_triggers[toon]:
                            self.toon_triggers[toon].remove(old_pattern)
                            self.toon_triggers[toon].append(new_pattern)
                            self.settings.beginGroup(f"toon_triggers/{toon}")
                            self.settings.remove(self.encode_key(old_pattern))
                            self.settings.setValue(self.encode_key(new_pattern), "true")
                            self.settings.endGroup()
                self.master_triggers[new_pattern] = new_message
                self.settings.beginGroup("master_triggers")
                self.settings.setValue(self.encode_key(new_pattern), new_message)
                self.settings.endGroup()
                self.settings.sync()
                self.load_triggers()

    def add_toon_trigger(self, row, column):
        if row >= 0:
            pattern = self.master_triggers_table.item(row, 0).text()
            if self.current_toon_for_triggers and pattern not in self.toon_triggers.get(self.current_toon_for_triggers, []):
                self.toon_triggers.setdefault(self.current_toon_for_triggers, []).append(pattern)
                self.settings.beginGroup(f"toon_triggers/{self.current_toon_for_triggers}")
                self.settings.setValue(self.encode_key(pattern), "true")
                self.settings.endGroup()
                self.settings.sync()
                self.load_toon_triggers()

    def remove_toon_trigger(self, row, column):
        if row >= 0:
            pattern = self.toon_triggers_table.item(row, 0).text()
            if self.current_toon_for_triggers and pattern in self.toon_triggers.get(self.current_toon_for_triggers, []):
                self.toon_triggers[self.current_toon_for_triggers].remove(pattern)
                self.settings.beginGroup(f"toon_triggers/{self.current_toon_for_triggers}")
                self.settings.remove(self.encode_key(pattern))
                self.settings.endGroup()
                self.settings.sync()
                self.load_toon_triggers()

    def toggle_notifications(self, state):
        self.enabled = state == Qt.CheckState.Checked.value
        self.settings.setValue("voice_enabled", self.enabled)
        self.settings.sync()

    def process_log_line(self, line):
        if not self.enabled or not self.current_toon or self.current_toon not in self.toon_triggers:
            return
        for pattern in self.toon_triggers.get(self.current_toon, []):
            if pattern in line:
                message = self.master_triggers.get(pattern, "")
                if message:
                    if self.tts_thread and self.tts_thread.isRunning():
                        self.tts_thread.wait()
                    self.tts_thread = TTSThread(message)
                    self.tts_thread.start()
                    break

    def update_log_info(self, log_file, log_path, log_position, toon_name):
        if self.log_file and self.log_file != log_file:
            self.log_file.close()
        self.log_file = log_file
        self.log_path = log_path
        self.log_position = log_position
        self.current_toon = toon_name
        self.update_active_toon_label()

    def closeEvent(self, event):
        if self.tts_thread and self.tts_thread.isRunning():
            self.tts_thread.wait()
        self.hide()
        event.accept()

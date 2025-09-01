from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QCheckBox, QLabel, QListWidget, QMessageBox, QProgressBar
from PyQt6.QtCore import QSettings, Qt, QTimer, QPoint
import os
import re


class OverlayManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(2)
        self.setLayout(self.layout)
        self.old_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def add_bar(self, bar):
        self.layout.addWidget(bar)
        if not self.isVisible():
            self.show()

    def remove_bar(self, bar):
        self.layout.removeWidget(bar)
        bar.deleteLater()
        if self.layout.count() == 0:
            self.hide()


class TimerBar(QProgressBar):
    def __init__(self, message, duration, manager):
        super().__init__()
        self.manager = manager
        self.message = message
        self.duration = duration
        self.remaining = duration
        self.setFixedHeight(20)
        self.setRange(0, 100)
        self.setValue(100)
        self.setTextVisible(True)
        self.setStyleSheet("""
            QProgressBar {
                background-color: rgba(224,224,224,150);
                border: 1px solid rgba(160,160,160,150);
                border-radius: 2px;
                text-align: left;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: rgba(76,175,80,200);
            }
        """)
        self.setFormat(f"{self.message} (%v:%s)")
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

    def update_timer(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.timer.stop()
            self.manager.remove_bar(self)
            return
        percent = (self.remaining / self.duration) * 100
        self.setValue(int(percent))
        mins, secs = divmod(self.remaining, 60)
        self.setFormat(f"{self.message} ({mins}:{secs:02})")

    def paintEvent(self, event):
        super().paintEvent(event)


class OverlaysApp(QWidget):
    def __init__(self, log_dir, toon_name="Unknown"):
        super().__init__()
        self.setWindowTitle("Overlays")
        self.log_dir = log_dir if os.path.exists(log_dir) else "/app/logs"
        self.current_toon = toon_name
        config_dir = os.path.abspath("./config")
        os.makedirs(config_dir, exist_ok=True)
        self.settings = QSettings(os.path.join(
            config_dir, "overlays.ini"), QSettings.Format.IniFormat)
        self.enabled = self.settings.value(
            "overlays_enabled", False, type=bool)
        self.master_triggers = {}
        self.settings.beginGroup("master_overlays")
        for key in self.settings.allKeys():
            decoded_key = self.decode_key(key)
            value = self.settings.value(key)
            if '|' in value:
                message, duration = value.split('|')
                self.master_triggers[decoded_key] = {
                    'message': message, 'duration': int(duration)}
        self.settings.endGroup()
        if not self.master_triggers:
            self.master_triggers = {
                "You activate Stone Stance.": {'message': 'Stone Stance', 'duration': 480}
            }
            self.settings.beginGroup("master_overlays")
            for pattern, data in self.master_triggers.items():
                self.settings.setValue(self.encode_key(pattern), f"{
                                       data['message']}|{data['duration']}")
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
            self.settings.beginGroup(f"toon_overlays/{toon}")
            for key in self.settings.allKeys():
                self.toon_triggers[toon].append(self.decode_key(key))
            self.settings.endGroup()
        self.log_file = None
        self.log_path = None
        self.log_position = 0
        self.overlay_manager = OverlayManager()
        overlay_pos = self.settings.value("overlay_pos", QPoint(100, 100))
        self.overlay_manager.move(overlay_pos)
        self.setup_ui()
        self.update_active_toon_label()

    def encode_key(self, key):
        return key.replace(" ", "_")

    def decode_key(self, key):
        return key.replace("_", " ")

    def update_active_toon_label(self):
        self.active_toon_label.setText(f"Active Toon: {self.current_toon}")

    def setup_ui(self):
        self.resize(700, 600)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(4)
        self.layout.setContentsMargins(4, 4, 4, 4)

        # HEADER
        self.ov_management_label = QLabel("Overlay Management")
        self.ov_management_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ov_management_label.setStyleSheet(
            "font-weight: bold; font-size: 16px;")
        self.layout.addWidget(self.ov_management_label)

        self.active_toon_label = QLabel(f"Active Toon: {self.current_toon}")
        self.active_toon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.active_toon_label.setStyleSheet(
            "font-weight: bold; font-size: 14px;")
        self.layout.addWidget(self.active_toon_label)

        self.enable_checkbox = QCheckBox("Enable Overlays")
        self.enable_checkbox.setChecked(self.enabled)
        self.enable_checkbox.stateChanged.connect(self.toggle_overlays)
        self.layout.addWidget(self.enable_checkbox)

        # MAIN SCREEN
        self.toon_list_title = QLabel("Toon Overlay Profiles")
        self.toon_list_title.setStyleSheet(
            "font-weight: bold; font-size: 16px;")
        self.layout.addWidget(self.toon_list_title)

        self.toon_list = QListWidget()
        self.toon_list.itemDoubleClicked.connect(self.show_toon_triggers_ui)
        self.update_toon_list()
        self.layout.addWidget(self.toon_list)

        self.toon_input = QLineEdit()
        self.toon_input.setPlaceholderText(
            "Enter toon name to add (e.g., Bob)")
        self.layout.addWidget(self.toon_input)

        self.add_toon_button_layout = QHBoxLayout()
        add_toon_submit_button = QPushButton("Add New Toon")
        add_toon_submit_button.clicked.connect(self.add_toon)
        self.add_toon_button_layout.addWidget(add_toon_submit_button)
        delete_toon_submit_button = QPushButton("Delete Toon")
        delete_toon_submit_button.clicked.connect(self.delete_toon)
        self.add_toon_button_layout.addWidget(delete_toon_submit_button)
        triggers_button = QPushButton("Master Overlay List")
        triggers_button.clicked.connect(self.show_master_triggers)
        self.add_toon_button_layout.addWidget(triggers_button)
        self.button_layout_widget = QWidget()
        self.button_layout_widget.setLayout(self.add_toon_button_layout)
        self.layout.addWidget(self.button_layout_widget)

        # MASTER TRIGGERS UI
        self.trigger_layout = QVBoxLayout()
        self.trigger_header_layout = QHBoxLayout()
        self.back_button = QPushButton("<")
        self.back_button.setFixedWidth(30)
        self.back_button.clicked.connect(self.show_toon_list)
        self.trigger_header_layout.addWidget(self.back_button)
        self.trigger_header_layout.addStretch()
        self.trigger_layout.addLayout(self.trigger_header_layout)

        self.trigger_title = QLabel("Master Overlay List")
        self.trigger_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.trigger_layout.addWidget(self.trigger_title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search log patterns (e.g., Stone Stance)")
        self.search_input.textChanged.connect(self.filter_triggers)
        self.trigger_layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["Log Pattern", "Overlay Message", "Duration (secs)"])
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 200)
        self.table.setColumnWidth(2, 100)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemChanged.connect(self.update_trigger)
        self.trigger_layout.addWidget(self.table)

        self.input_layout = QHBoxLayout()
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText(
            "Enter log pattern (e.g., You activate Stone Stance.)")
        self.input_layout.addWidget(self.pattern_input)
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText(
            "Enter overlay message (e.g., Stone Stance)")
        self.input_layout.addWidget(self.message_input)
        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText(
            "Enter duration in seconds (e.g., 480)")
        self.input_layout.addWidget(self.duration_input)
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

        # TOON TRIGGERS UI
        self.toon_triggers_layout = QVBoxLayout()
        self.toon_triggers_header_layout = QHBoxLayout()
        self.toon_triggers_back_button = QPushButton("<")
        self.toon_triggers_back_button.setFixedWidth(30)
        self.toon_triggers_back_button.clicked.connect(self.show_toon_list)
        self.toon_triggers_header_layout.addWidget(
            self.toon_triggers_back_button)
        self.toon_triggers_header_layout.addStretch()
        self.toon_triggers_layout.addLayout(self.toon_triggers_header_layout)

        self.toon_triggers_title = QLabel("Overlays for Toon")
        self.toon_triggers_title.setStyleSheet(
            "font-weight: bold; font-size: 16px;")
        self.toon_triggers_layout.addWidget(self.toon_triggers_title)

        self.master_triggers_search_input = QLineEdit()
        self.master_triggers_search_input.setPlaceholderText(
            "Search master overlays (e.g., Stone Stance)")
        self.master_triggers_search_input.textChanged.connect(
            self.filter_master_triggers)
        self.toon_triggers_layout.addWidget(self.master_triggers_search_input)

        self.master_triggers_table = QTableWidget()
        self.master_triggers_table.setColumnCount(3)
        self.master_triggers_table.setHorizontalHeaderLabels(
            ["Log Pattern", "Overlay Message", "Duration (secs)"])
        self.master_triggers_table.setColumnWidth(0, 200)
        self.master_triggers_table.setColumnWidth(1, 200)
        self.master_triggers_table.setColumnWidth(2, 100)
        self.master_triggers_table.horizontalHeader().setStretchLastSection(True)
        self.master_triggers_table.cellDoubleClicked.connect(
            self.add_toon_trigger)
        self.toon_triggers_layout.addWidget(self.master_triggers_table)

        self.toon_triggers_search_input = QLineEdit()
        self.toon_triggers_search_input.setPlaceholderText(
            "Search toon overlays (e.g., Stone Stance)")
        self.toon_triggers_search_input.textChanged.connect(
            self.filter_toon_triggers)
        self.toon_triggers_layout.addWidget(self.toon_triggers_search_input)

        self.toon_triggers_table = QTableWidget()
        self.toon_triggers_table.setColumnCount(3)
        self.toon_triggers_table.setHorizontalHeaderLabels(
            ["Log Pattern", "Overlay Message", "Duration (secs)"])
        self.toon_triggers_table.setColumnWidth(0, 200)
        self.toon_triggers_table.setColumnWidth(1, 200)
        self.toon_triggers_table.setColumnWidth(2, 100)
        self.toon_triggers_table.horizontalHeader().setStretchLastSection(True)
        self.toon_triggers_table.cellDoubleClicked.connect(
            self.remove_toon_trigger)
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
        self.toon_triggers_title.setText(f"Overlays for {toon_name}")
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
        for pattern, data in self.master_triggers.items():
            if search_text in pattern.lower() or not search_text:
                row = self.table.rowCount()
                self.table.insertRow(row)
                pattern_item = QTableWidgetItem(pattern)
                pattern_item.setFlags(
                    pattern_item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 0, pattern_item)
                message_item = QTableWidgetItem(data['message'])
                message_item.setFlags(
                    message_item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 1, message_item)
                duration_item = QTableWidgetItem(str(data['duration']))
                duration_item.setFlags(
                    duration_item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 2, duration_item)
        self.table.itemChanged.connect(self.update_trigger)

    def filter_triggers(self):
        self.load_triggers()

    def load_master_triggers(self):
        self.master_triggers_table.setRowCount(0)
        search_text = self.master_triggers_search_input.text().strip().lower()
        for pattern, data in self.master_triggers.items():
            if search_text in pattern.lower() or not search_text:
                row = self.master_triggers_table.rowCount()
                self.master_triggers_table.insertRow(row)
                pattern_item = QTableWidgetItem(pattern)
                pattern_item.setFlags(
                    pattern_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.master_triggers_table.setItem(row, 0, pattern_item)
                message_item = QTableWidgetItem(data['message'])
                message_item.setFlags(
                    message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.master_triggers_table.setItem(row, 1, message_item)
                duration_item = QTableWidgetItem(str(data['duration']))
                duration_item.setFlags(
                    duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.master_triggers_table.setItem(row, 2, duration_item)

    def filter_master_triggers(self):
        self.load_master_triggers()

    def load_toon_triggers(self):
        self.toon_triggers_table.setRowCount(0)
        search_text = self.toon_triggers_search_input.text().strip().lower()
        if self.current_toon_for_triggers in self.toon_triggers:
            for pattern in self.toon_triggers[self.current_toon_for_triggers]:
                if search_text in pattern.lower() or not search_text:
                    data = self.master_triggers.get(
                        pattern, {'message': '', 'duration': 0})
                    row = self.toon_triggers_table.rowCount()
                    self.toon_triggers_table.insertRow(row)
                    pattern_item = QTableWidgetItem(pattern)
                    pattern_item.setFlags(
                        pattern_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.toon_triggers_table.setItem(row, 0, pattern_item)
                    message_item = QTableWidgetItem(data['message'])
                    message_item.setFlags(
                        message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.toon_triggers_table.setItem(row, 1, message_item)
                    duration_item = QTableWidgetItem(str(data['duration']))
                    duration_item.setFlags(
                        duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.toon_triggers_table.setItem(row, 2, duration_item)

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

    def delete_toon(self):
        selected_items = self.toon_list.selectedItems()
        if not selected_items:
            return
        toon_name = selected_items[0].text().strip()
        if toon_name == "No toons configured" or not toon_name:
            return
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Confirm Deletion")
        msg_box.setText(
            f"Are you sure you want to delete the toon '{toon_name}'?")
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        if msg_box.exec() != QMessageBox.StandardButton.Yes:
            return
        if toon_name in self.toons:
            self.toons.remove(toon_name)
            if toon_name in self.toon_triggers:
                del self.toon_triggers[toon_name]
            self.settings.beginGroup("toons")
            self.settings.remove("")
            for i, toon in enumerate(self.toons, 1):
                self.settings.setValue(str(i), toon)
            self.settings.endGroup()
            self.settings.beginGroup(f"toon_overlays/{toon_name}")
            self.settings.remove("")
            self.settings.endGroup()
            self.settings.sync()
            self.update_toon_list()
            if self.current_toon == toon_name:
                self.current_toon = "Unknown"
                self.update_active_toon_label()

    def add_trigger(self):
        pattern = self.pattern_input.text().strip()
        message = self.message_input.text().strip()
        duration_str = self.duration_input.text().strip()
        try:
            duration = int(duration_str)
            if pattern and message and duration > 0:
                self.master_triggers[pattern] = {
                    'message': message, 'duration': duration}
                self.settings.beginGroup("master_overlays")
                self.settings.setValue(self.encode_key(
                    pattern), f"{message}|{duration}")
                self.settings.endGroup()
                self.settings.sync()
                self.load_triggers()
                self.pattern_input.clear()
                self.message_input.clear()
                self.duration_input.clear()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input",
                                "Duration must be a positive integer.")

    def delete_trigger(self):
        selected = self.table.selectedItems()
        if selected:
            pattern = selected[0].text()
            if pattern in self.master_triggers:
                del self.master_triggers[pattern]
                self.settings.beginGroup("master_overlays")
                self.settings.remove(self.encode_key(pattern))
                self.settings.endGroup()
                for toon in self.toon_triggers:
                    if pattern in self.toon_triggers[toon]:
                        self.toon_triggers[toon].remove(pattern)
                        self.settings.beginGroup(f"toon_overlays/{toon}")
                        self.settings.remove(self.encode_key(pattern))
                        self.settings.endGroup()
                self.settings.sync()
                self.load_triggers()

    def update_trigger(self, item):
        row = item.row()
        pattern_item = self.table.item(row, 0)
        message_item = self.table.item(row, 1)
        duration_item = self.table.item(row, 2)
        if pattern_item and message_item and duration_item:
            new_pattern = pattern_item.text().strip()
            new_message = message_item.text().strip()
            try:
                new_duration = int(duration_item.text().strip())
                if new_pattern and new_message and new_duration > 0:
                    old_pattern = next((p for p in self.master_triggers if p != new_pattern and self.table.item(
                        row, 1).text() == self.master_triggers[p]['message']), None)
                    if old_pattern and old_pattern in self.master_triggers:
                        del self.master_triggers[old_pattern]
                        self.settings.beginGroup("master_overlays")
                        self.settings.remove(self.encode_key(old_pattern))
                        self.settings.endGroup()
                        for toon in self.toon_triggers:
                            if old_pattern in self.toon_triggers[toon]:
                                self.toon_triggers[toon].remove(old_pattern)
                                self.toon_triggers[toon].append(new_pattern)
                                self.settings.beginGroup(
                                    f"toon_overlays/{toon}")
                                self.settings.remove(
                                    self.encode_key(old_pattern))
                                self.settings.setValue(
                                    self.encode_key(new_pattern), "true")
                                self.settings.endGroup()
                    self.master_triggers[new_pattern] = {
                        'message': new_message, 'duration': new_duration}
                    self.settings.beginGroup("master_overlays")
                    self.settings.setValue(self.encode_key(new_pattern), f"{
                                           new_message}|{new_duration}")
                    self.settings.endGroup()
                    self.settings.sync()
                    self.load_triggers()
            except ValueError:
                QMessageBox.warning(self, "Invalid Input",
                                    "Duration must be a positive integer.")
                self.load_triggers()  # Revert

    def add_toon_trigger(self, row, column):
        if row >= 0:
            pattern = self.master_triggers_table.item(row, 0).text()
            if self.current_toon_for_triggers and pattern not in self.toon_triggers.get(self.current_toon_for_triggers, []):
                self.toon_triggers.setdefault(
                    self.current_toon_for_triggers, []).append(pattern)
                self.settings.beginGroup(
                    f"toon_overlays/{self.current_toon_for_triggers}")
                self.settings.setValue(self.encode_key(pattern), "true")
                self.settings.endGroup()
                self.settings.sync()
                self.load_toon_triggers()

    def remove_toon_trigger(self, row, column):
        if row >= 0:
            pattern = self.toon_triggers_table.item(row, 0).text()
            if self.current_toon_for_triggers and pattern in self.toon_triggers.get(self.current_toon_for_triggers, []):
                self.toon_triggers[self.current_toon_for_triggers].remove(
                    pattern)
                self.settings.beginGroup(
                    f"toon_overlays/{self.current_toon_for_triggers}")
                self.settings.remove(self.encode_key(pattern))
                self.settings.endGroup()
                self.settings.sync()
                self.load_toon_triggers()

    def toggle_overlays(self, state):
        self.enabled = state == Qt.CheckState.Checked.value
        self.settings.setValue("overlays_enabled", self.enabled)
        self.settings.sync()

    def process_log_line(self, line):
        if not self.enabled or not self.current_toon or self.current_toon not in self.toon_triggers:
            return
        for pattern in self.toon_triggers.get(self.current_toon, []):
            if pattern in line:  # Simple substring match; use re for advanced
                data = self.master_triggers.get(pattern, {})
                if data:
                    bar = TimerBar(data['message'],
                                   data['duration'], self.overlay_manager)
                    self.overlay_manager.add_bar(bar)
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
        self.settings.setValue("overlay_pos", self.overlay_manager.pos())
        self.overlay_manager.close()
        self.hide()
        event.accept()

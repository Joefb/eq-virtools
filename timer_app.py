import os
import re
from time import time
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QScrollArea, QLineEdit, QMenu
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

class MobTimerApp(QWidget):
    def __init__(self, log_dir):
        super().__init__()
        self.setWindowTitle("Mob Respawn Timer")
        self.log_dir = log_dir
        self.toon_name = "Unknown"
        self.log_path = None
        self.file = None
        self.log_position = 0
        self.timers = {}  # {mob_key: [QLabel, seconds, QTimer, mob_name]}
        self.mob_counts = {}
        self.setup_ui()
        self.load_active_log_file()
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.check_new_log_lines)
        self.poll_timer.start(1000)
        self.toon_check_timer = QTimer(self)
        self.toon_check_timer.timeout.connect(self.check_for_new_toon)
        self.toon_check_timer.start(3000)

    def update_log_directory(self, new_log_dir):
        self.log_dir = new_log_dir
        if self.file:
            self.file.close()
            self.file = None
        self.log_path = None
        self.log_position = 0
        self.load_active_log_file()

    def setup_ui(self):
        self.resize(280, 400)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(4, 4, 4, 4)
        self.toon_label = QLabel("Toon: Unknown")
        self.toon_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.toon_label)
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("Zone Respawn Time (e.g. 27:00)")
        main_layout.addWidget(self.time_input)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.timer_layout = QVBoxLayout(self.content)
        self.timer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.content)
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)
        self.timer_style = """
        QLabel {
            font-family: Monospace;
            font-size: 14px;
            padding: 4px 8px;
            margin: 0px;
            border: 1px solid #2a2a2a;
            background-color: #1a1a1a;
            color: #e0e0e0;
            min-width: 250px;
        }
        """

    def load_active_log_file(self):
        try:
            if not os.path.exists(self.log_dir):
                print(f"Log directory {self.log_dir} does not exist")
                return
            os.chdir(self.log_dir)
            log_files = [f for f in os.listdir() if f.startswith("eqlog_")]
            if not log_files:
                print(f"No log files found in {self.log_dir}")
                return
            log_files = sorted(log_files, key=lambda f: os.stat(f).st_mtime, reverse=True)
            new_log_file = log_files[0]
            new_toon = new_log_file.split("_")[1]
            if new_log_file != self.log_path:
                print(f"Switching to new toon log: {new_log_file}")
                self.log_path = new_log_file
                self.toon_name = new_toon
                self.toon_label.setText(f"Toon: {self.toon_name}")
                if self.file:
                    self.file.close()
                self.file = open(new_log_file, "r")
                self.file.seek(0, os.SEEK_END)
                self.log_position = self.file.tell()
        except Exception as e:
            print(f"Error loading log file: {e}")

    def check_for_new_toon(self):
        try:
            if not os.path.exists(self.log_dir):
                print(f"Log directory {self.log_dir} does not exist")
                return
            os.chdir(self.log_dir)
            log_files = [f for f in os.listdir() if f.startswith("eqlog_")]
            if not log_files:
                print(f"No log files found in {self.log_dir}")
                return
            log_files = sorted(log_files, key=lambda f: os.stat(f).st_mtime, reverse=True)
            latest_file = log_files[0]
            if latest_file != self.log_path:
                self.load_active_log_file()
        except Exception as e:
            print(f"Error checking for new toon: {e}")

    def check_new_log_lines(self):
        if not self.file or not os.path.exists(self.log_path):
            self.load_active_log_file()
            return
        try:
            self.file.seek(self.log_position)
            new_lines = self.file.readlines()
            self.log_position = self.file.tell()
            for line in new_lines:
                clean_line = re.sub(r'^\[.*?\]\s', '', line.strip())
                if clean_line:
                    self.process_log_line(clean_line)
        except Exception as e:
            print(f"Error reading log lines: {e}")

    def process_log_line(self, line):
        mob_name = None
        if ("has been slain by" in line or "You have slain" in line):
            try:
                mob_name = (
                    re.search(r"You have slain (.+?)!", line).group(1)
                    if "You have slain" in line
                    else re.search(r"(.+?) has been slain by", line).group(1)
                ).strip()
            except AttributeError:
                return
            mob_key = f"{mob_name}_{int(time() * 1000)}"
            minutes = 6
            seconds = 30
            user_time = self.time_input.text().strip()
            if re.match(r"^\d+:\d{2}$", user_time):
                try:
                    m, s = map(int, user_time.split(":"))
                    minutes, seconds = m, s
                except ValueError:
                    pass
            self.start_timer(mob_key, mob_name, minutes * 60 + seconds)

    def start_timer(self, mob_key: str, mob_name: str, seconds: int):
        print(f"Starting timer for {mob_key} ({mob_name}, {seconds}s)")
        label = ColorTimerLabel(f"{mob_name} - {seconds // 60}:{seconds % 60:02d}", mob_key)
        label.setStyleSheet(self.timer_style)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_layout.addWidget(label)
        timer = QTimer(self)
        timer.timeout.connect(lambda: self.update_timer(mob_key))
        timer.start(1000)
        self.timers[mob_key] = [label, seconds, timer, mob_name]
        label.double_clicked.connect(lambda: self.remove_timer(mob_key))

    def update_timer(self, mob_key):
        if mob_key not in self.timers:
            print(f"Timer {mob_key} not found in update_timer")
            return
        label, seconds, timer, mob_name = self.timers[mob_key]
        seconds -= 1
        if seconds <= 0:
            print(f"Timer {mob_key} expired")
            timer.stop()
            timer.timeout.disconnect()
            label.deleteLater()
            del self.timers[mob_key]
        else:
            mins, secs = divmod(seconds, 60)
            label.setText(f"{mob_name} - {mins}:{secs:02d}")
            self.timers[mob_key][1] = seconds

    def remove_timer(self, mob_key):
        if mob_key in self.timers:
            print(f"Removing timer {mob_key}")
            label, _, timer, _ = self.timers[mob_key]
            timer.stop()
            timer.timeout.disconnect()
            label.deleteLater()
            del self.timers[mob_key]

    def closeEvent(self, event):
        if self.file:
            self.file.close()
        event.accept()

class ColorTimerLabel(QLabel):
    double_clicked = pyqtSignal()
    def __init__(self, text, mob_key):
        super().__init__(text)
        self.mob_key = mob_key
        self.style_base = """
            font-family: Monospace;
            font-size: 14px;
            padding: 4px 8px;
            margin: 0px;
            border: 1px solid #2a2a2a;
            color: #e0e0e0;
        """
        self.setStyleSheet(f"{self.style_base} background-color: #1a1a1a;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)

    def show_context_menu(self, pos):
        menu = QMenu()
        colors = {
            "Default": "#1a1a1a",
            "Green": "#145214",
            "Blue": "#143052",
            "Red": "#521414",
            "Purple": "#361452"
        }
        for name, color in colors.items():
            action = QAction(name, self)
            action.triggered.connect(lambda checked, c=color: self.set_background_color(c))
            menu.addAction(action)
        menu.exec(self.mapToGlobal(pos))

    def set_background_color(self, color):
        self.setStyleSheet(f"{self.style_base} background-color: {color};")

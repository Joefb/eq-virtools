from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QFileDialog
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QSettings, QTimer, QThread, pyqtSignal
from timer_app import MobTimerApp
import voice_notifications_app
import importlib
import os
import re
from gtts import gTTS
import pygame
import time

# Ensure latest VoiceNotificationsApp is loaded
importlib.reload(voice_notifications_app)
VoiceNotificationsApp = voice_notifications_app.VoiceNotificationsApp

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

class MainApp:
    def __init__(self):
        if QApplication.instance():
            QApplication.instance().quit()
        self.app = QApplication([])
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setProperty("MainApp", self)
        self.settings = QSettings("EQ-Virtools", "MainApp")
        self.log_dir = self.settings.value("log_dir", "/home/jfburgess/Games/everquest/Logs/")
        self.log_path = None
        self.log_file = None
        self.log_position = 0
        self.toon_name = "Unknown"
        self.timer_window = None
        self.voice_window = None
        self.tts_thread = None
        self.voice_enabled = self.settings.value("voice_enabled", False, type=bool)
        self.triggers = self.settings.value("voice_triggers", {"Your root has broken": "Root has broken!", " resists your spell": "Spell resisted!"}, type=dict)
        self.load_active_log_file()
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "tray-icon.png"))
        print(f"Loading icon from: {icon_path}")
        icon = QIcon(icon_path)
        self.tray = QSystemTrayIcon(icon)
        if icon.isNull():
            print(f"Failed to load icon, using fallback")
            self.tray.setIcon(QIcon.fromTheme("application-x-executable"))
        else:
            print(f"Icon loaded successfully")
        self.tray.setVisible(True)
        print(f"Tray visible: {self.tray.isVisible()}")
        if self.tray.isSystemTrayAvailable():
            print(f"System tray available")
        else:
            print(f"System tray unavailable")
        self.menu = QMenu()
        self.setup_menu()
        self.tray.setContextMenu(self.menu)
        self.log_poll_timer = QTimer()
        self.log_poll_timer.timeout.connect(self.update_log_position)
        self.log_poll_timer.start(1000)

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
                print(f"Switching to new toon log: {new_log_file} (toon: {new_toon})")
                self.log_path = new_log_file
                self.toon_name = new_toon
                if self.log_file:
                    print(f"Closing previous log file: {self.log_path}")
                    self.log_file.close()
                    self.log_file = None
                try:
                    self.log_file = open(new_log_file, "r")
                    self.log_file.seek(0, os.SEEK_END)
                    self.log_position = self.log_file.tell()
                    print(f"Opened new log file: {self.log_path}, position: {self.log_position}")
                except Exception as e:
                    print(f"Error opening log file {new_log_file}: {e}")
                    self.log_file = None
                    self.log_path = None
                    self.log_position = 0
                if self.timer_window and hasattr(self.timer_window, 'update_toon'):
                    self.timer_window.update_toon(self.toon_name, self.log_file, self.log_path, self.log_position)
                if self.voice_window and hasattr(self.voice_window, 'update_log_info'):
                    self.voice_window.update_log_info(self.log_file, self.log_path, self.log_position)
        except Exception as e:
            print(f"Error loading log file: {e}")
            self.log_file = None
            self.log_path = None
            self.log_position = 0

    def update_log_position(self):
        if not self.log_file or not os.path.exists(self.log_path) or self.log_file.closed:
            print(f"Log file unavailable (file: {self.log_path}, closed: {self.log_file.closed if self.log_file else True}), attempting to reload")
            self.load_active_log_file()
            return
        try:
            self.log_file.seek(self.log_position)
            new_lines = self.log_file.readlines()
            self.log_position = self.log_file.tell()
            if self.voice_enabled and (not self.voice_window or not self.voice_window.isVisible()):
                for line in new_lines:
                    clean_line = re.sub(r'^\[.*?\]\s', '', line.strip())
                    if clean_line:
                        for pattern, message in self.triggers.items():
                            if pattern in clean_line:
                                print(f"Voice alert: {message}")
                                if self.tts_thread and self.tts_thread.isRunning():
                                    self.tts_thread.wait()
                                self.tts_thread = TTSThread(message)
                                self.tts_thread.start()
                                break
            if self.voice_window and self.voice_window.isVisible():
                print(f"Processing lines with VoiceNotificationsApp: {self.voice_window}")
                for line in new_lines:
                    clean_line = re.sub(r'^\[.*?\]\s', '', line.strip())
                    if clean_line:
                        if hasattr(self.voice_window, 'process_log_line'):
                            self.voice_window.process_log_line(clean_line)
                        else:
                            print(f"Error: VoiceNotificationsApp lacks process_log_line method")
        except Exception as e:
            print(f"Error updating log position: {e}")
            self.log_file = None
            self.log_path = None
            self.log_position = 0
            self.load_active_log_file()

    def setup_menu(self):
        timer_action = QAction("Timer Tool", self.menu)
        timer_action.triggered.connect(self.launch_timer_tool)
        self.menu.addAction(timer_action)
        voice_action = QAction("Voice Notifications", self.menu)
        voice_action.triggered.connect(self.launch_voice_notifications)
        self.menu.addAction(voice_action)
        placeholder_action = QAction("Other Tools (TBD)", self.menu)
        placeholder_action.setEnabled(False)
        self.menu.addAction(placeholder_action)
        settings_action = QAction("Set Log Directory", self.menu)
        settings_action.triggered.connect(self.select_log_directory)
        self.menu.addAction(settings_action)
        quit_action = QAction("Quit", self.menu)
        quit_action.triggered.connect(self.quit)
        self.menu.addAction(quit_action)

    def launch_timer_tool(self):
        if not self.timer_window:
            self.timer_window = MobTimerApp(self.log_dir, self.toon_name, self.log_file, self.log_path, self.log_position)
        self.timer_window.show()

    def launch_voice_notifications(self):
        if not self.voice_window:
            self.voice_window = VoiceNotificationsApp(self.log_dir)
            self.voice_window.update_log_info(self.log_file, self.log_path, self.log_position)
        self.voice_window.show()

    def select_log_directory(self):
        directory = QFileDialog.getExistingDirectory(None, "Select Log Directory", self.log_dir)
        if directory:
            self.log_dir = directory
            self.settings.setValue("log_dir", self.log_dir)
            print(f"Log directory set to: {self.log_dir}")
            if self.log_file:
                self.log_file.close()
                self.log_file = None
            self.log_path = None
            self.log_position = 0
            self.load_active_log_file()

    def update_voice_settings(self, enabled, triggers):
        self.voice_enabled = enabled
        self.triggers = triggers
        self.settings.setValue("voice_enabled", self.voice_enabled)
        self.settings.setValue("voice_triggers", self.triggers)

    def quit(self):
        if self.log_file and not self.log_file.closed:
            self.log_file.close()
        if self.tts_thread and self.tts_thread.isRunning():
            self.tts_thread.wait()
        self.app.quit()

    def run(self):
        self.app.exec()

if __name__ == "__main__":
    app = MainApp()
    app.run()

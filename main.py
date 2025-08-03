from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QFileDialog
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QSettings, QTimer
from timer_app import MobTimerApp
import os

class MainApp:
    def __init__(self):
        if QApplication.instance():
            QApplication.instance().quit()
        self.app = QApplication([])
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setProperty("MainApp", self)  # Store MainApp instance
        self.settings = QSettings("EverQuestTools", "MainApp")
        self.log_dir = self.settings.value("log_dir", "/home/jfburgess/Games/everquest/Logs/")
        self.log_path = None
        self.log_file = None
        self.log_position = 0
        self.toon_name = "Unknown"
        self.timer_window = None
        self.load_active_log_file()
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "tray-icon.png"))
        print(f"Loading icon from: {icon_path}")
        icon = QIcon(icon_path)
        self.tray = QSystemTrayIcon(icon)
        if icon.isNull():
            print("Failed to load icon, using fallback")
            self.tray.setIcon(QIcon.fromTheme("application-x-executable"))
        else:
            print("Icon loaded successfully")
        self.tray.setVisible(True)
        print(f"Tray visible: {self.tray.isVisible()}")
        if self.tray.isSystemTrayAvailable():
            print("System tray available")
        else:
            print("System tray unavailable")
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
                print(f"Switching to new toon log: {new_log_file}")
                self.log_path = new_log_file
                self.toon_name = new_toon
                if self.log_file:
                    self.log_file.close()
                self.log_file = open(new_log_file, "r")
                self.log_file.seek(0, os.SEEK_END)
                self.log_position = self.log_file.tell()
                if self.timer_window and hasattr(self.timer_window, 'update_toon'):
                    self.timer_window.update_toon(self.toon_name, self.log_file, self.log_path, self.log_position)
        except Exception as e:
            print(f"Error loading log file: {e}")

    def update_log_position(self):
        if not self.log_file or not os.path.exists(self.log_path):
            self.load_active_log_file()
            return
        try:
            self.log_file.seek(self.log_position)
            self.log_file.readlines()  # Read to advance position
            self.log_position = self.log_file.tell()
        except Exception as e:
            print(f"Error updating log position: {e}")

    def setup_menu(self):
        timer_action = QAction("Timer Tool", self.menu)
        timer_action.triggered.connect(self.launch_timer_tool)
        self.menu.addAction(timer_action)
        placeholder_action = QAction("Other Tools (TBD)", self.menu)
        placeholder_action.setEnabled(False)
        self.menu.addAction(placeholder_action)
        settings_action = QAction("Set Log Directory", self.menu)
        settings_action.triggered.connect(self.select_log_directory)
        self.menu.addAction(settings_action)
        quit_action = QAction("Quit", self.menu)
        quit_action.triggered.connect(self.quit)
        self.menu.addAction(quit_action)

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

    def launch_timer_tool(self):
        if not self.timer_window:
            self.timer_window = MobTimerApp(self.log_dir, self.toon_name, self.log_file, self.log_path, self.log_position)
        self.timer_window.show()

    def quit(self):
        if self.log_file:
            self.log_file.close()
        self.app.quit()

    def run(self):
        self.app.exec()

if __name__ == "__main__":
    app = MainApp()
    app.run()

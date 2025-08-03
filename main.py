from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QFileDialog
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QSettings
from timer_app import MobTimerApp

class MainApp:
    def __init__(self):
        self.app = QApplication([])
        self.settings = QSettings("EverQuestTools", "MainApp")
        self.log_dir = self.settings.value("log_dir", "/home/jfburgess/Games/everquest/Logs/")
        self.tray = QSystemTrayIcon(QIcon.fromTheme("utilities-terminal"))
        self.tray.setVisible(True)
        self.menu = QMenu()
        self.setup_menu()
        self.tray.setContextMenu(self.menu)
        self.timer_window = None

    def setup_menu(self):
        # Timer Tool
        timer_action = QAction("Timer Tool", self.menu)
        timer_action.triggered.connect(self.launch_timer_tool)
        self.menu.addAction(timer_action)

        # Placeholder for Future Tools
        placeholder_action = QAction("Other Tools (TBD)", self.menu)
        placeholder_action.setEnabled(False)
        self.menu.addAction(placeholder_action)

        # Settings
        settings_action = QAction("Set Log Directory", self.menu)
        settings_action.triggered.connect(self.select_log_directory)
        self.menu.addAction(settings_action)

        # Quit
        quit_action = QAction("Quit", self.menu)
        quit_action.triggered.connect(self.app.quit)
        self.menu.addAction(quit_action)

    def select_log_directory(self):
        directory = QFileDialog.getExistingDirectory(None, "Select Log Directory", self.log_dir)
        if directory:
            self.log_dir = directory
            self.settings.setValue("log_dir", self.log_dir)
            print(f"Log directory set to: {self.log_dir}")
            if self.timer_window:
                self.timer_window.update_log_directory(self.log_dir)

    def launch_timer_tool(self):
        if not self.timer_window or not self.timer_window.isVisible():
            self.timer_window = MobTimerApp(self.log_dir)
            self.timer_window.show()

    def run(self):
        self.app.exec()

if __name__ == "__main__":
    app = MainApp()
    app.run()

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QFileDialog
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QSettings, QTimer
from timer_app import MobTimerApp
import voice_notifications_app
import os
import re

# Zone timers from Project 1999 Wiki (in seconds)
ZONE_TIMERS = {
    "The Arena": 400, "Arena": 400,
    "Beholder's Maze": 360, "Gorge of King Xorbb": 360,
    "East Commonlands": 400, "Eastern Commonlands": 400,
    "Eastern Plains of Karana": 400, "Eastern Karana": 400,
    "Erud's Crossing": 400,
    "Everfrost Peaks": 400, "Everfrost": 400,
    "Highpass Hold": 300, "High Hold": 300,
    "Innothule Swamp": 400, "Innothule": 400,
    "Kithicor Forest": 400, "Kithicor": 400,
    "Lake Rathetear": 400, "Rathetear": 400,
    "Misty Thicket": 400,
    "Nektulos Forest": 400, "Nektulos": 400,
    "Northern Desert of Ro": 400, "North Ro": 400,
    "Northern Plains of Karana": 400, "Northern Karana": 400,
    "Oasis of Marr": 990, "Oasis": 990,
    "Ocean of Tears": 360,
    "Qeynos Hills": 400, "Qeynos Hills": 400,
    "Rathe Mountains": 400, "Rathe Mtns": 400,
    "Southern Desert of Ro": 400, "South Ro": 400,
    "Southern Karana": 360,
    "The Feerrott": 400, "Feerrott": 400,
    "West Commonlands": 400, "Western Commonlands": 400,
    "Western Plains of Karana": 400, "Western Karana": 400,
    "Grobb": 1440,
    "Halas": 1440,
    "Neriak": 1440,
    "Freeport": 1440,
    "Qeynos": 400,
    "Oggok": 1440,
    "Rivervale": 1320,
    "Surefall Glade": 400,
    "Befallen": 1140,
    "Blackburrow": 1320,
    "Cazic Thule": 1320,
    "Clan Runnyeye": 1320, "Runnyeye": 1320,
    "High Keep": 600,
    "Lower Guk": 1680,
    "Nagafen's Lair": 1320, "Solusek B": 1320,
    "Najena": 1110,
    "Permafrost": 1320,
    "Qeynos Catacombs": 720, "Qeynos Sewers": 720,
    "Solusek's Eye": 1080, "Solusek A": 1080,
    "Splitpaw Lair": 1320, "Splitpaw": 1320,
    "The Temple of Solusek Ro": 300, "Solusek Ro": 300,
    "Upper Guk": 990,
    "Erudin": 400,
    "Erudin Palace": 1500,
    "Paineel": 630,
    "Kerra Island": 1065, "Kerra Isle": 1065,
    "Toxxulia Forest": 400, "Toxxulia": 400,
    "The Hole": 1290,
    "Stonebrunt Mountains": 670, "Stonebrunt": 670,
    "The Warrens": 400, "Warrens": 400,
    "Ak'Anon": 400, "Ak`Anon": 400,
    "Felwithe": 1440,
    "Kaladim": 400,
    "Kelethin": 400, "Greater Faydark": 400,
    "Butcherblock Mountains": 600, "Butcherblock": 600,
    "Dagnor's Cauldron": 400,
    "Greater Faydark": 425,
    "Lesser Faydark": 390,
    "Steamfont Mountains": 400, "Steamfont": 400,
    "Crushbone": 540,
    "Kedge Keep": 1320, "Kedge": 1320,
    "Mistmoore Castle": 1320, "Mistmoore": 1320,
    "The Estate of Unrest": 1320, "Unrest": 1320,
    "Burning Wood": 400, "Burning Woods": 400,
    "Dreadlands": 400,
    "Emerald Jungle": 400,
    "Field of Bone": 400,
    "Firiona Vie": 400,
    "Frontier Mountains": 400,
    "Lake of Ill Omen": 400,
    "The Overthere": 400, "Overthere": 400,
    "Skyfire Mountains": 780, "Skyfire": 780,
    "Swamp of No Hope": 400,
    "Timorous Deep": 720,
    "Trakanon's Teeth": 400,
    "Warsliks Woods": 400,
    "Cabilis": 400,
    "Chardok": 1080,
    "City of Mist": 1320,
    "Dalnir": 720,
    "Howling Stones": 1230, "Charasis": 1230,
    "Kaesora": 1080,
    "Karnor's Castle": 1620, "Karnor": 1620,
    "Kurn's Tower": 1100, "Kurn": 1100,
    "Mines of Nurga": 1230, "Nurga": 1230,
    "Old Sebilis": 1620, "Sebilis": 1620,
    "Temple of Droga": 1230, "Droga": 1230,
    "Veeshan's Peak": 400,
    "Cobalt Scar": 1200,
    "Eastern Wastes": 400,
    "The Great Divide": 640, "Great Divide": 640,
    "Iceclad Ocean": 400, "Iceclad": 400,
    "Wakening Land": 400,
    "Western Wastes": 400,
    "Icewell Keep": 1260,
    "Kael Drakkal": 1680, "Kael": 1680,
    "Skyshrine": 1800,
    "Thurgadin": 420,
    "Crystal Caverns": 885,
    "Dragon Necropolis": 1620,
    "Siren's Grotto": 1680, "Sirens": 1680,
    "Sleeper's Tomb": 28800,
    "Temple of Veeshan": 43200,
    "Tower of Frozen Shadow": 1200, "Frozen Shadow": 1200,
    "Velketor's Labyrinth": 1970, "Velketor": 1970,
    "Plane of Fear": 28800,
    "Plane of Hate": 28800,
    "Plane of Sky": 28800,
    "Plane of Growth": 43200,
    "Plane of Mischief": 4210
}

# Map /who names to zone entry names for consistency
WHO_TO_ZONE = {
    "Northern Karana": "Northern Plains of Karana",
    "Eastern Karana": "Eastern Plains of Karana",
    "Western Karana": "Western Plains of Karana",
    "Eastern Commonlands": "East Commonlands",
    "Western Commonlands": "West Commonlands",
    "Gorge of King Xorbb": "Beholder's Maze",
    "High Hold": "Highpass Hold",
    "Innothule": "Innothule Swamp",
    "Kithicor": "Kithicor Forest",
    "Rathetear": "Lake Rathetear",
    "North Ro": "Northern Desert of Ro",
    "South Ro": "Southern Desert of Ro",
    "Feerrott": "The Feerrott",
    "Everfrost": "Everfrost Peaks",
    "Oasis": "Oasis of Marr",
    "Runnyeye": "Clan Runnyeye",
    "Solusek B": "Nagafen's Lair",
    "Solusek A": "Solusek's Eye",
    "Splitpaw": "Splitpaw Lair",
    "Solusek Ro": "The Temple of Solusek Ro",
    "Qeynos Sewers": "Qeynos Catacombs",
    "Kerra Isle": "Kerra Island",
    "Toxxulia": "Toxxulia Forest",
    "Warrens": "The Warrens",
    "Ak`Anon": "Ak'Anon",
    "Greater Faydark": "Kelethin",
    "Butcherblock": "Butcherblock Mountains",
    "Kedge": "Kedge Keep",
    "Mistmoore": "Mistmoore Castle",
    "Unrest": "The Estate of Unrest",
    "Burning Woods": "Burning Wood",
    "Overthere": "The Overthere",
    "Skyfire": "Skyfire Mountains",
    "Charasis": "Howling Stones",
    "Karnor": "Karnor's Castle",
    "Kurn": "Kurn's Tower",
    "Nurga": "Mines of Nurga",
    "Sebilis": "Old Sebilis",
    "Droga": "Temple of Droga",
    "Great Divide": "The Great Divide",
    "Iceclad": "Iceclad Ocean",
    "Kael": "Kael Drakkal",
    "Sirens": "Siren's Grotto",
    "Frozen Shadow": "Tower of Frozen Shadow",
    "Velketor": "Velketor's Labyrinth"
}

class MainApp:
    def __init__(self):
        if QApplication.instance():
            QApplication.instance().quit()
        self.app = QApplication([])
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setProperty("MainApp", self)
        config_dir = os.path.abspath("./config")
        os.makedirs(config_dir, exist_ok=True)
        config_file = os.path.join(config_dir, "main-app.ini")
        self.settings = QSettings(config_file, QSettings.Format.IniFormat)
        self.log_dir = self.settings.value("General/log_dir", os.getenv("LOG_DIR", "/app/logs"), type=str)
        self.log_path = None
        self.log_file = None
        self.log_position = 0
        self.toon_name = "Unknown"
        self.current_zone = "Unknown"
        self.zone_timer = 400  # Default 6:40
        self.timer_window = None
        self.voice_window = None
        self.load_active_log_file()
        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "tray-icon.png"))
        icon = QIcon(icon_path)
        self.tray = QSystemTrayIcon(icon)
        if icon.isNull():
            self.tray.setIcon(QIcon.fromTheme("application-x-executable"))
        self.tray.setVisible(True)
        self.menu = QMenu()
        self.setup_menu()
        self.tray.setContextMenu(self.menu)
        self.log_poll_timer = QTimer()
        self.log_poll_timer.timeout.connect(self.update_log_position)
        self.log_poll_timer.start(1000)

    def load_active_log_file(self):
        try:
            if not os.path.exists(self.log_dir):
                return False
            os.chdir(self.log_dir)
            log_files = [f for f in os.listdir() if f.startswith("eqlog_")]
            if not log_files:
                return False
            log_files = sorted(log_files, key=lambda f: os.stat(f).st_mtime, reverse=True)
            new_log_file = log_files[0]
            new_toon = new_log_file.split("_")[1]
            if new_log_file != self.log_path or (self.log_file and self.log_file.closed):
                self.log_path = new_log_file
                self.toon_name = new_toon
                if self.log_file and not self.log_file.closed:
                    self.log_file.close()
                    self.log_file = None
                try:
                    self.log_file = open(new_log_file, "r")
                    self.log_file.seek(0, os.SEEK_END)
                    self.log_position = self.log_file.tell()
                except Exception as e:
                    self.log_file = None
                    self.log_path = None
                    self.log_position = 0
                    return False
                if self.timer_window and hasattr(self.timer_window, 'update_toon'):
                    self.timer_window.update_toon(self.toon_name, self.log_file, self.log_path, self.log_position, self.current_zone, self.zone_timer)
                if self.voice_window and hasattr(self.voice_window, 'update_log_info'):
                    self.voice_window.update_log_info(self.log_file, self.log_path, self.log_position)
                return True
            return True
        except Exception as e:
            self.log_file = None
            self.log_path = None
            self.log_position = 0
            return False

    def update_log_position(self):
        try:
            if not self.log_file or not os.path.exists(self.log_path) or self.log_file.closed:
                if not self.load_active_log_file():
                    return
            self.log_file.seek(self.log_position)
            new_lines = self.log_file.readlines()
            self.log_position = self.log_file.tell()
            for line in new_lines:
                clean_line = re.sub(r'^\[.*?\]\s', '', line.strip())
                if clean_line:
                    # Zone detection
                    zone_entry = re.match(r"You have entered (.*?)\.", clean_line)
                    who_single = re.match(r"There is 1 player in (.*?)\.", clean_line)
                    who_multi = re.match(r"There are \d+ players in (.*?)\.", clean_line)
                    zone_name = None
                    if zone_entry:
                        zone_name = zone_entry.group(1)
                    elif who_single:
                        zone_name = WHO_TO_ZONE.get(who_single.group(1), who_single.group(1))
                    elif who_multi:
                        zone_name = WHO_TO_ZONE.get(who_multi.group(1), who_multi.group(1))
                    if zone_name and zone_name != self.current_zone:
                        self.current_zone = zone_name
                        self.zone_timer = ZONE_TIMERS.get(zone_name, 400)
                        if self.timer_window and hasattr(self.timer_window, 'update_zone'):
                            self.timer_window.update_zone(self.current_zone, self.zone_timer)
                    if self.voice_window and self.voice_window.isVisible():
                        if hasattr(self.voice_window, 'process_log_line'):
                            self.voice_window.process_log_line(clean_line)
        except Exception as e:
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
            self.timer_window = MobTimerApp(self.log_dir, self.toon_name, self.log_file, self.log_path, self.log_position, self.current_zone, self.zone_timer)
        self.timer_window.show()

    def launch_voice_notifications(self):
        if not self.voice_window:
            self.voice_window = voice_notifications_app.VoiceNotificationsApp(self.log_dir)
            self.voice_window.update_log_info(self.log_file, self.log_path, self.log_position)
        self.voice_window.show()

    def select_log_directory(self):
        directory = QFileDialog.getExistingDirectory(None, "Select Log Directory", self.log_dir)
        if directory:
            self.log_dir = directory
            self.settings.beginGroup("General")
            self.settings.setValue("log_dir", self.log_dir)
            self.settings.endGroup()
            self.settings.sync()
            if self.log_file and not self.log_file.closed:
                self.log_file.close()
                self.log_file = None
            self.log_path = None
            self.log_position = 0
            self.current_zone = "Unknown"
            self.zone_timer = 400
            self.load_active_log_file()

    def quit(self):
        if self.log_file and not self.log_file.closed:
            self.log_file.close()
        self.app.quit()

    def run(self):
        self.app.exec()

if __name__ == "__main__":
    app = MainApp()
    app.run()

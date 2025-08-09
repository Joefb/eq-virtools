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

# Zone timers from Project 1999 Wiki (in seconds)
# Maps both zone entry names (e.g., "Northern Plains of Karana") and /who names (e.g., "Northern Karana")
ZONE_TIMERS = {
    "The Arena": 400, "Arena": 400,  # Default 6:40 (N/A, no NPCs)
    "Beholder's Maze": 360, "Gorge of King Xorbb": 360,  # 6:00
    "East Commonlands": 400, "Eastern Commonlands": 400,  # 6:40
    "Eastern Plains of Karana": 400, "Eastern Karana": 400,  # 6:40
    "Erud's Crossing": 400,  # 6:40 (same for both)
    "Everfrost Peaks": 400, "Everfrost": 400,  # 6:40
    "Highpass Hold": 300, "High Hold": 300,  # 5:00 (first listed)
    "Innothule Swamp": 400, "Innothule": 400,  # 6:40
    "Kithicor Forest": 400, "Kithicor": 400,  # 6:40
    "Lake Rathetear": 400, "Rathetear": 400,  # 6:40
    "Misty Thicket": 400,  # 6:40 (same for both)
    "Nektulos Forest": 400, "Nektulos": 400,  # 6:40
    "Northern Desert of Ro": 400, "North Ro": 400,  # 6:40
    "Northern Plains of Karana": 400, "Northern Karana": 400,  # 6:40
    "Oasis of Marr": 990, "Oasis": 990,  # 16:30
    "Ocean of Tears": 360,  # 6:00 (same for both)
    "Qeynos Hills": 400, "Qeynos Hills": 400,  # 6:40
    "Rathe Mountains": 400, "Rathe Mtns": 400,  # 6:40
    "Southern Desert of Ro": 400, "South Ro": 400,  # 6:40
    "Southern Karana": 360,  # 6:00 (same for both)
    "The Feerrott": 400, "Feerrott": 400,  # 6:40
    "West Commonlands": 400, "Western Commonlands": 400,  # 6:40
    "Western Plains of Karana": 400, "Western Karana": 400,  # 6:40
    "Grobb": 1440,  # 24:00 (same for both)
    "Halas": 1440,  # 24:00 (same for both)
    "Neriak": 1440,  # 24:00 (same for both)
    "Freeport": 1440,  # 24:00 (same for both)
    "Qeynos": 400,  # 6:40 (same for both)
    "Oggok": 1440,  # 24:00 (same for both)
    "Rivervale": 1320,  # 22:00 (same for both)
    "Surefall Glade": 400,  # 6:40 (same for both)
    "Befallen": 1140,  # 19:00 (same for both)
    "Blackburrow": 1320,  # 22:00 (same for both)
    "Cazic Thule": 1320,  # 22:00 (same for both)
    "Clan Runnyeye": 1320, "Runnyeye": 1320,  # 22:00
    "High Keep": 600,  # 10:00 (Goblins, first listed)
    "Lower Guk": 1680,  # 28:00 (same for both)
    "Nagafen's Lair": 1320, "Solusek B": 1320,  # 22:00
    "Najena": 1110,  # 18:30 (same for both)
    "Permafrost": 1320,  # 22:00 (same for both)
    "Qeynos Catacombs": 720, "Qeynos Sewers": 720,  # 12:00 (first listed)
    "Solusek's Eye": 1080, "Solusek A": 1080,  # 18:00
    "Splitpaw Lair": 1320, "Splitpaw": 1320,  # 22:00 (Gnolls, first listed)
    "The Temple of Solusek Ro": 300, "Solusek Ro": 300,  # 5:00
    "Upper Guk": 990,  # 16:30 (same for both)
    "Erudin": 400,  # 6:40 (Sharks)
    "Erudin Palace": 1500,  # 25:00 (same for both)
    "Paineel": 630,  # 10:30 (same for both)
    "Kerra Island": 1065, "Kerra Isle": 1065,  # 17:45
    "Toxxulia Forest": 400, "Toxxulia": 400,  # 6:40
    "The Hole": 1290,  # 21:30 (same for both)
    "Stonebrunt Mountains": 670, "Stonebrunt": 670,  # 11:10
    "The Warrens": 400, "Warrens": 400,  # 6:40
    "Ak'Anon": 400, "Ak`Anon": 400,  # 6:40
    "Felwithe": 1440,  # 24:00 (same for both)
    "Kaladim": 400,  # 6:40 (same for both)
    "Kelethin": 400, "Greater Faydark": 400,  # Default 6:40 (MM:SS)
    "Butcherblock Mountains": 600, "Butcherblock": 600,  # 10:00 (first listed)
    "Dagnor's Cauldron": 400,  # Default 6:40 (MM:SS)
    "Greater Faydark": 425,  # 7:05
    "Lesser Faydark": 390,  # 6:30 (same for both)
    "Steamfont Mountains": 400, "Steamfont": 400,  # 6:40
    "Crushbone": 540,  # 9:00 (same for both)
    "Kedge Keep": 1320, "Kedge": 1320,  # 22:00
    "Mistmoore Castle": 1320, "Mistmoore": 1320,  # 22:00
    "The Estate of Unrest": 1320, "Unrest": 1320,  # 22:00
    "Burning Wood": 400, "Burning Woods": 400,  # 6:40
    "Dreadlands": 400,  # 6:40 (same for both)
    "Emerald Jungle": 400,  # Default 6:40 (MM:SS)
    "Field of Bone": 400,  # 6:40 (same for both)
    "Firiona Vie": 400,  # 6:40 (same for both)
    "Frontier Mountains": 400,  # 6:40 (same for both)
    "Lake of Ill Omen": 400,  # 6:40 (same for both)
    "The Overthere": 400, "Overthere": 400,  # 6:40
    "Skyfire Mountains": 780, "Skyfire": 780,  # 13:00
    "Swamp of No Hope": 400,  # 6:40 (same for both)
    "Timorous Deep": 720,  # 12:00 (same for both)
    "Trakanon's Teeth": 400,  # 6:40 (same for both)
    "Warsliks Woods": 400,  # 6:40 (same for both)
    "Cabilis": 400,  # 6:40 (same for both)
    "Chardok": 1080,  # 18:00 (same for both)
    "City of Mist": 1320,  # 22:00 (same for both)
    "Dalnir": 720,  # 12:00 (same for both)
    "Howling Stones": 1230, "Charasis": 1230,  # 20:30
    "Kaesora": 1080,  # 18:00 (same for both)
    "Karnor's Castle": 1620, "Karnor": 1620,  # 27:00
    "Kurn's Tower": 1100, "Kurn": 1100,  # 18:20
    "Mines of Nurga": 1230, "Nurga": 1230,  # 20:30
    "Old Sebilis": 1620, "Sebilis": 1620,  # 27:00
    "Temple of Droga": 1230, "Droga": 1230,  # 20:30
    "Veeshan's Peak": 400,  # Default 6:40 (MM:SS)
    "Cobalt Scar": 1200,  # 20:00 (same for both)
    "Eastern Wastes": 400,  # 6:40 (same for both)
    "The Great Divide": 640, "Great Divide": 640,  # 10:40
    "Iceclad Ocean": 400, "Iceclad": 400,  # 6:40
    "Wakening Land": 400,  # 6:40 (first listed)
    "Western Wastes": 400,  # Default 6:40 (MM:SS)
    "Icewell Keep": 1260,  # 21:00 (same for both)
    "Kael Drakkal": 1680, "Kael": 1680,  # 28:00
    "Skyshrine": 1800,  # 30:00 (same for both)
    "Thurgadin": 420,  # 7:00 (same for both)
    "Crystal Caverns": 885,  # 14:45 (same for both)
    "Dragon Necropolis": 1620,  # 27:00 (same for both)
    "Siren's Grotto": 1680, "Sirens": 1680,  # 28:00
    "Sleeper's Tomb": 28800,  # 8:00:00 (same for both)
    "Temple of Veeshan": 43200,  # 72:00 (same for both)
    "Tower of Frozen Shadow": 1200, "Frozen Shadow": 1200,  # 20:00
    "Velketor's Labyrinth": 1970, "Velketor": 1970,  # 32:50
    "Plane of Fear": 28800,  # 8:00:00 (same for both)
    "Plane of Hate": 28800,  # 8:00:00 (same for both)
    "Plane of Sky": 28800,  # 8:00:00 (same for both)
    "Plane of Growth": 43200,  # 12:00:00 (same for both)
    "Plane of Mischief": 4210  # 01:10:10 (same for both)
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
        self.current_zone = "Unknown"
        self.zone_timer = 400  # Default 6:40
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
                return False
            os.chdir(self.log_dir)
            log_files = [f for f in os.listdir() if f.startswith("eqlog_")]
            if not log_files:
                print(f"No log files found in {self.log_dir}, will retry")
                return False
            log_files = sorted(log_files, key=lambda f: os.stat(f).st_mtime, reverse=True)
            new_log_file = log_files[0]
            new_toon = new_log_file.split("_")[1]
            if new_log_file != self.log_path or (self.log_file and self.log_file.closed):
                print(f"Switching to new toon log: {new_log_file} (toon: {new_toon})")
                self.log_path = new_log_file
                self.toon_name = new_toon
                if self.log_file and not self.log_file.closed:
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
                    return False
                if self.timer_window and hasattr(self.timer_window, 'update_toon'):
                    self.timer_window.update_toon(self.toon_name, self.log_file, self.log_path, self.log_position, self.current_zone, self.zone_timer)
                if self.voice_window and hasattr(self.voice_window, 'update_log_info'):
                    self.voice_window.update_log_info(self.log_file, self.log_path, self.log_position)
                return True
            return True
        except Exception as e:
            print(f"Error loading log file: {e}")
            self.log_file = None
            self.log_path = None
            self.log_position = 0
            return False

    def update_log_position(self):
        try:
            if self.log_path and os.path.exists(self.log_dir):
                log_files = [f for f in os.listdir(self.log_dir) if f.startswith("eqlog_")]
                if log_files:
                    latest_log = max(log_files, key=lambda f: os.stat(os.path.join(self.log_dir, f)).st_mtime)
                    if latest_log != self.log_path:
                        print(f"Detected newer log file: {latest_log}, current: {self.log_path}")
                        self.load_active_log_file()
        except Exception as e:
            print(f"Error checking for new log files: {e}")

        if not self.log_file or not os.path.exists(self.log_path) or self.log_file.closed:
            print(f"Log file unavailable (file: {self.log_path}, closed: {self.log_file.closed if self.log_file else True}), attempting to reload")
            if not self.load_active_log_file():
                return
        try:
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
                        self.zone_timer = ZONE_TIMERS.get(zone_name, 400)  # Default 6:40
                        print(f"Detected zone: {self.current_zone}, timer: {self.zone_timer} seconds")
                        if self.timer_window and hasattr(self.timer_window, 'update_zone'):
                            self.timer_window.update_zone(self.current_zone, self.zone_timer)
                    # Voice notifications
                    if self.voice_enabled and (not self.voice_window or not self.voice_window.isVisible()):
                        for pattern, message in self.triggers.items():
                            if pattern in clean_line:
                                print(f"Voice alert: {message}")
                                if self.tts_thread and self.tts_thread.isRunning():
                                    self.tts_thread.wait()
                                self.tts_thread = TTSThread(message)
                                self.tts_thread.start()
                                break
                    if self.voice_window and self.voice_window.isVisible():
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
            self.timer_window = MobTimerApp(self.log_dir, self.toon_name, self.log_file, self.log_path, self.log_position, self.current_zone, self.zone_timer)
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
            if self.log_file and not self.log_file.closed:
                self.log_file.close()
                self.log_file = None
            self.log_path = None
            self.log_position = 0
            self.current_zone = "Unknown"
            self.zone_timer = 400
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

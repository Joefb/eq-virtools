# EQ-Virtools

EQ-Virtools is a Linux-only utility for EverQuest, providing mob respawn timers and voice notifications from game logs. It features a system tray app with a timer tool and voice alert configuration.

## Prerequisites

- **Operating System**: Linux (Ubuntu, Fedora, Arch).
- **Python**: 3.10 or higher.
- **Log Files**: EverQuest logs in `/home/$USER/Games/everquest/Logs` (e.g., `eqlog_CharacterName_server.txt`).
- **Dependencies**:
  - System: `python3`, `python3-pip`, `libasound2`, `libx11-6`, `libxcb1`.
  - Python: `gTTS`, `PyQt6`, `pygame`.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/eq-virtools.git
   cd eq-virtools
   ```

2. Install dependencies:

   **Ubuntu (24.04 or later)**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip libasound2 libx11-6 libxcb1
   pip3 install gTTS==2.5.1 PyQt6==6.7.0 pygame==2.5.2
   ```

   **Fedora (40 or later)**:
   ```bash
   sudo dnf install python3 python3-pip alsa-lib libX11 libxcb
   pip3 install gTTS==2.5.1 PyQt6==6.7.0 pygame==2.5.2
   ```

   **Arch Linux**:
   ```bash
   sudo pacman -Sy python python-pip alsa-lib libx11 libxcb
   pip3 install gTTS==2.5.1 PyQt6==6.7.0 pygame==2.5.2
   ```

## Usage

1. Ensure logs are in `/home/$USER/Games/everquest/Logs`.
2. Run the app:
   ```bash
   ./run.sh
   ```
3. System tray icon:
   - **Timer Tool**: Shows mob timers with zone detection (e.g., “Zone: Northern Karana (6:40)”).
   - **Voice Notifications**: Configure alerts (e.g., “Root has broken!”).
   - **Quit**: Exit app.
4. Timer Tool:
   - Timers start on mob kills (e.g., “You have slain a willowisp!”).
   - Double-click to remove timers.
   - Right-click for color options (Default, Green, Blue, Red, Purple).
   - Enter custom time (e.g., “27:00”) or use zone default.

## Troubleshooting

- **No system tray**: Enable `ubuntu-appindicators` in GNOME Extensions.
- **Audio issues**: Test ALSA:
  ```bash
  aplay /usr/share/sounds/alsa/Front_Center.wav
  ```
  Install `alsa-utils` if needed (`sudo apt install alsa-utils`).
- **Log issues**: Check permissions:
  ```bash
  chmod -R u+rw /home/$USER/Games/everquest/Logs
  ```
- **Python errors**: Verify Python 3.10+ and packages:
  ```bash
  python3 --version
  pip3 list | grep -E "gTTS|PyQt6|pygame"
  ```

## Contributing

Submit issues or PRs on GitHub. Use feature branches for changes.

## License

[MIT License](LICENSE)
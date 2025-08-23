# EQ-Virtools

EQ-Virtools is a Linux-only utility for EverQuest, providing mob respawn timers and voice notifications from game logs. It runs in a system tray with a timer tool and voice alert configuration.

## Prerequisites

- **Operating System**: Linux (Arch, Ubuntu, Fedora, etc.).
- **Python**: 3.10 or higher (for manual install).
- **Docker**: Required for containerized setup (optional).
- **Log Files**: EverQuest logs in `/home/$USER/Games/everquest/Logs` (e.g., `eqlog_CharacterName_server.txt`).
- **Dependencies**:
  - System: `python3`, `python3-pip`, `libasound2`, `libx11-6`, `libxcb1` (manual install).
  - Python: `gTTS==2.5.1`, `PyQt6==6.7.0`, `pygame==2.5.2` (manual or Docker).
  - Docker: Includes all dependencies (`libqt6core6`, `libqt6gui6`, `libqt6widgets6`, `libsdl2-2.0-0`, etc.).

## Installation

### Option 1: Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/eq-virtools.git
   cd eq-virtools
   ```
2. Install dependencies:

   **Arch Linux**:
   ```bash
   sudo pacman -Sy python python-pip alsa-lib libx11 libxcb
   pip3 install gTTS==2.5.1 PyQt6==6.7.0 pygame==2.5.2
   ```

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

### Option 2: Docker Installation

1. Install Docker:
   - **Arch**: `sudo pacman -S docker && sudo systemctl enable --now docker`
   - **Ubuntu**: `sudo apt install docker.io && sudo systemctl enable --now docker`
   - **Fedora**: `sudo dnf install docker && sudo systemctl enable --now docker`
2. Clone the repository:
   ```bash
   git clone https://github.com/your-username/eq-virtools.git
   cd eq-virtools
   ```
3. Build the Docker image:
   ```bash
   docker build -t eq-virtools .
   ```
4. Run the container, mounting your log directory:
   ```bash
   xhost +local:docker
   docker run --rm -it -v /home/$USER/Games/everquest/Logs:/app/logs --env DISPLAY=$DISPLAY --net=host eq-virtools
   ```

## Usage

1. Ensure logs are in `/home/$USER/Games/everquest/Logs`.
2. Run the app:
   - Manual: `./run.sh`
   - Docker: See Docker installation step 4.
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
  Install `alsa-utils` (`sudo pacman -S alsa-utils`).
- **Log issues**: Check permissions:
  ```bash
  chmod -R u+rw /home/$USER/Games/everquest/Logs
  ```
- **Docker issues**: Ensure Docker is running and logs are mounted.

## Contributing

Submit issues or PRs on GitHub. Use feature branches.

## License

[MIT License](LICENSE)
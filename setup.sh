#!/bin/bash

# setup.sh: Install dependencies for EQ-Virtools on Linux
# Supports Ubuntu, Fedora, Arch

set -e

# Display usage information
usage() {
    echo "Usage: $0 [--help]"
    echo "Installs system and Python dependencies for EQ-Virtools."
    echo "  --help    Display this help message and exit"
    exit 0
}

# Check for help flag
if [ "$1" = "--help" ]; then
    usage
fi

# Check for root privileges (for sudo)
check_sudo() {
    if ! command -v sudo >/dev/null 2>&1; then
        echo "Error: 'sudo' is required but not installed. Please install it and run again."
        exit 1
    fi
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        echo "Detected distribution: $DISTRO"
    else
        echo "Error: Cannot detect distribution. /etc/os-release not found."
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    echo "Installing system dependencies..."
    case $DISTRO in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y python3 python3-pip libasound2 libx11-6 libxcb1
            ;;
        fedora)
            sudo dnf install -y python3 python3-pip alsa-lib libX11 libxcb
            ;;
        arch)
            sudo pacman -Sy --noconfirm python python-pip alsa-lib libx11 libxcb
            ;;
        *)
            echo "Error: Unsupported distribution '$DISTRO'. Supported: ubuntu, fedora, arch."
            exit 1
            ;;
    esac
    echo "System dependencies installed."
}

# Check Python version (3.10+)
check_python() {
    if ! command -v python3 >/dev/null 2>&1; then
        echo "Error: Python3 not found. Please install Python 3.10+."
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)
    if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
        echo "Error: Python 3.10+ required, found $PYTHON_VERSION."
        exit 1
    fi
    echo "Python $PYTHON_VERSION found."
}

# Check pip
check_pip() {
    if ! command -v pip3 >/dev/null 2>&1; then
        echo "Error: pip3 not found. Please install python3-pip."
        exit 1
    fi
    echo "pip3 found."
}

# Install Python dependencies
install_python_deps() {
    echo "Installing Python dependencies from requirements.txt..."
    if [ ! -f requirements.txt ]; then
        echo "Error: requirements.txt not found in current directory."
        exit 1
    fi
    pip3 install -r requirements.txt
    echo "Python dependencies installed."
}

# Verify installations
verify_install() {
    echo "Verifying installations..."
    for pkg in gTTS PyQt6 pygame; do
        if pip3 show "$pkg" >/dev/null 2>&1; then
            echo "$pkg is installed."
        else
            echo "Error: $pkg failed to install."
            exit 1
        fi
    done
    if command -v python3 >/dev/null 2>&1 && command -v pip3 >/dev/null 2>&1; then
        echo "System dependencies verified."
    else
        echo "Error: System dependencies (python3 or pip3) missing."
        exit 1
    fi
}

# Main installation process
main() {
    echo "Starting EQ-Virtools dependency installation..."
    check_sudo
    detect_distro
    install_system_deps
    check_python
    check_pip
    install_python_deps
    verify_install
    echo "Installation complete! Run './run.sh' to start EQ-Virtools."
    echo "Ensure log files are in /home/$USER/Games/everquest/Logs."
}

main

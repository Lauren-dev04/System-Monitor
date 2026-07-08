#!/bin/bash
# Build script for System Monitor

echo " Building System Monitor..."

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install dependencies
pip install -r requirements.txt pyinstaller

# Build with PyInstaller
pyinstaller --noconfirm --onefile --windowed \
    --name "SystemMonitor" \
    --icon="icon.png" \
    --add-data "src/ui:ui" \
    --add-data "src/hardware:hardware" \
    --hidden-import "psutil" \
    --hidden-import "pyrsmi" \
    --hidden-import "PySide6" \
    src/main.py

echo "Build complete! Executable in dist/SystemMonitor"

#!/bin/bash
# FFConverter Launcher
# Extract to any folder and run this!

cd "$(dirname "$0")"

# Hybrid FFmpeg detection: system first, then bundled
if command -v ffmpeg >/dev/null 2>&1; then
    # Use system ffmpeg
    echo "Using system FFmpeg"
else
    # Use bundled ffmpeg
    echo "Using bundled FFmpeg"
    export PATH="$(pwd)/usr/bin:$PATH"
fi

# Find Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Error: Python not found"
    echo "Install python3: sudo apt install python3"
    exit 1
fi

# Run the app
exec $PYTHON "$(pwd)/ffc.py" "$@"
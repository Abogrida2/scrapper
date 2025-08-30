#!/bin/bash
echo "=== STARTING BUILD ==="
echo "Current directory: $(pwd)"
echo "Listing files:"
ls -la

echo "=== INSTALLING PACKAGES ==="
pip install --upgrade pip
pip install Flask==2.3.3
pip install yt-dlp==2023.12.30
pip install Werkzeug==2.3.7
pip install requests==2.31.0

echo "=== BUILD COMPLETED ==="
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version)"
echo "Installed packages:"
pip list

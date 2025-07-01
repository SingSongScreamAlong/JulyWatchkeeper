#!/usr/bin/env python3
"""
WATCHKEEPER - Dependency Installer
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def install_dependencies():
    print("🛡️ WATCHKEEPER - Dependency Installation")
    print("=" * 50)
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    
    print(f"✅ Python version: {sys.version}")
    
    commands = [
        ("pip3 install -r requirements.txt", "Installing Python packages"),
        ("playwright install chromium", "Installing Playwright browser"),
        ("python3 -c \"import nltk; nltk.download('vader_lexicon', quiet=True)\"", "Downloading NLTK data")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    directories = ["data", "data/logs", "config"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    print("\n✅ All dependencies installed successfully!")
    return True

if __name__ == "__main__":
    success = install_dependencies()
    sys.exit(0 if success else 1)

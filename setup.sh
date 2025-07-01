#!/bin/bash

echo "🛡️ WATCHKEEPER - Automated Setup"
echo "=========================================="

if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is designed for macOS"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Installing via Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install python3
fi

echo "✅ Python 3 found: $(python3 --version)"

echo "🔧 Creating virtual environment..."
python3 -m venv watchkeeper_env
source watchkeeper_env/bin/activate

pip install --upgrade pip

echo "📦 Installing Python packages..."
pip install -r requirements.txt

echo "🌐 Installing Playwright browsers..."
playwright install chromium

echo "📚 Downloading NLTK sentiment data..."
python3 -c "import nltk; nltk.download('vader_lexicon', quiet=True)"

echo "📁 Creating directory structure..."
mkdir -p data/logs
mkdir -p config

chmod +x scripts/*.py
chmod +x guardian.py

echo "✅ WATCHKEEPER setup complete!"
echo ""
echo "🚀 To start WATCHKEEPER:"
echo "   source watchkeeper_env/bin/activate"
echo "   python3 guardian.py"

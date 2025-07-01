# 🚀 WATCHKEEPER - Quick Start Guide

## Installation (5 minutes)

### Option 1: Automated Setup
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup
```bash
pip3 install -r requirements.txt
playwright install chromium
python3 -c "import nltk; nltk.download('vader_lexicon')"
python3 scripts/test_system.py
```

## First Run

### Demo Mode (Recommended)
```bash
python3 guardian.py --demo
```

### Continuous Monitoring
```bash
python3 guardian.py --monitor --cycle-minutes 30
```

## What You'll See

1. **Initialization**: Browser and AI components start
2. **Intelligence Collection**: RSS feeds and web investigation
3. **Threat Assessment**: AI analysis of collected data
4. **Alerts**: Console display of important findings
5. **Summary**: Statistics and top threats/opportunities

## Customization

Edit `config/settings.json` to adjust:
- Alert thresholds
- Monitoring frequency
- Geographic focus
- Performance settings

## Troubleshooting

- **Memory issues**: Reduce `max_concurrent_agents` in settings
- **Browser errors**: Run `playwright install chromium` again
- **Network errors**: Check firewall settings
- **Performance**: Increase cycle time for older hardware

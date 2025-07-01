#!/usr/bin/env python3
"""
WATCHKEEPER - Startup Script
"""

import sys
import argparse
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="🛡️ WATCHKEEPER Startup")
    parser.add_argument("--mode", choices=["demo", "monitor", "test"], 
                       default="demo", help="Startup mode")
    parser.add_argument("--cycle-minutes", type=int, default=30,
                       help="Minutes between monitoring cycles")
    
    args = parser.parse_args()
    
    guardian_path = Path("guardian.py")
    if not guardian_path.exists():
        print("❌ guardian.py not found. Make sure you're in the correct directory.")
        sys.exit(1)
    
    print("🛡️ WATCHKEEPER - Starting...")
    
    if args.mode == "test":
        print("🧪 Running system tests...")
        subprocess.run([sys.executable, "scripts/test_system.py"])
    elif args.mode == "demo":
        print("🎬 Running demonstration...")
        subprocess.run([sys.executable, "guardian.py", "--demo"])
    elif args.mode == "monitor":
        print(f"👁️ Starting continuous monitoring (cycle: {args.cycle_minutes} min)")
        subprocess.run([sys.executable, "guardian.py", "--monitor", 
                       "--cycle-minutes", str(args.cycle_minutes)])

if __name__ == "__main__":
    main()

"""HASSAN DAILY: fetch prices → safety checks → write Arabic text → render → verify → email.

Usage:
    python main.py                          # full run
    python main.py --no-history --no-email  # local test: don't save prices, don't send email
"""

import argparse
import sys

from src.pipeline import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-history", action="store_true", help="don't save today's prices to history")
    parser.add_argument("--no-email", action="store_true", help="print results instead of emailing them")
    args = parser.parse_args()
    sys.exit(run(save_history=not args.no_history, email=not args.no_email))

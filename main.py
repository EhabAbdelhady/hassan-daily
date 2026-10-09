"""HASSAN DAILY: prepare today's infographic, then publish it.

Usage:
    python main.py                # prepare (checks + preview email); also publishes if REQUIRE_APPROVAL=false
    python main.py prepare        # prepare only
    python main.py publish        # publish the prepared post (the "approve" step)
    python main.py --dry-run      # like DRY_RUN=true: never uploads or posts
    python main.py --no-history --no-email   # local test: don't save prices, don't send email
"""

import argparse
import sys

from src.config import settings
from src.pipeline import run

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("step", nargs="?", default="all", choices=["all", "prepare", "publish"])
    parser.add_argument("--dry-run", action="store_true", help="never upload or post (overrides DRY_RUN)")
    parser.add_argument("--no-history", action="store_true", help="don't save today's prices to history")
    parser.add_argument("--no-email", action="store_true", help="print results instead of emailing them")
    args = parser.parse_args()
    if args.dry_run:
        settings.DRY_RUN = True
    sys.exit(run(step=args.step, save_history=not args.no_history, email=not args.no_email))

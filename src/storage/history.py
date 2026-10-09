"""History storage and delta calculator for daily market indicators."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from ..config import settings


class HistoryStorage:
    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or settings.HISTORY_FILE
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def load_history(self) -> Dict[str, Any]:
        """Loads historical records from disk."""
        if not self.history_file.exists():
            return {"records": []}
            
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"records": []}

    def get_latest_record(self) -> Optional[Dict[str, Any]]:
        """Returns the most recent historical record."""
        data = self.load_history()
        records = data.get("records", [])
        if records:
            return records[-1]
        return None

    def calculate_delta(self, current_price: float, previous_price: Optional[float]) -> Tuple[float, float, str, bool]:
        """Calculates percentage change and returns (pct, nominal_diff, formatted_string, is_positive)."""
        if not previous_price or previous_price <= 0:
            return 0.0, 0.0, "0.00%", True

        nominal_diff = current_price - previous_price
        pct = (nominal_diff / previous_price) * 100
        is_positive = pct >= 0
        sign = "+" if is_positive else ""
        formatted = f"{sign}{pct:.2f}%"

        return pct, nominal_diff, formatted, is_positive

    def save_record(
        self,
        gold_24k: float,
        gold_21k: float,
        gold_18k: float,
        usd_buy: float,
        usd_sell: float,
        btc_price: float,
        brent_price: float
    ) -> Dict[str, Any]:
        """Appends a new day's record to the history file."""
        data = self.load_history()
        records = data.setdefault("records", [])

        new_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "gold": {
                "24k": gold_24k,
                "21k": gold_21k,
                "18k": gold_18k
            },
            "usd_egp": {
                "buy": usd_buy,
                "sell": usd_sell
            },
            "bitcoin": {
                "price": btc_price
            },
            "brent": {
                "price": brent_price
            }
        }

        # Keep history records limited to last 365 days
        records.append(new_record)
        if len(records) > 365:
            records = records[-365:]
        data["records"] = records

        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return new_record

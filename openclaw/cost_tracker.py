"""
cost_tracker.py
Tracks local vs cloud calls and estimates tokens saved.
Logs to D:\CLAUDE\logs\ with date prefix.
"""
import json
from datetime import date
from pathlib import Path
from loguru import logger

# Approximate cost per 1M tokens (input)
_COST_PER_MTK = {
    "claude-sonnet-4-6":           3.00,
    "claude-haiku-4-5-20251001":   0.80,
    "local":                       0.00,
}
_AVG_TOKENS_PER_CALL = 500   # conservative estimate


class CostTracker:
    def __init__(self):
        self._log_dir = Path(r"D:\CLAUDE\logs")
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._today_file = self._log_dir / f"{date.today().strftime('%Y%m%d')}_openclaw_usage.json"
        self._data = self._load()

    def record(self, decision):
        backend = decision.backend
        key = "local" if backend in ("ollama", "lmstudio") else decision.model

        self._data["calls"] = self._data.get("calls", 0) + 1
        self._data.setdefault("by_backend", {})
        self._data["by_backend"][backend] = self._data["by_backend"].get(backend, 0) + 1
        self._data.setdefault("by_model", {})
        self._data["by_model"][decision.model] = self._data["by_model"].get(decision.model, 0) + 1

        # Cost saved vs all-Sonnet
        saved = (_COST_PER_MTK["claude-sonnet-4-6"] - _COST_PER_MTK.get(key, 0)) \
                * _AVG_TOKENS_PER_CALL / 1_000_000
        self._data["usd_saved"] = round(self._data.get("usd_saved", 0.0) + saved, 6)
        self._save()

    def summary(self) -> dict:
        return self._data

    def print_summary(self):
        d = self._data
        total = d.get("calls", 0)
        local = sum(v for k, v in d.get("by_backend", {}).items() if k != "claude")
        cloud = d.get("by_backend", {}).get("claude", 0)
        pct   = round(local / total * 100) if total else 0
        print(f"\n{'='*50}")
        print(f"OpenClaw Usage — {date.today()}")
        print(f"{'='*50}")
        print(f"  Total calls : {total}")
        print(f"  Local       : {local} ({pct}%)")
        print(f"  Cloud       : {cloud} ({100-pct}%)")
        print(f"  $ Saved     : ${d.get('usd_saved', 0):.4f} (vs all-Sonnet)")
        print(f"{'='*50}\n")

    def _load(self) -> dict:
        if self._today_file.exists():
            return json.loads(self._today_file.read_text())
        return {}

    def _save(self):
        self._today_file.write_text(json.dumps(self._data, indent=2))

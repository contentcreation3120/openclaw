"""
Tests for chat() in openclaw_web.py.
Mocks openclaw.router.router.route and openclaw_web.fetch_quote to avoid live servers.
Run with: pytest tests/test_chat_flow.py -v
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Ensure the project root is importable
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# Import the module under test
import openclaw_web
from openclaw_web import chat


# ── Shared mock fixtures ──────────────────────────────────────────────────────

STOCK_QUOTE = {
    "symbol": "MSTR",
    "price": 350.00,
    "change": 5.00,
    "change_pct": 1.45,
    "day_high": 355.00,
    "day_low": 345.00,
    "prev_close": 345.00,
    "volume": 1_200_000,
    "rsi_14": 58.3,
}

# Use ZB (30Y Bond futures) — it IS in FUTURES_SYMBOLS and NOT in _COMMON_WORDS
FUTURES_QUOTE = {
    "symbol": "ZB",
    "price": 115.50,
    "change": 0.25,
    "change_pct": 0.22,
    "day_high": 116.00,
    "day_low": 115.00,
    "prev_close": 115.25,
    "volume": 80_000,
    "rsi_14": 48.2,
}
FUTURES_TICKER = "ZB"  # a futures symbol that survives extract_tickers()


# ── Bare ticker → menu ────────────────────────────────────────────────────────

class TestBareTickerMenu:
    def test_mstr_lowercase_shows_clarify(self):
        with patch("openclaw_web.fetch_quote", return_value=STOCK_QUOTE):
            result = chat("mstr", [])
        assert "[clarify]" in result
        assert "MSTR" in result

    def test_mstr_uppercase_shows_clarify(self):
        with patch("openclaw_web.fetch_quote", return_value=STOCK_QUOTE):
            result = chat("MSTR", [])
        assert "[clarify]" in result
        assert "MSTR" in result

    def test_zb_lowercase_shows_futures_menu(self):
        # ZB (30Y Bond futures) — in FUTURES_SYMBOLS and not filtered by _COMMON_WORDS
        with patch("openclaw_web.fetch_quote", return_value=FUTURES_QUOTE):
            result = chat("zb", [])
        assert "[clarify]" in result
        assert "Futures" in result

    def test_zb_uppercase_shows_futures_menu(self):
        with patch("openclaw_web.fetch_quote", return_value=FUTURES_QUOTE):
            result = chat("ZB", [])
        assert "[clarify]" in result
        assert "Futures" in result


# ── Numbered selection after stock menu ───────────────────────────────────────

class TestNumberedSelectionStock:
    STOCK_CLARIFY_HISTORY = [
        ("mstr", "> **[clarify]** Stock detected: **`MSTR`** — $350.00")
    ]

    def test_selection_1_swing_trade(self):
        captured = {}
        def fake_route(prompt):
            captured["prompt"] = prompt
            return "swing trade analysis"

        with patch("openclaw_web.openclaw_route", side_effect=fake_route):
            chat("1", self.STOCK_CLARIFY_HISTORY)

        assert "MSTR" in captured["prompt"]
        assert "swing" in captured["prompt"].lower()

    def test_selection_2_day_trade(self):
        captured = {}
        def fake_route(prompt):
            captured["prompt"] = prompt
            return "day trade analysis"

        with patch("openclaw_web.openclaw_route", side_effect=fake_route):
            chat("2", self.STOCK_CLARIFY_HISTORY)

        assert "day trade" in captured["prompt"].lower()


# ── Numbered selection after futures menu ─────────────────────────────────────

class TestNumberedSelectionFutures:
    FUTURES_CLARIFY_HISTORY = [
        ("zb", "> **[clarify]** Futures detected: **`ZB`** — $115.50")
    ]

    def test_selection_1_day_trade_futures(self):
        captured = {}
        def fake_route(prompt):
            captured["prompt"] = prompt
            return "futures day trade analysis"

        with patch("openclaw_web.openclaw_route", side_effect=fake_route):
            chat("1", self.FUTURES_CLARIFY_HISTORY)

        assert "ZB" in captured["prompt"]
        assert "day trade" in captured["prompt"].lower()


# ── Follow-ups inject context ─────────────────────────────────────────────────

class TestFollowUpContextInjection:
    PREVIOUS_HISTORY = [
        ("swing trade MSTR", "Here is your setup: Entry $350, SL $340, TP $370")
    ]

    def test_yes_injects_context(self):
        captured = {}
        def fake_route(prompt):
            captured["prompt"] = prompt
            return "continuing..."

        with patch("openclaw_web.openclaw_route", side_effect=fake_route):
            chat("yes", self.PREVIOUS_HISTORY)

        assert "Context from previous exchange" in captured["prompt"]

    def test_ok_injects_context(self):
        captured = {}
        def fake_route(prompt):
            captured["prompt"] = prompt
            return "continuing..."

        with patch("openclaw_web.openclaw_route", side_effect=fake_route):
            chat("ok", self.PREVIOUS_HISTORY)

        assert "Context from previous exchange" in captured["prompt"]

    def test_go_ahead_injects_context(self):
        captured = {}
        def fake_route(prompt):
            captured["prompt"] = prompt
            return "continuing..."

        with patch("openclaw_web.openclaw_route", side_effect=fake_route):
            chat("go ahead", self.PREVIOUS_HISTORY)

        assert "Context from previous exchange" in captured["prompt"]


# ── Empty / whitespace ────────────────────────────────────────────────────────

class TestEmptyInput:
    def test_empty_string(self):
        assert chat("", []) == ""

    def test_whitespace_only(self):
        assert chat("   ", []) == ""


# ── Normal routing (no ticker menu) ──────────────────────────────────────────

class TestNormalRouting:
    def test_swing_trade_with_keyword_routes_directly(self):
        """'swing' is a strategy keyword — should go to route(), not menu."""
        called = {}
        def fake_route(prompt):
            called["hit"] = True
            return "setup"

        with patch("openclaw_web.openclaw_route", side_effect=fake_route):
            result = chat("swing trade setup for MSTR", [])

        assert called.get("hit") is True

    def test_plan_my_trading_day_routes(self):
        called = {}
        def fake_route(prompt):
            called["hit"] = True
            return "planning response"

        # patch extract_tickers to return [] so no ticker menu fires
        with patch("openclaw_web.openclaw_route", side_effect=fake_route), \
             patch("openclaw_web.extract_tickers", return_value=[]):
            chat("plan my trading day for tomorrow", [])

        assert called.get("hit") is True

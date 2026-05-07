"""
Edge case / "10-year-old breaking the app" test suite.
Nothing here should crash — every call must return a valid string or empty string.
Run with: pytest tests/test_edge_cases.py -v
"""
import sys
import os
import pytest
from unittest.mock import patch

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from openclaw.router.classifier import classify, RouteDecision
from openclaw.market_data import extract_tickers
import openclaw_web
from openclaw_web import chat


# ── classify() must never raise ───────────────────────────────────────────────

class TestClassifyEdgeCases:
    def _ok(self, prompt):
        d = classify(prompt)
        assert isinstance(d, RouteDecision)
        assert d.task_type is not None
        return d

    def test_empty_string(self):
        self._ok("")

    def test_whitespace_only(self):
        self._ok("     ")

    def test_numbers_only(self):
        self._ok("12345")

    def test_emoji_rockets(self):
        self._ok("🚀🚀🚀 to the moon")

    def test_all_caps_question(self):
        self._ok("WHAT IS THE BEST TRADE RIGHT NOW")

    def test_sql_injection(self):
        self._ok("'; DROP TABLE trades;--")

    def test_xss_attempt(self):
        self._ok("<script>alert('xss')</script>")

    def test_greek_letters_with_ticker(self):
        self._ok("αβγδ tell me about MSTR")

    def test_newlines_in_message(self):
        self._ok("swing\ntrade\nMSTR\nnow")

    def test_random_nonsense(self):
        self._ok("xkcd fjqw bvzp qlrm")

    def test_repeated_ticker(self):
        self._ok("MSTR MSTR MSTR MSTR")

    def test_all_return_non_none_task_type(self):
        prompts = [
            "", "     ", "12345", "🚀🚀🚀 to the moon",
            "WHAT IS THE BEST TRADE RIGHT NOW", "'; DROP TABLE trades;--",
            "<script>alert('xss')</script>", "αβγδ tell me about MSTR",
            "swing\ntrade\nMSTR\nnow", "xkcd fjqw bvzp qlrm", "MSTR MSTR MSTR MSTR",
        ]
        for p in prompts:
            d = classify(p)
            assert d.task_type is not None, f"task_type is None for prompt: {p!r}"


# ── extract_tickers() must never raise ───────────────────────────────────────

class TestExtractTickersEdgeCases:
    def test_empty_string(self):
        result = extract_tickers("")
        assert isinstance(result, list)

    def test_emoji_with_ticker(self):
        result = extract_tickers("🚀 MSTR 🌙")
        assert "MSTR" in result

    def test_sql_injection(self):
        result = extract_tickers("'; DROP TABLE--")
        assert isinstance(result, list)

    def test_numbers_only(self):
        result = extract_tickers("12345 67890")
        assert result == []

    def test_lowercase_multiple_tickers(self):
        result = extract_tickers("mstr aapl nvda tsla")
        assert "MSTR" in result
        assert "AAPL" in result
        assert "NVDA" in result
        assert "TSLA" in result


# ── chat() must never crash ───────────────────────────────────────────────────

def _mock_route(prompt):
    return "ok"


class TestChatEdgeCases:
    def test_empty_string(self):
        assert chat("", []) == ""

    def test_whitespace_only(self):
        assert chat("   ", []) == ""

    def test_emoji_only(self):
        with patch("openclaw_web.openclaw_route", side_effect=_mock_route):
            result = chat("🚀🚀🚀", [])
        assert isinstance(result, str)

    def test_numbers_only(self):
        with patch("openclaw_web.openclaw_route", side_effect=_mock_route):
            result = chat("12345", [])
        assert isinstance(result, str)

    def test_xss_attempt(self):
        with patch("openclaw_web.openclaw_route", side_effect=_mock_route):
            result = chat("<script>alert('xss')</script>", [])
        assert isinstance(result, str)

    def test_sql_injection(self):
        with patch("openclaw_web.openclaw_route", side_effect=_mock_route):
            result = chat("'; DROP TABLE trades;--", [])
        assert isinstance(result, str)

    def test_very_long_message(self):
        with patch("openclaw_web.openclaw_route", side_effect=_mock_route):
            result = chat("swing trade MSTR " * 200, [])
        assert isinstance(result, str)

    def test_unicode_with_ticker(self):
        with patch("openclaw_web.openclaw_route", side_effect=_mock_route):
            result = chat("αβγδ MSTR swing trade", [])
        assert isinstance(result, str)

    def test_newlines_in_message(self):
        with patch("openclaw_web.openclaw_route", side_effect=_mock_route):
            result = chat("swing\ntrade\nMSTR", [])
        assert isinstance(result, str)

    def test_invalid_menu_option_no_crash(self):
        history = [("mstr", "> **[clarify]** Stock detected: `MSTR`")]
        with patch("openclaw_web.openclaw_route", side_effect=_mock_route):
            result = chat("9", history)
        assert isinstance(result, str)

    def test_selection_without_history(self):
        with patch("openclaw_web.openclaw_route", side_effect=_mock_route):
            result = chat("1", [])
        assert isinstance(result, str)

    def test_followup_without_history(self):
        with patch("openclaw_web.openclaw_route", side_effect=_mock_route):
            result = chat("yes", [])
        assert isinstance(result, str)


# ── Error handling ────────────────────────────────────────────────────────────

class TestChatErrorHandling:
    def test_route_raises_exception(self):
        def bad_route(prompt):
            raise Exception("model crashed")

        with patch("openclaw_web.openclaw_route", side_effect=bad_route):
            result = chat("swing trade MSTR", [])
        assert isinstance(result, str)
        assert "Error" in result

    def test_route_returns_none(self):
        with patch("openclaw_web.openclaw_route", return_value=None):
            result = chat("swing trade MSTR", [])
        assert isinstance(result, str)

    def test_route_returns_empty_string(self):
        with patch("openclaw_web.openclaw_route", return_value=""):
            result = chat("swing trade MSTR", [])
        assert isinstance(result, str)

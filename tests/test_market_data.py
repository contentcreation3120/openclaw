"""
Tests for openclaw/market_data.py
Run with: pytest tests/test_market_data.py -v
"""
import pytest
from openclaw.market_data import extract_tickers, is_futures


# ── extract_tickers ───────────────────────────────────────────────────────────

class TestExtractTickers:
    # Lowercase / mixed-case fix (text.upper() applied before regex)
    def test_lowercase_mstr(self):
        result = extract_tickers("mstr strategy")
        assert "MSTR" in result

    def test_uppercase_mstr(self):
        result = extract_tickers("MSTR strategy")
        assert "MSTR" in result

    def test_mixedcase_mstr(self):
        result = extract_tickers("MStr strategy")
        assert "MSTR" in result

    def test_lowercase_aapl(self):
        # MNQ is in _COMMON_WORDS (futures symbol) — use a stock ticker to test lowercase
        result = extract_tickers("aapl trade setup")
        assert "AAPL" in result

    # Multiple tickers
    def test_multiple_tickers(self):
        result = extract_tickers("compare AAPL and MSFT performance")
        assert "AAPL" in result
        assert "MSFT" in result

    # Common words filtered
    def test_common_words_filtered(self):
        result = extract_tickers("I AM IN a good trade today")
        assert "I" not in result
        assert "AM" not in result
        assert "IN" not in result
        assert "A" not in result

    # Indicator names filtered (_COMMON_WORDS includes RSI, MACD, VWAP)
    def test_rsi_filtered(self):
        result = extract_tickers("RSI is at 70 and MACD crossed")
        assert "RSI" not in result
        assert "MACD" not in result

    def test_vwap_filtered(self):
        result = extract_tickers("price is above VWAP today")
        assert "VWAP" not in result

    # Edge cases
    def test_empty_string(self):
        assert extract_tickers("") == []

    def test_no_tickers_from_filtered_words(self):
        # Known common/indicator words are filtered; "TO", "OF", "THE", "AND", "FOR" all filtered
        result = extract_tickers("to of the and for")
        for t in result:
            assert t not in {"TO", "OF", "THE", "AND", "FOR"}

    def test_single_char_filtered(self):
        # Single char tokens must be filtered (len >= 2 required)
        result = extract_tickers("X Y Z trade")
        for t in result:
            assert len(t) >= 2

    # Returns list of strings, uppercased
    def test_returns_list(self):
        result = extract_tickers("AAPL trade setup")
        assert isinstance(result, list)

    def test_results_are_uppercase(self):
        result = extract_tickers("aapl msft nvda")
        for t in result:
            assert t == t.upper()


# ── is_futures ────────────────────────────────────────────────────────────────

class TestIsFutures:
    def test_mnq_true(self):
        assert is_futures("MNQ") is True

    def test_es_true(self):
        assert is_futures("ES") is True

    def test_nq_true(self):
        assert is_futures("NQ") is True

    def test_aapl_false(self):
        assert is_futures("AAPL") is False

    def test_mstr_false(self):
        assert is_futures("MSTR") is False

    # Case insensitive via .upper()
    def test_lowercase_mnq(self):
        assert is_futures("mnq") is True

    def test_mixedcase_mnq(self):
        assert is_futures("Mnq") is True

    def test_unknown_symbol_false(self):
        assert is_futures("XYZQ") is False

    def test_cl_true(self):
        assert is_futures("CL") is True

    def test_gc_true(self):
        assert is_futures("GC") is True

    def test_ym_true(self):
        assert is_futures("YM") is True

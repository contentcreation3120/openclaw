"""
Tests for the classifier using the current API.
Run with: pytest tests/test_classifier.py -v
"""
import pytest
from openclaw.router.classifier import classify, RouteDecision


# ── Helpers ─────────────────────────────────────────────────────────────────

def _c(prompt):
    d = classify(prompt)
    assert isinstance(d, RouteDecision)
    return d


# ── Code routing ─────────────────────────────────────────────────────────────

class TestCodeRouting:
    def test_write_a_function(self):
        d = _c("write a function that calculates win rate")
        assert d.task_type == "code"
        assert d.backend == "lmstudio"

    def test_debug_this(self):
        d = _c("debug this traceback AttributeError on line 42")
        assert d.task_type == "code"
        assert d.backend == "lmstudio"

    def test_fix_the_bug(self):
        d = _c("fix the bug in my function")
        assert d.task_type == "code"
        assert d.backend == "lmstudio"

    def test_how_do_i_parse_json(self):
        d = _c("how do I parse JSON in Python")
        assert d.task_type == "code"
        assert d.backend == "lmstudio"

    def test_sql_query(self):
        d = _c("SQL query to get all trades from last week")
        assert d.task_type == "code"
        assert d.backend == "lmstudio"

    def test_code_wins_over_trading(self):
        # Code keywords checked first — should be code even though "trading" is in prompt
        d = _c("write a trading strategy in Python")
        assert d.task_type == "code"


# ── Trading routing ───────────────────────────────────────────────────────────

class TestTradingRouting:
    def test_should_i_enter(self):
        d = _c("should I enter this long on MNQ right now")
        assert d.task_type == "trading"
        assert d.backend == "ollama"

    def test_stop_loss(self):
        d = _c("where should I put my stop loss for this trade")
        assert d.task_type == "trading"
        assert d.backend == "ollama"

    def test_apex(self):
        d = _c("apex funded account rules for daily loss limit")
        assert d.task_type == "trading"
        assert d.backend == "ollama"

    def test_swing_trade_tsla(self):
        d = _c("swing trade TSLA setup for next week")
        assert d.task_type == "trading"
        assert d.backend == "ollama"

    def test_day_trade_nvda(self):
        d = _c("day trade NVDA intraday setup")
        assert d.task_type == "trading"
        assert d.backend == "ollama"

    def test_bullish(self):
        d = _c("market looks bullish today what is your take")
        assert d.task_type == "trading"
        assert d.backend == "ollama"

    def test_entry_price_target(self):
        d = _c("entry price target for this setup")
        assert d.task_type == "trading"
        assert d.backend == "ollama"


# ── Signal routing ────────────────────────────────────────────────────────────

class TestSignalRouting:
    def test_rsi_at_72(self):
        d = _c("RSI at 72 is this overbought")
        assert d.task_type == "signal"

    def test_vwap_rejected(self):
        d = _c("VWAP rejected twice now looking weak")
        assert d.task_type == "signal"

    def test_macd_crossed(self):
        # Avoid "chart", "bullish" (trading kw); "MACD crossed above signal line" is clean
        d = _c("MACD crossed above signal line")
        assert d.task_type == "signal"

    def test_support_resistance(self):
        d = _c("price at major support resistance zone")
        assert d.task_type == "signal"

    def test_breakout(self):
        d = _c("breakout above the daily high with volume")
        assert d.task_type == "signal"


# ── Research routing ──────────────────────────────────────────────────────────

class TestResearchRouting:
    def test_explain_iv_rank(self):
        # Use "what is" to hit research; avoid "IV rank" which is in _SIGNAL_KEYWORDS
        d = _c("what is implied volatility rank and why does it matter")
        assert d.task_type == "research"

    def test_what_is_credit_spread(self):
        d = _c("what is a credit spread and how does it work")
        assert d.task_type == "research"

    def test_compare_spy_qqq(self):
        d = _c("compare SPY vs QQQ performance this year")
        assert d.task_type == "research"

    def test_news_about_tesla(self):
        d = _c("news about Tesla and what is moving the stock")
        assert d.task_type == "research"


# ── Writing routing ───────────────────────────────────────────────────────────

class TestWritingRouting:
    def test_draft_a_letter(self):
        # "draft" is a writing keyword; avoid "my account" (trading) and "ema" inside "email"
        d = _c("draft a letter to my broker about fees")
        assert d.task_type == "writing"

    def test_compose_a_post(self):
        # "compose" is a writing keyword; avoids "write a " code prefix
        d = _c("compose a LinkedIn post about my trading journey")
        assert d.task_type == "writing"

    def test_rewrite_this(self):
        d = _c("rewrite this paragraph to sound more professional")
        assert d.task_type == "writing"


# ── Planning routing ──────────────────────────────────────────────────────────

class TestPlanningRouting:
    def test_plan_my_trading_day(self):
        d = _c("plan my trading day for tomorrow morning")
        assert d.task_type == "planning"

    def test_what_should_i_focus_on(self):
        d = _c("what should I focus on this week to improve")
        assert d.task_type == "planning"

    def test_set_my_goals(self):
        d = _c("set goals for this month around position sizing")
        assert d.task_type == "planning"


# ── Journal routing ───────────────────────────────────────────────────────────

class TestJournalRouting:
    def test_session_recap(self):
        d = _c("session recap for today 3 wins 2 losses up $240")
        assert d.task_type == "journal"

    def test_calculate_win_rate(self):
        d = _c("calculate my win rate from these trades")
        assert d.task_type == "journal"

    def test_trade_log(self):
        d = _c("here is my trade log for the week review it")
        assert d.task_type == "journal"


# ── General fallback ──────────────────────────────────────────────────────────

class TestGeneralFallback:
    def test_hello_there(self):
        d = _c("hello there")
        assert d.task_type == "general"

    def test_how_are_you(self):
        d = _c("how are you doing today")
        assert d.task_type == "general"


# ── Long context ──────────────────────────────────────────────────────────────

class TestLongContext:
    def test_500x_market_context(self):
        d = _c("market context " * 500)
        assert d.task_type == "long_context"


# ── Backend checks ────────────────────────────────────────────────────────────

class TestBackendRouting:
    def test_code_goes_to_lmstudio(self):
        d = _c("write a function to calculate RSI")
        assert d.backend == "lmstudio"

    def test_trading_goes_to_ollama(self):
        d = _c("should I enter this trade at VWAP")
        assert d.backend == "ollama"

    def test_general_goes_to_ollama(self):
        d = _c("hello there")
        assert d.backend == "ollama"


# ── RouteDecision fields ──────────────────────────────────────────────────────

class TestRouteDecisionFields:
    def test_all_fields_present(self):
        d = classify("write a function")
        assert d.task_type is not None
        assert d.model is not None
        assert d.backend is not None
        assert d.reason is not None

    def test_returns_route_decision(self):
        d = classify("hello")
        assert isinstance(d, RouteDecision)

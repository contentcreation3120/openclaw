"""
Tests for the task classifier.  Run with: pytest tests/
"""

import pytest
from openclaw.router.classifier import TaskClassifier, TaskTier


@pytest.fixture
def clf():
    return TaskClassifier()


class TestStrategyRouting:
    def test_should_i_trade(self, clf):
        result = clf.classify("Should I trade this setup given the macro environment?")
        assert result.tier == TaskTier.CLOUD_SONNET
        assert result.use_case == "strategy_decision"

    def test_portfolio_allocation(self, clf):
        result = clf.classify("What portfolio allocation makes sense with 3 open positions?")
        assert result.tier == TaskTier.CLOUD_SONNET

    def test_recommend_keyword(self, clf):
        result = clf.classify("Can you recommend how to size this trade?")
        assert result.tier == TaskTier.CLOUD_SONNET


class TestCodeRouting:
    def test_python_code_block(self, clf):
        result = clf.classify("```python\ndef compute_rsi(prices): pass\n```  fix this")
        assert result.tier == TaskTier.LOCAL_CODE
        assert result.use_case == "code_generation"

    def test_backtest_keyword(self, clf):
        result = clf.classify("Write a backtest for my EMA crossover strategy in pandas")
        assert result.tier == TaskTier.LOCAL_CODE

    def test_debug_keyword(self, clf):
        result = clf.classify("Debug this traceback: AttributeError on line 42")
        assert result.tier == TaskTier.LOCAL_CODE


class TestSignalRouting:
    def test_rsi_signal(self, clf):
        result = clf.classify("RSI is at 28 and MACD is crossing up — should I act on this signal?")
        assert result.tier == TaskTier.LOCAL_MID
        assert result.use_case == "signal_analysis"

    def test_vwap_entry(self, clf):
        result = clf.classify("Price just reclaimed VWAP with a breakout candle, entry looks good")
        assert result.tier == TaskTier.LOCAL_MID


class TestPremarketRouting:
    def test_premarket_keyword(self, clf):
        result = clf.classify("Give me a pre-market brief for SPY based on overnight futures")
        assert result.tier == TaskTier.LOCAL_MID
        assert result.use_case == "premarket_brief"

    def test_morning_brief(self, clf):
        result = clf.classify("What's the morning brief? What happened yesterday in the market?")
        assert result.tier == TaskTier.LOCAL_MID


class TestJournalRouting:
    def test_eod_recap(self, clf):
        result = clf.classify("Here are my trades for the day, write an end of day recap")
        assert result.tier == TaskTier.LOCAL_FAST
        assert result.use_case == "trade_journal"

    def test_pnl_summary(self, clf):
        result = clf.classify("Summarise my P&L and win rate from today's session")
        assert result.tier == TaskTier.LOCAL_FAST


class TestTokenLengthFallback:
    def test_very_long_unclassified_goes_to_haiku(self, clf):
        # Need >1200 estimated tokens: 1200 / 1.35 ≈ 889 words minimum
        # Use 950 words of neutral filler that won't trigger any keyword
        long_prompt = "lorem ipsum dolor sit amet consectetur adipiscing elit " * 170
        result = clf.classify(long_prompt)
        assert result.tier == TaskTier.CLOUD_HAIKU

    def test_short_unclassified_goes_to_fast(self, clf):
        result = clf.classify("hello there")
        assert result.tier == TaskTier.LOCAL_FAST

    def test_medium_unclassified_goes_to_mid(self, clf):
        # Need 600-1200 estimated tokens: 600/1.35 ≈ 445 words; 1200/1.35 ≈ 889 words
        # Use ~500 words of neutral filler
        medium_prompt = "lorem ipsum dolor sit amet consectetur adipiscing elit " * 90
        result = clf.classify(medium_prompt)
        assert result.tier == TaskTier.LOCAL_MID

from dataclasses import dataclass
from openclaw.config import settings

_MODEL  = settings.local_model   # hermes3 (or whatever LOCAL_MODEL is set to)
_BACK   = "ollama"

@dataclass
class RouteDecision:
    task_type: str
    model:     str
    backend:   str
    reason:    str

# ── Keyword sets (first match wins, ordered by priority) ────────────────────

_CODE_KEYWORDS = {
    "write a ","write the ","how to ","how do i","debug","fix the bug","fix this",
    "implement","function","class ","script","refactor","unit test","sql","endpoint",
    "dockerfile","regex","algorithm","syntax error","traceback","import ","def ","async ",
    "pip install","error in my code","code review","what does this code",
}

_TRADING_KEYWORDS = {
    "should i trade","should i enter","should i buy","should i sell","should i short",
    "should i long","is this a good trade","apex","tradovate","funded account","prop firm",
    "risk management","position size","drawdown","daily loss","trailing drawdown",
    "portfolio","capital allocation","market outlook","what do you recommend",
    "trading plan","trade setup","my account","pnl","profit and loss",
    "strategy","give me a strategy","buy price","entry price","stop loss","target",
    "current price","what's the price","price of","price target","tp1","tp2","sl1","sl2",
    "bullish","bearish","chart","technical analysis","swing trade","day trade",
}

_SIGNAL_KEYWORDS = {
    "rsi","macd","ema","vwap","entry","stop loss","take profit","confluence",
    "breakout","rejection","support","resistance","long ","short ","iv rank",
    "tqqq","soxl","tsll","mnq","luxalgo","signal","candlestick","divergence",
    "oversold","overbought","trend","momentum","volume spike",
}

_RESEARCH_KEYWORDS = {
    "explain","what is","what are","how does","tell me about","research",
    "overview","difference between","compare","pros and cons","history of",
    "why does","define","who is","what happened","news about","latest on",
    "summarize this","summarize the","give me info",
}

_WRITING_KEYWORDS = {
    "write an email","write a email","draft","write a letter","blog post",
    "write a post","write a message","write a report","compose","write content",
    "write an article","proofread","rewrite","rephrase","write a bio",
    "write a description","tweet","linkedin","subject line","write a proposal",
}

_PLANNING_KEYWORDS = {
    "plan my","my schedule","my goals","priorities","this week","today's tasks",
    "what should i focus","make a plan","action plan","set goals","roadmap",
    "organize my","weekly plan","daily plan","task list","to-do","to do list",
    "help me plan","break this down","step by step plan",
}

_JOURNAL_KEYWORDS = {
    "journal","trade log","daily pnl","win rate","performance","session recap",
    "how did i do","statistics","stats","recap","today's trades","my trades",
    "summarize my session","track my","review my",
}


def classify(prompt: str) -> RouteDecision:
    p = prompt.lower()

    # Code goes to LM Studio (Devstral) if available, else hermes3
    if _any(p, _CODE_KEYWORDS):
        return RouteDecision("code", "devstral-small-2-24b-instruct-2512", "lmstudio", f"Code -> Devstral (LM Studio)")

    # All other tasks → hermes3 via Ollama, Claude Haiku fallback
    if _any(p, _TRADING_KEYWORDS):
        return RouteDecision("trading",  _MODEL, _BACK, f"Trading -> {_MODEL}")
    if _any(p, _SIGNAL_KEYWORDS):
        return RouteDecision("signal",   _MODEL, _BACK, f"Signal -> {_MODEL}")
    if _any(p, _RESEARCH_KEYWORDS):
        return RouteDecision("research", _MODEL, _BACK, f"Research -> {_MODEL}")
    if _any(p, _WRITING_KEYWORDS):
        return RouteDecision("writing",  _MODEL, _BACK, f"Writing -> {_MODEL}")
    if _any(p, _PLANNING_KEYWORDS):
        return RouteDecision("planning", _MODEL, _BACK, f"Planning -> {_MODEL}")
    if _any(p, _JOURNAL_KEYWORDS):
        return RouteDecision("journal",  _MODEL, _BACK, f"Journal -> {_MODEL}")
    if len(prompt.split()) > 400:
        return RouteDecision("long_context", _MODEL, _BACK, f"Long -> {_MODEL}")

    return RouteDecision("general", _MODEL, _BACK, f"General -> {_MODEL}")


def _any(text: str, keywords: set) -> bool:
    return any(kw in text for kw in keywords)

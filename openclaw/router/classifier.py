from dataclasses import dataclass

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

    if _any(p, _CODE_KEYWORDS):
        return RouteDecision("code",     "devstral-small-2-24b-instruct-2512", "lmstudio", "Code -> Devstral 24B")
    if _any(p, _TRADING_KEYWORDS):
        return RouteDecision("trading",  "nemotron-3-nano:30b", "ollama", "Trading -> Nemotron 30B")
    if _any(p, _SIGNAL_KEYWORDS):
        return RouteDecision("signal",   "nemotron-3-nano:30b", "ollama", "Signal -> Nemotron 30B")
    if _any(p, _RESEARCH_KEYWORDS):
        return RouteDecision("research", "nemotron-3-nano:30b", "ollama", "Research -> Nemotron 30B")
    if _any(p, _WRITING_KEYWORDS):
        return RouteDecision("writing",  "gpt-oss:20b", "ollama", "Writing -> GPT-OSS 20B")
    if _any(p, _PLANNING_KEYWORDS):
        return RouteDecision("planning", "gpt-oss:20b", "ollama", "Planning -> GPT-OSS 20B")
    if _any(p, _JOURNAL_KEYWORDS):
        return RouteDecision("journal",  "gpt-oss:20b", "ollama", "Journal -> GPT-OSS 20B")
    if len(prompt.split()) > 400:
        return RouteDecision("long_context", "nemotron-3-nano:30b", "ollama", "Long -> Nemotron 30B")

    return RouteDecision("general", "gpt-oss:20b", "ollama", "General -> GPT-OSS 20B")


def _any(text: str, keywords: set) -> bool:
    return any(kw in text for kw in keywords)

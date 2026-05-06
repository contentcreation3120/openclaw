from dataclasses import dataclass

@dataclass
class RouteDecision:
    task_type: str
    model:     str
    backend:   str
    reason:    str

_CODE_KEYWORDS = {"write code","write a ","debug","fix the bug","implement","function","class ","script","refactor","unit test","sql query","api endpoint","endpoint","dockerfile","regex","algorithm","syntax error","traceback","import ","def ","async ","how do i","how to"}
_STRATEGY_KEYWORDS = {"should i trade","should i enter","is this a good trade","risk management","position size","portfolio","drawdown","strategy decision","market outlook","what do you recommend","should i buy","should i sell","is it safe","capital allocation","funded account","apex rule","prop firm"}
_SIGNAL_KEYWORDS = {"signal","mnq","tqqq","soxl","tsll","entry","stop loss","take profit","confluence","luxalgo","breakout","rejection","candlestick","rsi","macd","ema","vwap","support","resistance","long ","short "}
_JOURNAL_KEYWORDS = {"summarize","summary","recap","today's trades","session recap","how did i do","win rate","trade log","daily pnl","journal","performance","statistics","stats"}

def classify(prompt: str) -> RouteDecision:
    p = prompt.lower()
    if _any_match(p, _CODE_KEYWORDS):
        return RouteDecision("code","devstral-small-2-24b-instruct-2512","lmstudio","Code task -> Devstral 24B")
    if _any_match(p, _STRATEGY_KEYWORDS):
        return RouteDecision("strategy","claude-sonnet-4-6","claude","High-stakes decision -> Claude Sonnet")
    if _any_match(p, _SIGNAL_KEYWORDS):
        return RouteDecision("signal","nemotron-3-nano:30b","ollama","Signal analysis -> Nemotron 30B")
    if _any_match(p, _JOURNAL_KEYWORDS):
        return RouteDecision("journal","gpt-oss:20b","ollama","Trade journal -> GPT-OSS 20B")
    if len(prompt.split()) > 400:
        return RouteDecision("long_context","nemotron-3-nano:30b","ollama","Long prompt -> Nemotron 30B")
    return RouteDecision("general","gpt-oss:20b","ollama","General/short -> GPT-OSS 20B (default)")

def _any_match(text: str, keywords: set) -> bool:
    return any(kw in text for kw in keywords)

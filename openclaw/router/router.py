from loguru import logger
from openclaw.router.classifier import classify, RouteDecision
from openclaw.tasks.prompts import get_prompt
from openclaw.market_data import build_market_context, extract_tickers, is_futures
from openclaw.cost_tracker import CostTracker

tracker = CostTracker()

_STRATEGY_WORDS = {"strategy","setup","trade","entry","stop","target","position","swing","intraday","day trade","day trading","swing trade","swing trading"}


def route(prompt: str, system: str = "", max_tokens: int = 1536, task_type: str = None) -> str:
    decision = classify(prompt)
    if task_type:
        decision.task_type = task_type   # caller override (e.g. auto_analysis)
    logger.info(f"Route: [{decision.task_type}] -> {decision.model} | {decision.reason}")

    # For trading prompts: detect futures vs stocks and refine task_type
    if decision.task_type in ("trading", "signal"):
        tickers = extract_tickers(prompt)
        p_lower = prompt.lower()
        has_strategy_word = any(w in p_lower for w in _STRATEGY_WORDS)

        if tickers and has_strategy_word:
            futures_tickers = [t for t in tickers if is_futures(t)]
            stock_tickers   = [t for t in tickers if not is_futures(t)]

            if futures_tickers and not stock_tickers:
                decision.task_type = "trading_futures"
                logger.info(f"Futures detected: {futures_tickers} -> day trading mode")
            elif stock_tickers and not futures_tickers:
                decision.task_type = "trading_stocks"
                logger.info(f"Stock detected: {stock_tickers} -> swing trading mode")
            # mixed or unclear: keep original task_type, model will ask

    # Inject live market data (pass task_type so research gets fundamentals + news)
    market_ctx = build_market_context(prompt, decision.task_type)
    if market_ctx:
        enriched_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT — Use only these real prices, do not estimate:\n"
            f"{market_ctx}"
        )
        logger.info("Market data injected")
    else:
        enriched_prompt = prompt

    sys_prompt = system or get_prompt(decision.task_type)
    response = _dispatch(enriched_prompt, sys_prompt, max_tokens, decision)
    tracker.record(decision)
    return response


def explain(prompt: str) -> RouteDecision:
    return classify(prompt)


def _dispatch(prompt, system, max_tokens, decision):
    from openclaw.backends import ollama_backend, lmstudio_backend, cloud_backend
    if decision.backend == "ollama":
        if ollama_backend.is_available():
            try:
                return ollama_backend.complete(prompt, decision.model, system, max_tokens)
            except RuntimeError as e:
                logger.warning(f"Ollama failed: {e} -- fallback Haiku")
        else:
            logger.warning("Ollama offline -- fallback Haiku")
        return cloud_backend.complete(prompt, cloud_backend.HAIKU, system, max_tokens)

    if decision.backend == "lmstudio":
        if lmstudio_backend.is_available():
            try:
                return lmstudio_backend.complete(prompt, decision.model, system, max_tokens)
            except RuntimeError as e:
                logger.warning(f"LM Studio failed: {e} -- fallback Haiku")
        else:
            logger.warning("LM Studio offline -- fallback Haiku")
        return cloud_backend.complete(prompt, cloud_backend.HAIKU, system, max_tokens)

    return cloud_backend.complete(prompt, decision.model, system, max_tokens)

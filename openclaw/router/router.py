from loguru import logger
from openclaw.router.classifier import classify, RouteDecision
from openclaw.cost_tracker import CostTracker

tracker = CostTracker()

def route(prompt: str, system: str = "", max_tokens: int = 1024) -> str:
    decision = classify(prompt)
    logger.info(f"Route: [{decision.task_type}] -> {decision.model} | {decision.reason}")
    response = _dispatch(prompt, system, max_tokens, decision)
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

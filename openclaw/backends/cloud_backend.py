import anthropic
from loguru import logger
from openclaw.config import settings

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
SONNET = "claude-sonnet-4-6"
HAIKU  = "claude-haiku-4-5-20251001"

def complete(prompt: str, model: str = SONNET, system: str = "", max_tokens: int = 1024) -> str:
    messages = [{"role": "user", "content": prompt}]
    kwargs = dict(model=model, max_tokens=max_tokens, messages=messages)
    if system:
        kwargs["system"] = system
    try:
        r = _client.messages.create(**kwargs)
        u = r.usage
        logger.info(f"Claude {model} | in={u.input_tokens} out={u.output_tokens}")
        return r.content[0].text
    except Exception as e:
        raise RuntimeError(f"Claude ({model}): {e}") from e

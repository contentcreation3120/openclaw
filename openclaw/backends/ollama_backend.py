from openai import OpenAI
from loguru import logger

_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

def complete(prompt: str, model: str, system: str = "", max_tokens: int = 1024) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        r = _client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=0.3)
        return r.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"Ollama ({model}): {e}") from e

def is_available() -> bool:
    try:
        _client.models.list()
        return True
    except Exception:
        return False

def list_models() -> list:
    try:
        return [m.id for m in _client.models.list().data]
    except Exception:
        return []

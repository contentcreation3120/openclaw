from openai import OpenAI

_client = OpenAI(base_url="http://localhost:1234/v1", api_key="lmstudio")

def complete(prompt: str, model: str, system: str = "", max_tokens: int = 2048) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        r = _client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=0.1)
        return r.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"LM Studio ({model}): {e}") from e

def is_available() -> bool:
    try:
        _client.models.list()
        return True
    except Exception:
        return False

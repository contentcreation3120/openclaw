import subprocess, time, os, threading
from pathlib import Path
from loguru import logger

OLLAMA_EXE   = Path(os.environ.get("LOCALAPPDATA","")) / "Programs" / "Ollama" / "ollama.exe"
LMSTUDIO_EXE = Path(os.environ.get("LOCALAPPDATA","")) / "Programs" / "LM-Studio" / "LM Studio.exe"

def start_all() -> dict:
    return {"ollama": start_ollama(), "lmstudio": start_lmstudio()}

def stop_all() -> dict:
    return {"ollama": _kill("ollama"), "lmstudio": _kill("LM Studio")}

def start_ollama() -> str:
    if _is_running("ollama"): return "already_running"
    if not OLLAMA_EXE.exists(): return "not_found"
    subprocess.Popen([str(OLLAMA_EXE), "serve"], creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(2); logger.success("Ollama started"); return "started"

def start_lmstudio() -> str:
    if _is_running("LM Studio"): return "already_running"
    if not LMSTUDIO_EXE.exists(): return "not_found"
    subprocess.Popen([str(LMSTUDIO_EXE)], creationflags=subprocess.CREATE_NO_WINDOW)
    time.sleep(3); logger.success("LM Studio started"); return "started"

def status() -> dict:
    from openclaw.backends import ollama_backend, lmstudio_backend
    return {
        "ollama":   "online" if ollama_backend.is_available() else "offline",
        "lmstudio": "online" if lmstudio_backend.is_available() else "offline",
    }

def _kill(name: str) -> str:
    import psutil
    killed = 0
    for p in psutil.process_iter(["name"]):
        if name.lower() in p.info["name"].lower():
            try: p.kill(); killed += 1
            except: pass
    return f"stopped ({killed})" if killed else "was_not_running"

def _is_running(name: str) -> bool:
    import psutil
    return any(name.lower() in p.name().lower() for p in psutil.process_iter(["name"]))


def list_ollama_models() -> list[str]:
    """Return list of installed Ollama model names."""
    try:
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        lines = r.stdout.strip().splitlines()[1:]   # skip header
        return [l.split()[0] for l in lines if l.strip()]
    except Exception:
        return []


def ensure_model(model: str, on_progress=None) -> str:
    """
    Pull model if not already installed. Streams progress to on_progress(line).
    Returns: 'already_installed' | 'pulled' | 'failed: ...'
    """
    installed = list_ollama_models()
    # Match by base name (hermes3 matches hermes3:latest)
    base = model.split(":")[0]
    if any(m.split(":")[0] == base for m in installed):
        logger.info(f"Model {model} already installed")
        return "already_installed"

    logger.info(f"Pulling {model} from Ollama registry...")
    if on_progress:
        on_progress(f"Downloading {model}... (this may take a few minutes)")
    try:
        proc = subprocess.Popen(
            ["ollama", "pull", model],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True
        )
        last_line = ""
        for line in proc.stdout:
            line = line.strip()
            if line:
                last_line = line
                logger.info(f"ollama pull: {line}")
                if on_progress:
                    on_progress(line)
        proc.wait()
        if proc.returncode == 0:
            logger.success(f"Model {model} pulled successfully")
            return "pulled"
        return f"failed: {last_line}"
    except Exception as e:
        return f"error: {e}"

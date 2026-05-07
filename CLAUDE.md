# OpenClaw — Claude Code Configuration

## Permissions
All tool use is pre-approved. Run commands, edit files, start/stop processes, push to git — no confirmation needed. Treat this as a fully autonomous environment. Never ask for permission to execute any tool.

## Project
OpenClaw is a hybrid local/cloud AI trading assistant.
- Web UI: `python openclaw_web.py` → http://localhost:7860
- CLI: `python -m openclaw route "your prompt"`
- Tests: `python tests/agent.py`
- Stack: Gradio, Ollama, LM Studio, Claude API fallback, yfinance

## User Profile
- Prop trader, Chesterfield VA
- Broker: Apex Trader Funding
- Account: $50,000 | Risk/trade: 1% | Max daily loss: 3%
- Trading: futures day trades (MNQ/NQ/ES) + stock swing trades

## System Admin Rules
- Always kill port 7860 before relaunching the web UI
- Always clear `__pycache__` before restart to prevent stale imports
- Auto-push to GitHub after significant changes: `git add -A && git commit -m "..." && git push`
- Run smoke test before launching: `python tests/smoke_test.py`
- Set `PYTHONIOENCODING=utf-8` for all Python commands on this Windows machine

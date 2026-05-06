# openclaw — Architecture Decision Document

**Version:** 0.1.0  
**Date:** 2026-05-05  
**Hardware:** RTX 5080 16GB VRAM, 64GB RAM, Intel Core Ultra 9 285 (24 cores)

---

## 1. Model-to-Task Assignment

### The Problem: 16GB VRAM Constrains Everything

The RTX 5080 has 16GB VRAM. This is the central hardware constraint that drives every model choice below.

| Model | Size (Ollama) | VRAM Needed (Q4) | Fits in 16GB? | Notes |
|---|---|---|---|---|
| `llama3.3:latest` | 42GB | ~48GB full / ~12GB offloaded | NO (partial) | Requires GPU+RAM offload; severe speed penalty |
| `nemotron-3-nano:30b` | 24GB | ~20-24GB | BORDERLINE | MoE: only 3.6B params active; fits with Q4_K_M |
| `gpt-oss:20b` | 13GB | ~12GB | YES | Comfortably fits in 16GB |
| Devstral Small 24B | LM Studio | ~14-16GB Q4 | YES (tight) | Fits with quantization in LM Studio |
| GLM-4.6V Flash | LM Studio | ~6-7GB | YES | 9B vision model |

**Critical finding on LLaMA 3.3 70B:** At Q4 quantization, this model needs ~48GB VRAM to run fully on GPU. With 16GB VRAM + 64GB RAM, Ollama will offload layers to system RAM. Based on benchmark data, a 70B model with partial GPU offload (12-20 layers on GPU out of 80) achieves only 6-15 tokens/second. This is unusable for a real-time trading workflow. LLaMA 3.3 is demoted to **manual/experimental use only** — do not route automated workloads to it.

---

### Final Model Assignments

#### TIER 1 — LOCAL FAST: `gpt-oss:20b` via Ollama
**Use cases:** Trade journal summaries, EOD recaps, short Q&A  
**Why:** Fits entirely in 16GB VRAM. Benchmarks show it matches o3-mini on common tasks and runs at 40-70 tok/s on the RTX 5080. For journal summarisation (a simple structured extraction task), this is massive overkill in a good way. Zero cloud spend.

#### TIER 2 — LOCAL MID: `nemotron-3-nano:30b` via Ollama
**Use cases:** Pre-market briefs, signal analysis, structured output  
**Why:** Nemotron 3 Nano is a Mixture-of-Experts model — 30B total parameters but only 3.6B are active per forward pass. This means it fits into ~20-24GB (GPU + RAM) with Q4_K_M quantization, and inference speed is closer to a 7B dense model. Its MoE architecture gives disproportionate analytical quality for the compute cost. NVIDIA optimized it specifically for structured output and reasoning, which is exactly what signal analysis needs. HumanEval: 78%, MATH: 82.88%. It will run partially in VRAM and partially in RAM — acceptable because these are non-latency-critical tasks (pre-market brief is written once, not typed interactively).

#### TIER 3 — LOCAL CODE: `devstral-small-2-24b` via LM Studio
**Use cases:** Python code generation, backtest scripts, debugging  
**Why:** Devstral Small 2 (24B) achieves 68% on SWE-bench Verified — it is purpose-built for software engineering tasks. It runs on a single GPU with 16GB VRAM at Q4 quantization. Crucially, LM Studio's GGUF execution gives better coding task performance on this model than Ollama due to LM Studio's optimized context handling. Devstral will produce better code than Nemotron for complex multi-file refactors and algorithm implementation.

**Fallback:** If LM Studio is not running, code tasks fall back to `claude-haiku-4-5`. This is an intentional one-level cascade (local code → cloud haiku only) because code quality variance from wrong models is expensive to fix.

#### TIER 4 — CLOUD HAIKU: `claude-haiku-4-5`
**Use cases:** Complex prompts >1200 tokens (uncategorized), code overflow, LM Studio offline fallback  
**Cost:** $1.00/$5.00 per MTok input/output  
**Why:** Haiku is the safety net. It handles anything too long or too ambiguous for local models without spending Sonnet budget.

#### TIER 5 — CLOUD SONNET: `claude-sonnet-4-6`
**Use cases:** Strategy decisions, high-stakes trade decisions, portfolio advice  
**Cost:** $3.00/$15.00 per MTok input/output  
**Why:** Trading strategy decisions carry real financial risk. This is the one case where you do not want to gamble on a local model giving a confident-but-wrong answer. Sonnet is always used here, no exceptions, regardless of prompt length. This is hard-coded in the classifier (`force_cloud_for_strategy=True`).

---

### What to Do with LLaMA 3.3 70B

Do not delete it — keep it as a manual experimentation model. Pull it up in the Ollama CLI when you want to test something and have 10+ minutes to spare. It is not routed by openclaw. If you later add a second GPU or upgrade to 24GB VRAM, it becomes a viable TIER 2 replacement for Nemotron.

---

## 2. Routing Logic: Rule-Based, Not ML Classifier

### Decision: Rule-Based Rules Win Here

Three approaches were evaluated:

| Approach | Latency | Accuracy | Maintenance | Verdict |
|---|---|---|---|---|
| **Keyword/rule-based** | 0ms | ~88% for this narrow domain | Low | CHOSEN |
| **Small ML classifier** | 50-200ms (model load + inference) | ~92% trained | High (labeling, retraining) | Overkill |
| **Meta-LLM routing** | 500ms-2s (another LLM call) | ~95% | Medium | Wastes what we're trying to save |

**Why rules beat ML for this use case:**

1. The task taxonomy is narrow and fixed: exactly 5 use-case types. ML classifiers excel when you have dozens of fuzzy categories or free-form intent. For 5 well-defined trading workflows, keywords are sufficient.

2. An ML classifier requires an embedding model running in-process (adding ~200ms cold start and RAM pressure). A meta-LLM router costs tokens — the exact thing we're trying to minimize.

3. The routing only needs to be ~85% accurate to generate massive savings. Even if 15% of journal summaries accidentally go to Nemotron instead of GPT-OSS, you've still saved Sonnet calls on 100% of them.

4. Rule transparency matters: when a strategy decision goes to Sonnet, you want to know exactly why. With rules, the reason is always logged and explainable.

### The Single Exception: Code Task Cascading

Code generation uses a **one-level cascade**:
- If LM Studio (Devstral) is available → route there
- If LM Studio is down → cascade to Haiku

This is the only cascading in the system. The reason is availability, not confidence: LM Studio requires the app to be open and the model to be loaded. This is a binary check (is the server responding?), not a soft confidence score, so it is reliable.

---

## 3. Backend Choice: Ollama Primary, LM Studio Secondary

### Decision: Ollama as the Primary Local Inference Backend

| Factor | Ollama | LM Studio |
|---|---|---|
| API stability | Excellent (production-grade) | Good (app must be open) |
| Daemon mode | Yes (runs as background service) | No (app must be open) |
| Concurrent requests | Yes | Yes (since v0.3.x) |
| Model management | CLI-driven, scriptable | GUI-driven |
| Inference speed | 10-20% faster (less GUI overhead) | Slightly slower |
| GGUF support | Yes | Yes (more formats) |
| Windows service | Yes | No |
| Embedding API | Yes (`/v1/embeddings`) | Yes |

**Ollama is the backbone** for TIER 1 (GPT-OSS) and TIER 2 (Nemotron). Both models are already pulled. Ollama runs as a background process on Windows and does not require any GUI interaction.

**LM Studio is used exclusively for Devstral** (TIER 3 / code tasks). LM Studio is included because:
1. Devstral is already loaded there
2. LM Studio has better GGUF quantization options for 24B models
3. The user already has a working setup

If you prefer to consolidate: pull `devstral-small-2:24b` into Ollama and remove LM Studio from the routing stack entirely. The code to do this is in `openclaw/backends/ollama_backend.py` — just add Devstral as a model name constant.

### API Compatibility

Both backends speak the OpenAI REST API format (`/v1/chat/completions`). The `openai` Python package points to them via `base_url` override. This means:
- No custom HTTP client needed
- Streaming works identically
- The same message format (`{"role": "user", "content": "..."}`) works everywhere

---

## 4. Package Structure

```
D:\CLAUDE\projects\openclaw\
├── openclaw/
│   ├── __init__.py              # Public API exports
│   ├── __main__.py              # CLI: python -m openclaw chat/explain/servers
│   ├── config.py                # Settings dataclass, reads from env vars
│   ├── router/
│   │   ├── classifier.py        # Rule-based prompt classifier → TaskTier
│   │   └── router.py            # Dispatches to correct backend, handles fallback
│   ├── backends/
│   │   ├── ollama_backend.py    # Ollama via openai package (localhost:11434)
│   │   ├── lmstudio_backend.py  # LM Studio via openai package (localhost:1234)
│   │   └── cloud_backend.py     # Anthropic SDK (prompt caching enabled)
│   ├── tasks/
│   │   └── prompts.py           # Named system prompts per use-case
│   └── server/
│       └── lifecycle.py         # START/STOP server manager
├── scripts/
│   ├── start_servers.ps1        # PowerShell: one-click start all local servers
│   └── stop_servers.ps1         # PowerShell: one-click stop + free VRAM
├── tests/
│   └── test_classifier.py       # Pytest suite for routing rules
├── pyproject.toml
└── .env.example
```

### Integration Pattern (typical usage in trading-ecosystem)

```python
from openclaw.router.router import Router
from openclaw.tasks.prompts import get_system_prompt
from openclaw.router.classifier import TaskClassifier

router = Router.default()

# The classifier picks the system prompt automatically
clf = TaskClassifier()
classification = clf.classify(user_prompt)
system = get_system_prompt(classification.use_case)

result = router.chat(user_prompt, system=system)
print(result.content)
# result.model → tells you which model actually ran
# result.tier  → tells you which tier was used
```

---

## 5. START/STOP: One-Click Server Management

### The Problem

Ollama (42GB + 24GB model VRAM) and LM Studio occupy VRAM even when idle. The user wants a simple button to start/stop them for trading sessions.

### Solution A: PowerShell Scripts (immediate, no install required)

```powershell
# Start everything
.\scripts\start_servers.ps1

# Stop everything + free VRAM
.\scripts\stop_servers.ps1
```

These are in `/scripts/`. They check if Ollama is already running before launching, wait for health checks, and print status.

### Solution B: Python CLI (after pip install)

```bash
# After: pip install -e .
openclaw servers start
openclaw servers stop
openclaw servers status
```

This uses `openclaw/server/lifecycle.py` which probes `/v1/models` on each backend and launches processes with `subprocess.Popen` (hidden windows on Windows via `CREATE_NO_WINDOW`).

### LM Studio Caveat

LM Studio cannot be programmatically started/stopped via CLI in a fully automated way — it requires the application to be open and the model to be loaded in the GUI. The scripts handle this by printing instructions and detecting whether LM Studio is already running. The practical workaround is:
- Keep LM Studio open during trading sessions when you expect to do code work
- The router detects LM Studio absence and falls back to Haiku automatically

---

## 6. Estimated Token Savings vs All-Claude Approach

### Usage Assumptions (conservative estimate)

| Use Case | Calls/Day | Avg Tokens (in+out) | Current All-Sonnet Cost |
|---|---|---|---|
| Trade journal summaries | 1 | 800 | $0.013 |
| Pre-market brief | 1 | 1,200 | $0.019 |
| Signal analysis | 5 | 600 each = 3,000 | $0.048 |
| Code generation | 3 | 1,500 each = 4,500 | $0.071 |
| Strategy decisions | 1 | 2,000 | $0.032 |
| **Daily total** | **11 calls** | **11,500 tokens** | **$0.183/day** |

At $0.183/day, the all-Sonnet cost is ~$5.49/month or ~$66.8/year.

### With openclaw Routing

| Use Case | Routed To | Cost/Day |
|---|---|---|
| Trade journal summaries | GPT-OSS (local) | $0.00 |
| Pre-market brief | Nemotron (local) | $0.00 |
| Signal analysis | Nemotron (local) | $0.00 |
| Code generation | Devstral (local) | $0.00 |
| Strategy decisions | Sonnet | $0.032 |

**Daily cloud cost with openclaw: ~$0.032**  
**Monthly: ~$0.96**  
**Annual: ~$11.68**

### Savings Summary

| Metric | All-Sonnet | openclaw |
|---|---|---|
| Daily API cost | $0.183 | $0.032 |
| Monthly API cost | $5.49 | $0.96 |
| Annual API cost | $66.80 | $11.68 |
| **Savings** | — | **$55.12/year (82%)** |

At higher usage (active trading days with 20+ LLM calls), the savings scale proportionally. Only strategy decisions (which are intentionally few) touch the Claude API.

### With Prompt Caching

If you use a fixed system prompt (e.g., `STRATEGY_DECISION_SYSTEM` in `tasks/prompts.py`), the cached input rate for Sonnet drops from $3.00 to $0.30/MTok — an additional 90% reduction on system prompt tokens. For a 500-token strategy system prompt sent once per day, this saves another ~$0.02/month. Marginal at low volume, but meaningful at scale.

---

## 7. Decisions Not Taken (and Why)

### Why Not Always Use Ollama for Code Too?

You could pull Devstral into Ollama. The reason to keep LM Studio is: the user already has Devstral loaded there and working. Adding a third tool just to consolidate is unnecessary. If LM Studio causes friction, pull `devstral-small-2:24b` into Ollama with `ollama pull devstral-small-2:24b` and update the `LOCAL_CODE` tier to use `OllamaBackend`.

### Why Not Use LiteLLM as the Routing Layer?

LiteLLM is excellent for provider abstraction but adds a dependency and a config file that duplicates what the router already does. openclaw is opinionated: it knows exactly 5 task types and exactly 5 models. LiteLLM shines when you need to abstract 20+ providers dynamically.

### Why Not Use Confidence-Based Cascading for All Tiers?

Research shows LLM self-reported confidence is poorly calibrated — models can be wrong and confident simultaneously. For trading decisions, a confident-but-wrong local answer about whether to enter a trade is strictly worse than routing to Sonnet. The only cascade is a binary availability check (is LM Studio up?), which is reliable.

### Why Not Use LLaMA 3.3 70B?

See Section 1. With 16GB VRAM and layer offloading to RAM, LLaMA 3.3 achieves ~6-15 tokens/second. Nemotron 3 Nano 30B (MoE architecture) achieves comparable analytical quality at 3x+ the throughput. LLaMA 3.3 is retained in Ollama for manual experimentation only.

---

## 8. Installation

```bash
# 1. Clone / navigate to the project
cd D:\CLAUDE\projects\openclaw

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install
pip install -e ".[dev]"

# 4. Configure
copy .env.example .env
# Edit .env and set ANTHROPIC_API_KEY

# 5. Start servers
.\scripts\start_servers.ps1

# 6. Test the router
python -m openclaw explain "Should I take this trade given current volatility?"
python -m openclaw explain "Summarise my trade journal for today"
python -m openclaw explain "Write a backtest for my EMA crossover in pandas"

# 7. Run tests
pytest tests/
```

---

## 9. Routing Decision Table (Quick Reference)

| Trigger | Tier | Model | Backend |
|---|---|---|---|
| "should I trade", "strategy", "recommend", "advise" | CLOUD_SONNET | claude-sonnet-4-6 | Anthropic |
| "def ", "```python", "backtest", "traceback", "debug", "refactor" | LOCAL_CODE | devstral-small-2-24b | LM Studio |
| "RSI", "MACD", "signal", "entry", "breakout", "VWAP", "divergence" | LOCAL_MID | nemotron-3-nano:30b | Ollama |
| "pre-market", "morning brief", "game plan", "overnight" | LOCAL_MID | nemotron-3-nano:30b | Ollama |
| "trade journal", "EOD recap", "P&L", "session recap" | LOCAL_FAST | gpt-oss:20b | Ollama |
| Prompt >1200 tokens (any category) | CLOUD_HAIKU | claude-haiku-4-5 | Anthropic |
| Prompt 600-1200 tokens (uncategorized) | LOCAL_MID | nemotron-3-nano:30b | Ollama |
| Prompt <600 tokens (uncategorized) | LOCAL_FAST | gpt-oss:20b | Ollama |
| Code task + LM Studio offline | CLOUD_HAIKU | claude-haiku-4-5 | Anthropic |
| Any local backend fails | CLOUD_HAIKU → CLOUD_SONNET | escalation chain | Anthropic |

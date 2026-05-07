"""
OpenClaw Web UI
Launch: python openclaw_web.py  |  Opens at http://localhost:7860
"""
import sys
import os
import re
import socket

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from openclaw.router.router import route as openclaw_route
from openclaw.router.classifier import classify
from openclaw.market_data import extract_tickers, is_futures, fetch_quote
from openclaw.server.lifecycle import start_all, status as server_status

import gradio as gr

# ── Auto-start local servers on launch ───────────────────────────────────────
print("\n  OpenClaw — starting local AI servers...")
_srv = start_all()
print(f"  Ollama   : {_srv['ollama']}")
print(f"  LM Studio: {_srv['lmstudio']}")

_DEEP_TASKS = {"trading","trading_futures","trading_stocks","trading_day","signal","research","auto_analysis","options"}
_FOLLOWUPS  = {"yes","ok","sure","go ahead","continue","please","do it","yep","yeah","correct","exactly","proceed"}
_STRATEGY_WORDS = {
    "strategy","setup","trade","entry","stop","target","position",
    "swing","intraday","day trade","day trading","price","chart",
    "signal","buy","sell","long","short","options","option",
    "research","explain","what is","analyze","analysis",
}


def get_status() -> str:
    s = server_status()
    return (
        f"Ollama: {s.get('ollama','offline').upper()}  |  "
        f"LM Studio: {s.get('lmstudio','offline').upper()}  |  "
        "Claude API: ONLINE (fallback)"
    )


def chat(message: str, history: list) -> str:
    if not message.strip():
        return ""

    msg_clean = message.strip().lower().rstrip("!.?")
    enriched  = message

    # ── Short follow-up (yes/ok/sure) → inject context from last exchange ────
    words = message.strip().split()
    if len(words) <= 3 and msg_clean in _FOLLOWUPS and history:
        last_user = history[-1][0] or ""
        last_ai   = history[-1][1] or ""
        last_clean = "\n".join(l for l in last_ai.splitlines() if not l.startswith(">"))
        enriched = (
            f"[Context from previous exchange]\n"
            f"User asked: {last_user}\n"
            f"You replied: {last_clean[:600]}\n\n"
            f"User follow-up: {message}\n"
            f"Continue from where you left off."
        )

    # ── Drill-down shortcuts: "swing MSTR" / "day MNQ" / "options AAPL" ─────
    drill = re.match(
        r'^(swing|day|options?|research)\s+([A-Za-z]{1,5})$',
        message.strip(), re.IGNORECASE
    )
    if drill:
        action = drill.group(1).lower()
        sym    = drill.group(2).upper()
        if action == "swing":
            enriched = f"swing trade setup for {sym} — entry zone, SL1, SL2, TP1, TP2, position size"
        elif action == "day":
            enriched = f"day trade {sym} intraday — entry, SL1, SL2, TP1, TP2, exit rule before close"
        elif action in ("option", "options"):
            enriched = f"options strategy for {sym} — best structure, strikes, expiry, IV rank context"
        elif action == "research":
            enriched = f"research {sym} — full fundamental analysis, catalysts, bull case, bear case, verdict"

    # ── Auto-route: bare ticker with no action words ──────────────────────────
    if not drill:
        p_lower  = enriched.lower()
        tickers  = extract_tickers(enriched)
        has_act  = any(w in p_lower for w in _STRATEGY_WORDS)

        if tickers and not has_act:
            sym = tickers[0]
            if is_futures(sym):
                # Futures = always day trade with Apex — no menu needed
                enriched = f"day trade {sym} futures — Apex-compliant entry, SL1, SL2, TP1, TP2, contracts"
            else:
                # Stock bare ticker → full auto-analysis in one shot
                enriched = f"auto analysis {sym}"

    # ── Classify and route ────────────────────────────────────────────────────
    decision = classify(enriched)
    header   = f"> **[{decision.task_type}]** routed to `{decision.model}` ({decision.backend})\n\n"

    try:
        response = openclaw_route(enriched)
        if not response:
            return header + "> *(model returned empty — Ollama may still be loading, try again)*"

        result = header + response

        # Append drill-down shortcuts for trading/research responses
        tickers = extract_tickers(enriched)
        sym = next((t for t in tickers if not is_futures(t)), None)
        if decision.task_type in _DEEP_TASKS and sym and not drill:
            result += (
                f"\n\n---\n*Drill down: "
                f"**swing {sym}** · **day {sym}** · "
                f"**options {sym}** · **research {sym}***"
            )
        return result

    except Exception as e:
        return header + f"> **Error:** {e}"


# ── UI layout ─────────────────────────────────────────────────────────────────
CSS = """
.gradio-container { max-width: 900px !important; margin: 0 auto !important; }
footer { display: none !important; }
"""

with gr.Blocks(title="OpenClaw", css=CSS) as demo:

    gr.Markdown("# OPENCLAW\n**Personal AI trading assistant** — live data, local models, institutional analysis.")

    with gr.Row():
        status_box = gr.Textbox(
            label="Servers", value=get_status(),
            interactive=False, max_lines=1, scale=5,
        )
        gr.Button("Refresh", scale=1, size="sm").click(get_status, outputs=status_box)

    gr.Markdown("""
| Type this | You get |
|---|---|
| `MSTR` | Full auto: live price + technicals + fundamentals + news + recommended play |
| `MNQ` | Futures day trade setup (Apex rules) — no menu, instant |
| `swing MSTR` | Swing trade: entry zone, SL1/SL2, TP1/TP2, position size |
| `day NVDA` | Day trade: intraday entry, stops, targets, exit rule |
| `options AAPL` | Options strategy: structure, strikes, expiry, IV context |
| `research TSLA` | Fundamental deep-dive: bull/bear case, catalysts, verdict |
| `plan my trading day` | Time-blocked plan around market hours |
| `session recap: 3W 2L +$240` | Journal with win rate, avg R, lessons |
""")

    gr.ChatInterface(
        fn=chat,
        chatbot=gr.Chatbot(
            height=520,
            render_markdown=True,
            show_label=False,
            placeholder="Type a ticker (MSTR, MNQ) or any request...",
        ),
        textbox=gr.Textbox(
            placeholder="MSTR · swing MSTR · day MNQ · options AAPL · research TSLA · plan my day...",
            scale=7,
        ),
        examples=[
            "MSTR",
            "MNQ",
            "swing TSLA",
            "day NVDA",
            "options AAPL",
            "research MSTR",
            "should I enter a long on MNQ, price at VWAP with RSI 52",
            "plan my trading day for tomorrow",
            "session recap: 3 wins 2 losses up $240",
            "write a Python function to calculate profit factor from a trade list",
        ],
    )

if __name__ == "__main__":
    print(f"\n  OpenClaw -> http://localhost:7860\n")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        inbrowser=True,
        share=False,
    )

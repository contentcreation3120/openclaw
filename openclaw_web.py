"""
OpenClaw Web UI
Launch: python openclaw_web.py  |  Opens at http://localhost:7860
"""
import sys
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from openclaw.router.router import route as openclaw_route
from openclaw.router.classifier import classify
from openclaw.market_data import extract_tickers, is_futures
from openclaw.server.lifecycle import start_all, status as server_status, ensure_model
from openclaw.tasks.prompts import get_prompt
from openclaw.config import settings

import gradio as gr

# ── Auto-start local servers + ensure primary model is installed ──────────────
print("\n  OpenClaw — starting local AI servers...")
_srv = start_all()
print(f"  Ollama   : {_srv['ollama']}")
print(f"  LM Studio: {_srv['lmstudio']}")

print(f"\n  Checking primary model: {settings.local_model}")
_pull = ensure_model(settings.local_model, on_progress=lambda l: print(f"  {l}"))
print(f"  Model status: {_pull}\n")

_DEEP_TASKS = {
    "trading","trading_futures","trading_stocks","trading_day",
    "signal","research","auto_analysis","options"
}
_FOLLOWUPS = {
    "yes","ok","sure","go ahead","continue","please","do it",
    "yep","yeah","correct","exactly","proceed",
}
_STRATEGY_WORDS = {
    "strategy","setup","trade","entry","stop","target","position",
    "swing","intraday","day trade","day trading","price","chart",
    "signal","buy","sell","long","short","options","option",
    "research","explain","what is","analyze","analysis",
}

_BTN_LABELS = {
    "swing":    ("📈", "Swing Trade", "Swing"),
    "day":      ("⚡", "Day Trade",   "Day"),
    "options":  ("🎯", "Options Play","Options"),
    "research": ("🔬", "Deep Research","Research"),
}


def get_status() -> str:
    s = server_status()
    return (
        f"Ollama: {s.get('ollama','offline').upper()}  |  "
        f"LM Studio: {s.get('lmstudio','offline').upper()}  |  "
        "Claude API: ONLINE (fallback)"
    )


def _chat(message: str, history: list) -> tuple[str, str]:
    """
    Core chat logic. Returns (response_str, detected_sym_or_empty).
    detected_sym is the ticker that was acted on, or "" if none.
    """
    if not message.strip():
        return "", ""

    msg_clean   = message.strip().lower().rstrip("!.?")
    enriched    = message
    forced_task = None
    detected_sym = ""

    # ── Short follow-up → inject last exchange as context ────────────────────
    words = message.strip().split()
    if len(words) <= 3 and msg_clean in _FOLLOWUPS and history:
        last_user  = history[-1][0] or ""
        last_ai    = history[-1][1] or ""
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
        detected_sym = sym
        if action == "swing":
            enriched = f"swing trade setup for {sym} — entry zone, SL1, SL2, TP1, TP2, position size"
        elif action == "day":
            enriched = f"day trade {sym} intraday — entry, SL1, SL2, TP1, TP2, exit rule before close"
        elif action in ("option", "options"):
            enriched    = f"options strategy for {sym} — best structure, strikes, expiry, IV rank context"
            forced_task = "options"
        elif action == "research":
            enriched    = f"research {sym} — full fundamental analysis, catalysts, bull case, bear case, verdict"
            forced_task = "research"

    # ── Auto-route: bare ticker with no action words ──────────────────────────
    drill_sym = drill.group(2).upper() if drill else None

    if not drill:
        p_lower  = enriched.lower()
        tickers  = extract_tickers(enriched)
        has_act  = any(w in p_lower for w in _STRATEGY_WORDS)

        if tickers and not has_act:
            sym = tickers[0]
            if is_futures(sym):
                enriched = (
                    f"day trade {sym} futures — "
                    f"Apex-compliant entry, SL1, SL2, TP1, TP2, contracts"
                )
                detected_sym = sym
            else:
                enriched     = f"auto analysis {sym}"
                forced_task  = "auto_analysis"
                drill_sym    = sym
                detected_sym = sym

    # ── Classify + optional task override ────────────────────────────────────
    decision   = classify(enriched)
    forced_sys = get_prompt(forced_task) if forced_task else ""
    if forced_task:
        decision.task_type = forced_task

    header = (
        f"> **[{decision.task_type}]** "
        f"routed to `{decision.model}` ({decision.backend})\n\n"
    )

    try:
        response = openclaw_route(enriched, system=forced_sys, task_type=forced_task)
        if not response:
            return header + "> *(model returned empty — Ollama may still be loading, try again)*", detected_sym

        result = header + response

        # Append drill-down footer (only for stock tickers, only when not already a drill-down)
        if decision.task_type in _DEEP_TASKS and drill_sym and not is_futures(drill_sym):
            footer = (
                f"\n\n---\n*Drill down: "
                f"**swing {drill_sym}** · **day {drill_sym}** · "
                f"**options {drill_sym}** · **research {drill_sym}***"
            )
            if f"swing {drill_sym}" not in result:
                result += footer

        return result, detected_sym

    except Exception as e:
        return header + f"> **Error:** {e}", detected_sym


def _btn_labels(sym: str) -> tuple[str, str, str, str]:
    """Return button labels for the 4 drill-down buttons."""
    if sym:
        return (
            f"📈 Swing {sym}",
            f"⚡ Day {sym}",
            f"🎯 Options {sym}",
            f"🔬 Research {sym}",
        )
    return (
        "📈 Swing Trade",
        "⚡ Day Trade",
        "🎯 Options Play",
        "🔬 Deep Research",
    )


def respond(message: str, history: list, last_sym: str) -> tuple:
    """
    Main Gradio handler. Returns:
      (history, last_sym, clear_textbox, btn_swing, btn_day, btn_opts, btn_research, btn_row_visibility)
    """
    if not message.strip():
        s0, s1, s2, s3 = _btn_labels(last_sym)
        visible = gr.update(visible=bool(last_sym))
        return history, last_sym, "", gr.update(value=s0), gr.update(value=s1), gr.update(value=s2), gr.update(value=s3), visible

    response_str, detected = _chat(message, history)
    new_sym = detected if detected else last_sym

    history = history + [[message, response_str]]

    s0, s1, s2, s3 = _btn_labels(new_sym)
    visible = gr.update(visible=bool(new_sym))

    return (
        history,
        new_sym,
        "",                      # clear textbox
        gr.update(value=s0),
        gr.update(value=s1),
        gr.update(value=s2),
        gr.update(value=s3),
        visible,
    )


def respond_drill(action: str, history: list, last_sym: str) -> tuple:
    """Called by the drill-down buttons."""
    if not last_sym:
        s0, s1, s2, s3 = _btn_labels(last_sym)
        visible = gr.update(visible=False)
        return history, last_sym, gr.update(value=s0), gr.update(value=s1), gr.update(value=s2), gr.update(value=s3), visible

    message = f"{action} {last_sym}"
    response_str, detected = _chat(message, history)
    new_sym = detected if detected else last_sym

    history = history + [[message, response_str]]

    s0, s1, s2, s3 = _btn_labels(new_sym)
    visible = gr.update(visible=bool(new_sym))

    return (
        history,
        new_sym,
        gr.update(value=s0),
        gr.update(value=s1),
        gr.update(value=s2),
        gr.update(value=s3),
        visible,
    )


# ── UI ────────────────────────────────────────────────────────────────────────
CSS = """
.gradio-container { max-width: 900px !important; margin: 0 auto !important; }
footer { display: none !important; }
#drill-row { gap: 8px; }
#drill-row button { flex: 1; }
"""

EXAMPLES = [
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
]

with gr.Blocks(title="OpenClaw") as demo:

    gr.Markdown(
        "# OPENCLAW\n"
        "**Personal AI trading assistant** — live data, local models, institutional analysis."
    )

    with gr.Row():
        status_box = gr.Textbox(
            label="Servers", value=get_status(),
            interactive=False, max_lines=1, scale=5,
        )
        gr.Button("Refresh", scale=1, size="sm").click(get_status, outputs=status_box)

    gr.Markdown("""
| Type this | You get | Model |
|---|---|---|
| `MSTR` | Full auto: price + technicals + fundamentals + news + play | Hermes3 (local) |
| `MNQ` | Futures day trade setup (Apex rules) — instant, no menu | Hermes3 (local) |
| `swing MSTR` | Swing trade: entry zone, SL1/SL2, TP1/TP2, position size | Hermes3 (local) |
| `day NVDA` | Day trade: intraday entry, stops, targets, exit rule | Hermes3 (local) |
| `options AAPL` | Options strategy: structure, strikes, expiry, IV context | Hermes3 (local) |
| `research TSLA` | Institutional deep-dive: patterns, insiders, 15yr thesis | Hermes3 (local) |
| `plan my trading day` | Time-blocked plan around market hours | Hermes3 (local) |
| `write a Python function` | Code | Devstral (LM Studio) |
| *Ollama offline* | Any request | Claude API (auto fallback) |
""")

    # ── State ────────────────────────────────────────────────────────────────
    last_sym_state = gr.State("")

    # ── Chatbot ──────────────────────────────────────────────────────────────
    chatbot = gr.Chatbot(
        height=520,
        render_markdown=True,
        show_label=False,
        placeholder="Type a ticker (MSTR, MNQ) or any request...",
    )

    # ── Drill-down buttons (hidden until a ticker is detected) ────────────────
    with gr.Row(visible=False, elem_id="drill-row") as btn_row:
        btn_swing    = gr.Button("📈 Swing Trade",   variant="secondary", size="sm")
        btn_day      = gr.Button("⚡ Day Trade",     variant="secondary", size="sm")
        btn_opts     = gr.Button("🎯 Options Play",  variant="secondary", size="sm")
        btn_research = gr.Button("🔬 Deep Research", variant="primary",   size="sm")

    # ── Input row ────────────────────────────────────────────────────────────
    with gr.Row():
        txt = gr.Textbox(
            placeholder="MSTR · swing MSTR · day MNQ · options AAPL · research TSLA · plan my day...",
            scale=8,
            show_label=False,
            container=False,
        )
        send_btn = gr.Button("Send", variant="primary", scale=1)

    # ── Examples ─────────────────────────────────────────────────────────────
    gr.Examples(
        examples=EXAMPLES,
        inputs=txt,
        label="Quick examples",
    )

    # ── Shared outputs list ──────────────────────────────────────────────────
    _respond_outputs = [
        chatbot, last_sym_state, txt,
        btn_swing, btn_day, btn_opts, btn_research, btn_row,
    ]
    _drill_outputs = [
        chatbot, last_sym_state,
        btn_swing, btn_day, btn_opts, btn_research, btn_row,
    ]

    # ── Wire submit / click ──────────────────────────────────────────────────
    txt.submit(
        fn=respond,
        inputs=[txt, chatbot, last_sym_state],
        outputs=_respond_outputs,
    )
    send_btn.click(
        fn=respond,
        inputs=[txt, chatbot, last_sym_state],
        outputs=_respond_outputs,
    )

    btn_swing.click(
        fn=lambda h, s: respond_drill("swing", h, s),
        inputs=[chatbot, last_sym_state],
        outputs=_drill_outputs,
    )
    btn_day.click(
        fn=lambda h, s: respond_drill("day", h, s),
        inputs=[chatbot, last_sym_state],
        outputs=_drill_outputs,
    )
    btn_opts.click(
        fn=lambda h, s: respond_drill("options", h, s),
        inputs=[chatbot, last_sym_state],
        outputs=_drill_outputs,
    )
    btn_research.click(
        fn=lambda h, s: respond_drill("research", h, s),
        inputs=[chatbot, last_sym_state],
        outputs=_drill_outputs,
    )

if __name__ == "__main__":
    print(f"\n  OpenClaw -> http://localhost:7860\n")
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        inbrowser=True,
        share=False,
        css=CSS,
    )

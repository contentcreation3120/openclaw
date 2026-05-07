"""
OpenClaw Chat GUI — tkinter, zero extra dependencies.
Run: python openclaw_gui.py
"""
import tkinter as tk
from tkinter import scrolledtext
import threading
import subprocess
import sys
import os

PYTHON = sys.executable
BG        = "#0d0d14"
BG_INPUT  = "#1c1c2a"
BG_HEADER = "#12121c"
CYAN      = "#50c8ff"
GREEN     = "#50e68c"
YELLOW    = "#e6b432"
DIM       = "#505070"
WHITE     = "#dcdceb"
BTN_GREEN = "#196641"
BTN_RED   = "#8c1e1e"

class OpenClawApp:
    def __init__(self, root):
        self.root = root
        root.title("OpenClaw — Hybrid AI Router")
        root.configure(bg=BG)
        root.geometry("820x660")
        root.minsize(640, 500)
        self._build_ui()

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG_HEADER, height=60)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="OPENCLAW", font=("Segoe UI", 18, "bold"),
                 fg=CYAN, bg=BG_HEADER).place(x=14, y=8)
        tk.Label(hdr, text="Local first. Claude when it counts.",
                 font=("Segoe UI", 8), fg=DIM, bg=BG_HEADER).place(x=16, y=38)

        # Status dots
        self.dot_ollama   = tk.Label(hdr, text="● Ollama",    font=("Segoe UI", 8), fg=DIM, bg=BG_HEADER)
        self.dot_lmstudio = tk.Label(hdr, text="● LM Studio", font=("Segoe UI", 8), fg=DIM, bg=BG_HEADER)
        self.dot_claude   = tk.Label(hdr, text="● Claude API", font=("Segoe UI", 8), fg=DIM, bg=BG_HEADER)
        self.dot_ollama.place(x=270, y=10)
        self.dot_lmstudio.place(x=270, y=32)
        self.dot_claude.place(x=400, y=10)

        tk.Button(hdr, text="▶ START", font=("Segoe UI", 8, "bold"),
                  bg=BTN_GREEN, fg="white", relief="flat", cursor="hand2",
                  command=self._start_servers).place(x=690, y=10, width=100, height=20)
        tk.Button(hdr, text="■ STOP", font=("Segoe UI", 8, "bold"),
                  bg=BTN_RED, fg="white", relief="flat", cursor="hand2",
                  command=self._stop_servers).place(x=690, y=34, width=100, height=20)

        # ── Route badge ──────────────────────────────────────────────────────
        self.badge_var = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self.badge_var,
                 font=("Segoe UI", 7, "bold"), fg=CYAN, bg=BG,
                 anchor="w").pack(fill="x", padx=8, pady=(4, 0))

        # ── Chat area ────────────────────────────────────────────────────────
        self.chat = scrolledtext.ScrolledText(
            self.root, bg=BG, fg=WHITE, font=("Consolas", 9),
            relief="flat", state="disabled", wrap="word",
            padx=6, pady=6
        )
        self.chat.pack(fill="both", expand=True, padx=8, pady=(2, 4))
        self.chat.tag_config("you",    foreground=CYAN)
        self.chat.tag_config("ai",     foreground=GREEN)
        self.chat.tag_config("system", foreground=YELLOW)
        self.chat.tag_config("error",  foreground="#e65050")

        # ── Input row ────────────────────────────────────────────────────────
        bar = tk.Frame(self.root, bg=BG_INPUT)
        bar.pack(fill="x", padx=8, pady=(0, 8))

        self.input_var = tk.StringVar()
        self.entry = tk.Entry(bar, textvariable=self.input_var,
                              font=("Segoe UI", 10), bg=BG_INPUT, fg=WHITE,
                              relief="flat", insertbackground=WHITE)
        self.entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(6, 0))
        self.entry.bind("<Return>", lambda e: self._send())

        self.send_btn = tk.Button(bar, text="Send  ▶", font=("Segoe UI", 9, "bold"),
                                  bg=BTN_GREEN, fg="white", relief="flat",
                                  cursor="hand2", command=self._send)
        self.send_btn.pack(side="right", ipadx=10, ipady=6)

        # ── Status bar ───────────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(self.root, textvariable=self.status_var,
                 font=("Segoe UI", 7), fg=DIM, bg=BG, anchor="w"
                 ).pack(fill="x", padx=10, pady=(0, 4))

        self._log("system", "OpenClaw ready. Type a prompt below and press Enter.")
        self._log("system", "strategy → Claude Sonnet  |  signal → Nemotron  |  journal → GPT-OSS  |  code → Devstral")
        self.entry.focus()

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _log(self, role, text):
        self.chat.configure(state="normal")
        prefix = {"you": "You: ", "ai": "AI:  ", "system": "---  ", "error": "ERR: "}[role]
        self.chat.insert("end", prefix, role)
        self.chat.insert("end", text + "\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _set_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()

    # ── Send ─────────────────────────────────────────────────────────────────
    def _send(self):
        prompt = self.input_var.get().strip()
        if not prompt:
            return
        self.input_var.set("")
        self.send_btn.configure(state="disabled")
        self._log("you", prompt)
        threading.Thread(target=self._route, args=(prompt,), daemon=True).start()

    def _route(self, prompt):
        self._set_status("Routing...")

        # Get routing decision
        try:
            dec = subprocess.run(
                [PYTHON, "-m", "openclaw", "explain", prompt],
                capture_output=True, text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            lines = (dec.stdout or "")
            task  = next((l.split(":")[-1].strip() for l in lines.splitlines() if "Task type" in l), "?")
            model = next((l.split(":")[-1].strip() for l in lines.splitlines() if "Model" in l), "?")
            backend = next((l.split(":")[-1].strip() for l in lines.splitlines() if "Backend" in l), "?")
            self.badge_var.set(f"  [{task}]  →  {model}  ({backend})")
            self._set_status(f"Calling {model}...")
        except Exception:
            self.badge_var.set("")

        # Get actual response
        try:
            result = subprocess.run(
                [PYTHON, "-m", "openclaw", "route", prompt],
                capture_output=True, text=True, timeout=120,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )
            # stdout = model response, stderr = loguru logs (ignore)
            response = (result.stdout or "").strip()
            if response:
                self.root.after(0, self._log, "ai", response)
            else:
                self.root.after(0, self._log, "error", "No response. Is Ollama running? Check .env for API key.")
        except subprocess.TimeoutExpired:
            self.root.after(0, self._log, "error", "Timed out after 120s.")
        except Exception as e:
            self.root.after(0, self._log, "error", str(e))

        self._set_status("Ready")
        self.root.after(0, lambda: self.send_btn.configure(state="normal"))
        self.root.after(0, self.entry.focus)

    # ── Server controls ───────────────────────────────────────────────────────
    def _start_servers(self):
        self._log("system", "Starting servers...")
        threading.Thread(target=self._run_start, daemon=True).start()

    def _run_start(self):
        scripts = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass",
                        "-File", os.path.join(scripts, "start_servers.ps1")],
                       capture_output=True)
        self.dot_ollama.configure(fg=GREEN)
        self.dot_claude.configure(fg=GREEN)
        self.dot_lmstudio.configure(fg=YELLOW)
        self.root.after(0, self._log, "system", "Ollama started. LM Studio: open it and click Start Server.")

    def _stop_servers(self):
        self._log("system", "Stopping servers...")
        threading.Thread(target=self._run_stop, daemon=True).start()

    def _run_stop(self):
        scripts = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
        subprocess.run(["powershell", "-ExecutionPolicy", "Bypass",
                        "-File", os.path.join(scripts, "stop_servers.ps1")],
                       capture_output=True)
        for dot in [self.dot_ollama, self.dot_lmstudio, self.dot_claude]:
            dot.configure(fg=DIM)
        self.root.after(0, self._log, "system", "Local servers stopped.")


if __name__ == "__main__":
    root = tk.Tk()
    app = OpenClawApp(root)
    root.mainloop()

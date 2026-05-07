"""Run a single chat message and print the response."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress gradio init output
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

from openclaw.server.lifecycle import start_all
start_all()

from openclaw_web import _chat

msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "MSTR"
print(f"\nQ: {msg}\n" + "="*70)
response, sym = _chat(msg, [])
print(response)
print(f"\n[detected sym: {sym}]")

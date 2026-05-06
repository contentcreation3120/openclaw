import sys
import io
from openclaw.router.router import route, explain

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def main():
    if len(sys.argv) < 3:
        print("Usage: python -m openclaw explain <prompt>")
        print("       python -m openclaw route <prompt>")
        sys.exit(1)
    cmd, prompt = sys.argv[1], " ".join(sys.argv[2:])
    if cmd == "explain":
        d = explain(prompt)
        print(f"\nTask type : {d.task_type}")
        print(f"Model     : {d.model}")
        print(f"Backend   : {d.backend}")
        print(f"Reason    : {d.reason}\n")
    elif cmd == "route":
        print(route(prompt))

if __name__ == "__main__":
    main()

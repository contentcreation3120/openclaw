"""
Standalone test runner for OpenClaw test suite.
Run with: python tests/agent.py
"""
import subprocess
import sys
import os
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TESTS = [
    ("classifier",   "tests/test_classifier.py"),
    ("market_data",  "tests/test_market_data.py"),
    ("chat_flow",    "tests/test_chat_flow.py"),
    ("edge_cases",   "tests/test_edge_cases.py"),
]

COL_NAME   = 14
COL_PASS   = 7
COL_FAIL   = 7
COL_ERROR  = 7
COL_TIME   = 8

LINE = "-" * (COL_NAME + COL_PASS + COL_FAIL + COL_ERROR + COL_TIME + 12)


def run_test(name, path):
    start = time.time()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", path, "-v", "--tb=short", "--no-header"],
        capture_output=True,
        text=True,
        cwd=BASE,
    )
    elapsed = time.time() - start
    stdout = result.stdout + result.stderr

    passed = stdout.count(" PASSED")
    failed = stdout.count(" FAILED")
    errors = stdout.count(" ERROR")

    return {
        "name":    name,
        "passed":  passed,
        "failed":  failed,
        "errors":  errors,
        "time":    elapsed,
        "ok":      result.returncode == 0,
        "output":  stdout,
    }


def main():
    print()
    print("  OpenClaw Test Suite")
    print(LINE)
    print(
        f"  {'Suite':<{COL_NAME}}  "
        f"{'PASSED':>{COL_PASS}}  "
        f"{'FAILED':>{COL_FAIL}}  "
        f"{'ERROR':>{COL_ERROR}}  "
        f"{'TIME':>{COL_TIME}}  "
        f"STATUS"
    )
    print(LINE)

    results = []
    for name, path in TESTS:
        r = run_test(name, path)
        results.append(r)
        status = "OK" if r["ok"] else "FAIL"
        print(
            f"  {r['name']:<{COL_NAME}}  "
            f"{r['passed']:>{COL_PASS}}  "
            f"{r['failed']:>{COL_FAIL}}  "
            f"{r['errors']:>{COL_ERROR}}  "
            f"{r['time']:>{COL_TIME-1}.1f}s  "
            f"{status}"
        )

        # Print failure details
        if not r["ok"]:
            for line in r["output"].splitlines():
                if line.strip():
                    print(f"    {line}")

    print(LINE)

    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    total_errors = sum(r["errors"] for r in results)
    total_time   = sum(r["time"]   for r in results)
    all_ok       = all(r["ok"]     for r in results)

    print(
        f"  {'TOTAL':<{COL_NAME}}  "
        f"{total_passed:>{COL_PASS}}  "
        f"{total_failed:>{COL_FAIL}}  "
        f"{total_errors:>{COL_ERROR}}  "
        f"{total_time:>{COL_TIME-1}.1f}s  "
        f"{'ALL OK' if all_ok else 'FAILURES'}"
    )
    print(LINE)
    print()

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()

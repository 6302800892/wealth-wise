"""Harness evaluator helper: run a sprint contract's API checks against a running WealthWise app.

Usage:
    python scripts/evaluate_contract.py sprint-contracts/sprint-1.json --base-url http://127.0.0.1:8000

Writes a Markdown report to specs/reviews/<contract-name>-api-evaluation.md and exits non-zero
when any check fails, so it can gate the ratchet. Standard library only.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _request(base_url, method, path, body=None, token=None, extra_headers=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json", **(extra_headers or {})}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(base_url + path, data=data, method=method, headers=headers)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    payload = json.loads(raw) if raw else None
    return status, payload, elapsed_ms


def _subset(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and _subset(v, actual[k]) for k, v in expected.items())
    return expected == actual


def _login(base_url, username, password, cache):
    if username not in cache:
        status, payload, _ = _request(base_url, "POST", "/api/v1/auth/login",
                                      {"username": username, "password": password})
        if status != 200:
            raise RuntimeError(f"login failed for {username}: {status}")
        cache[username] = payload["token"]
    return cache[username]


def run_check(base_url, check, password, tokens):
    token = _login(base_url, check["auth"], password, tokens) if check.get("auth") else None
    status, payload, elapsed = _request(base_url, check["method"], check["path"], check.get("body"), token)
    ok = status == check["expected_status"] and _subset(check.get("expected_body", {}), payload or {})
    limit = check.get("max_response_time_ms")
    if limit is not None and elapsed > limit:
        ok = False
    return {"id": check["id"], "description": check["description"], "status": status,
            "expected": check["expected_status"], "elapsed_ms": elapsed, "passed": ok}


def _report(contract_path, results):
    passed = sum(r["passed"] for r in results)
    lines = [f"# API evaluation — {contract_path.stem}", "",
             f"Checks passed: **{passed}/{len(results)}**", "",
             "| ID | Description | Expected | Actual | ms | Result |", "|---|---|---|---|---|---|"]
    for r in results:
        verdict = "PASS" if r["passed"] else "FAIL"
        lines.append(f"| {r['id']} | {r['description']} | {r['expected']} | {r['status']} | {r['elapsed_ms']} | {verdict} |")
    return "\n".join(lines) + "\n"


def _start_server(port):
    """Start a throwaway app instance on a temporary DB and wait for /health."""
    db = Path(tempfile.mkdtemp()) / "eval.db"
    env = {**os.environ, "WEALTHWISE_DB_PATH": str(db), "WEALTHWISE_PORT": str(port),
           "WEALTHWISE_BUSINESS_DATE": "2026-09-30", "WEALTHWISE_LOG_LEVEL": "WARNING"}
    process = subprocess.Popen([sys.executable, "-m", "src.main"], cwd=ROOT, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            if _request(f"http://127.0.0.1:{port}", "GET", "/health")[0] == 200:
                return process
        except urllib.error.URLError:
            time.sleep(0.5)
    process.terminate()
    raise RuntimeError("server did not become healthy")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--password", default="WealthWise@2026")
    parser.add_argument("--start", action="store_true", help="start a temporary server on port 8765")
    args = parser.parse_args()
    server = _start_server(8765) if args.start else None
    if server is not None:
        args.base_url = "http://127.0.0.1:8765"
    try:
        return _evaluate(args)
    finally:
        if server is not None:
            server.terminate()


def _evaluate(args) -> int:
    contract_path = Path(args.contract)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    tokens: dict[str, str] = {}
    results = [run_check(args.base_url, c, args.password, tokens) for c in contract["contract"]["api_checks"]]
    out = ROOT / "specs" / "reviews" / f"{contract_path.stem}-api-evaluation.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_report(contract_path, results), encoding="utf-8")
    print(out.read_text(encoding="utf-8"))
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

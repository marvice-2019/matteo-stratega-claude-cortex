"""Checks the simplest-approach hook. Run: python3 tests/test_simplest_approach.py"""

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent.parent / "hooks" / "simplest-approach-enforcer.py"
CASES = [
    (
        "BLOCK",
        "read page",
        "python3 -c 'from playwright.sync_api import sync_playwright; p=sync_playwright().start(); pg=p.chromium.launch().new_page(); pg.goto(\"https://x.com\"); print(pg.content())'",
    ),
    (
        "BLOCK",
        "puppeteer scrape",
        "node -e \"require('puppeteer').launch().then(b=>b.newPage())\"",
    ),
    ("BLOCK", "read page | cat", "node -e \"require('puppeteer').launch()\" | cat"),
    ("BLOCK", "launch chrome", "google-chrome https://example.com"),
    ("ALLOW", "skills search", "npx -y skills find playwright"),
    (
        "ALLOW",
        "skills install",
        "npx -y skills add anthropics/skills --skill webapp-testing",
    ),
    (
        "ALLOW",
        "pytest",
        "pytest tests/test_checkout.py --browser chromium  # playwright",
    ),
    ("ALLOW", "playwright test", "npx playwright test --trace off"),
    (
        "ALLOW",
        "with_server",
        "python scripts/with_server.py --server 'npm run dev' --port 5173 -- python test_playwright.py",
    ),
    (
        "ALLOW",
        "inline screenshot",
        "python3 - <<'PY'\nfrom playwright.sync_api import sync_playwright\nwith sync_playwright() as p:\n  pg=p.chromium.launch().new_page(); pg.goto('https://client.in'); pg.screenshot(path='s.png')\nPY",
    ),
    (
        "ALLOW",
        "inline form test",
        "python3 - <<'PY'\nfrom playwright.sync_api import sync_playwright\nwith sync_playwright() as p:\n  pg=p.chromium.launch().new_page(); pg.goto('https://client.in/contact'); pg.fill('#name','T'); pg.click('button')\nPY",
    ),
    ("ALLOW", "grep a file", "grep -rn playwright package.json"),
    ("ALLOW", "plain command", "ls -la"),
]


def decision(cmd: str) -> str:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
    out = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    return "BLOCK" if "deny" in out else "ALLOW"


def main() -> int:
    failures = 0
    for want, name, cmd in CASES:
        got = decision(cmd)
        failures += got != want
        print(f"{name:20} want={want} got={got}{'' if got == want else '  <-- FAIL'}")
    print("FAILURES:", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

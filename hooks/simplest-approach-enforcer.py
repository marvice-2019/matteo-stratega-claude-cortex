#!/usr/bin/env python3
"""
Hook: Simplest Approach Enforcer
Trigger: PreToolUse
Purpose: Blocks overcomplicated tool usage when a simpler built-in exists.
         Catches the classic "spin up a browser to read a web page" reflex.

Patch (testing exemption): browser automation is allowed when the command is
clearly a TEST or a tooling command, because WebFetch cannot click, fill forms,
take screenshots or capture console errors. Reading a page is still blocked.
"""

import json
import re
import sys

# Commands that are testing or tooling, never "reading a page".
TESTING_EXEMPTIONS = [
    r"\bpytest\b",  # pytest suites
    r"playwright\s+(test|show-report|install)\b",  # Playwright test runner / setup
    r"\bwith_server\.py\b",  # webapp-testing skill helper
    r"\bskills\s+(find|add|list|remove)\b",  # skills CLI (search/install)
    r"\b(pip3?|npm|pnpm|yarn)\s+(install|i|add)\b",  # installing packages
    r"^\s*(grep|rg|ls|cat|head|tail)\b",  # command STARTS by just looking at files/text
]

# Inline scripts that INTERACT with a page (things WebFetch cannot do).
INTERACTION_SIGNALS = (
    r"\.(click|fill|check|select_option|screenshot|set_input_files|press|hover)\("
    r"|\.on\(\s*['\"](console|pageerror|request|response)['\"]"
    r"|\bexpect\(|\bassert\b"
)

BLOCKED_PATTERNS = {
    "Bash": [
        {
            "pattern": r"playwright|puppeteer|cypress|selenium",
            "exempt_if_testing": True,
            "reason": "Browser automation detected. To read a web page use WebFetch. "
            "To edit files use Edit. To check built HTML use Read on the output file. "
            "(Testing is allowed: run it via pytest/playwright test/with_server.py, "
            "or make the script interact with the page: click, fill, screenshot, "
            "console capture, assertions.)",
            "suggestion": "WebFetch (read pages), Edit (modify files), Read (check output)",
        },
        {
            # Anchored to LAUNCHING a browser, not the word "chrome" anywhere
            # (so `grep chrome` or a container named chromium is not blocked).
            "pattern": r"open\s+-a\s+['\"]?(google chrome|chromium|safari)|\bgoogle-chrome\b|\bchromium-browser\b|chromium\s+--",
            "exempt_if_testing": False,
            "reason": "Opening a browser is almost never needed. To read web content use WebFetch. "
            "To check built HTML use Read.",
            "suggestion": "WebFetch or Read",
        },
    ]
}


def is_testing(command: str) -> bool:
    if any(re.search(p, command, re.IGNORECASE) for p in TESTING_EXEMPTIONS):
        return True
    return re.search(INTERACTION_SIGNALS, command) is not None


def main():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        print(json.dumps({}))
        return

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name in BLOCKED_PATTERNS:
        check_text = tool_input.get("command", "") if tool_name == "Bash" else ""
        if check_text:
            for rule in BLOCKED_PATTERNS[tool_name]:
                if re.search(rule["pattern"], check_text, re.IGNORECASE):
                    if rule["exempt_if_testing"] and is_testing(check_text):
                        continue
                    print(
                        json.dumps(
                            {
                                "hookSpecificOutput": {
                                    "hookEventName": "PreToolUse",
                                    "permissionDecision": "deny",
                                    "permissionDecisionReason": (
                                        f"Overcomplicated approach. {rule['reason']} "
                                        f"Use instead: {rule['suggestion']}. "
                                        f"Rule: always reach for the SIMPLEST tool first."
                                    ),
                                }
                            }
                        )
                    )
                    return

    print(json.dumps({}))


if __name__ == "__main__":
    main()

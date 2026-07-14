#!/usr/bin/env python3
import json
import os
import sys

data = json.load(sys.stdin)
tool_input = data.get("tool_input", {})
cmd = tool_input.get("command", "") or ""

safe_prefixes = [
    "git status",
    "git diff",
    "mvn test",
    "mvn -q -DskipTests compile",
    "mvn -DskipTests package",
]

if any(cmd.startswith(p) for p in safe_prefixes):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
        }
    }))
    sys.exit(0)

change_dir = "openspec/changes"
has_change = os.path.isdir(change_dir) and any(
    os.path.isdir(os.path.join(change_dir, x))
    for x in os.listdir(change_dir)
)

if not has_change:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": "当前未检测到 OpenSpec change，请确认是否继续",
        }
    }))
    sys.exit(0)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
    }
}))

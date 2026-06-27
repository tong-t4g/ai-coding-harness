#!/usr/bin/env python3
import json
import sys
import fnmatch
data = json.load(sys.stdin)
tool_input = data.get("tool_input", {})
file_path = tool_input.get("file_path", "") or ""
blocked_patterns = [
 "*/src/main/resources/application*.yml",
 "*/src/main/resources/bootstrap*.yml",
 "*/src/main/resources/db/*",
 "*/sql/*",
 "*/deploy/*",
 "*/infra/*",
 "*/secrets/*"
]
for pattern in blocked_patterns:
 if fnmatch.fnmatch(file_path, pattern):
 print(json.dumps({
 "hookSpecificOutput": {
 "hookEventName": "PreToolUse",
 "permissionDecision": "deny",
 "permissionDecisionReason": f"禁止修改受保护路径: {pattern}"
 }
 }))
 sys.exit(0)
print(json.dumps({
 "hookSpecificOutput": {
 "hookEventName": "PreToolUse",
 "permissionDecision": "allow",
 "permissionDecisionReason": "允许修改该路径"
 }
}))
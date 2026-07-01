#!/usr/bin/env python3
import json
import os
import pathlib
import re
import subprocess
import sys


OPENSPEC_CHANGES_PREFIX = "openspec/changes/"


def emit(output):
    print(json.dumps(output, ensure_ascii=True))


def allow_request():
    emit({
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {
                "behavior": "allow",
            },
        },
    })


def find_repo_root(cwd):
    base = cwd or os.getcwd()
    try:
        output = subprocess.check_output(
            ["git", "-C", base, "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if output:
            return pathlib.Path(output)
    except Exception:
        pass
    return pathlib.Path(base).resolve()


def normalize_repo_path(raw_path, repo_root):
    if not isinstance(raw_path, str):
        return None

    path = raw_path.strip().strip("\"'")
    if not path or path == "/dev/null":
        return None

    path = path.replace("\\", "/")
    if path.startswith("a/") or path.startswith("b/"):
        path = path[2:]

    try:
        candidate = pathlib.Path(path)
        if candidate.is_absolute():
            try:
                path = candidate.resolve().relative_to(repo_root.resolve()).as_posix()
            except ValueError:
                path = candidate.resolve().as_posix()
    except Exception:
        pass

    path = re.sub(r"^\./+", "", path)
    return path.strip("/")


def extract_patch_paths(command, repo_root):
    paths = set()
    if not isinstance(command, str):
        return paths

    patterns = (
        re.compile(r"^\*\*\* (?:Add|Delete|Update) File:\s+(.+)$"),
        re.compile(r"^\*\*\* Move to:\s+(.+)$"),
    )

    for line in command.splitlines():
        for pattern in patterns:
            match = pattern.match(line)
            if match:
                path = normalize_repo_path(match.group(1), repo_root)
                if path:
                    paths.add(path)
                break

    return paths


def extract_touched_paths(tool_input, repo_root):
    paths = set()
    if not isinstance(tool_input, dict):
        return paths

    for key in ("file_path", "path"):
        path = normalize_repo_path(tool_input.get(key), repo_root)
        if path:
            paths.add(path)

    for key in ("paths", "files"):
        values = tool_input.get(key)
        if isinstance(values, list):
            for value in values:
                path = normalize_repo_path(value, repo_root)
                if path:
                    paths.add(path)

    paths.update(extract_patch_paths(tool_input.get("command"), repo_root))
    return paths


def is_openspec_change_path(path):
    return path.replace("\\", "/").startswith(OPENSPEC_CHANGES_PREFIX)


def has_active_openspec_proposal(repo_root):
    changes_dir = repo_root / "openspec" / "changes"
    if not changes_dir.is_dir():
        return False

    for child in changes_dir.iterdir():
        if child.name == "archive" or not child.is_dir():
            continue
        if (child / "proposal.md").is_file():
            return True

    return False


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        emit({
            "systemMessage": "OpenSpec write gate received invalid hook input; continuing normal approval.",
        })
        return 0

    repo_root = find_repo_root(payload.get("cwd"))
    tool_input = payload.get("tool_input", {})
    touched_paths = extract_touched_paths(tool_input, repo_root)

    if touched_paths and all(is_openspec_change_path(path) for path in touched_paths):
        allow_request()
        return 0

    if has_active_openspec_proposal(repo_root):
        allow_request()
        return 0

    emit({
        "systemMessage": (
            "No active OpenSpec proposal was found under "
            "openspec/changes/<change-id>/proposal.md. "
            "Please decide whether to continue this code change."
        ),
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Install the bt2any skill into an agent's skill directory.

One canonical skill lives in this repo. The installer copies the whole skill
(SKILL.md + references/ + scripts/ + examples/) into the target agent directory so
Claude Code, Codex, CodeBuddy and Kiro can all use it. Re-run to update.

Usage:
    python3 install.py --agent auto
    python3 install.py --agent claude --target /path/to/project
    python3 install.py --agent all --target /path/to/project
    python3 install.py --agent codebuddy --global
"""
import argparse
import os
import shutil
import sys

SKILL_NAME = "bt2any"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REL = {
    "claude": os.path.join(".claude", "skills", SKILL_NAME),
    "codex": os.path.join(".agents", "skills", SKILL_NAME),
    "codebuddy": os.path.join(".codebuddy", "skills", SKILL_NAME),
    "kiro": os.path.join(".kiro", "skills", SKILL_NAME),
}
GLOBAL_BASE = {
    "claude": os.path.join(os.path.expanduser("~"), ".claude", "skills", SKILL_NAME),
    "codex": os.path.join(os.path.expanduser("~"), ".agents", "skills", SKILL_NAME),
    "codebuddy": os.path.join(os.path.expanduser("~"), ".codebuddy", "skills", SKILL_NAME),
    "kiro": os.path.join(os.path.expanduser("~"), ".kiro", "skills", SKILL_NAME),
}
COPY_ITEMS = ["SKILL.md", "references", "scripts", "examples", "agents", "README.md"]


def detect_agent(target):
    for name, rel in REL.items():
        if os.path.isdir(os.path.join(target, rel.split(os.sep)[0])):
            return name
    return "claude"  # sensible default


def install(dest):
    os.makedirs(dest, exist_ok=True)
    for item in COPY_ITEMS:
        src = os.path.join(REPO, item)
        if not os.path.exists(src):
            continue
        dst = os.path.join(dest, item)
        if os.path.isdir(src):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    print(f"installed/updated {SKILL_NAME} -> {dest}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--agent", choices=list(REL) + ["auto", "all"], default="auto")
    ap.add_argument("--target", default=os.getcwd(), help="project root (for local install)")
    ap.add_argument("--global", dest="as_global", action="store_true",
                    help="install into the user home global skill directory")
    a = ap.parse_args()

    if a.agent == "all":
        agents = list(REL)
    elif a.agent == "auto":
        agents = [detect_agent(a.target)]
    else:
        agents = [a.agent]

    for agent in agents:
        if a.as_global:
            dest = GLOBAL_BASE[agent]
        else:
            dest = os.path.join(a.target, REL[agent])
        install(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())

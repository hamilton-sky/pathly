"""Shared constants for the candidate CLI implementation."""

from __future__ import annotations

import re


CORE_PLAN_FILES = {
    "USER_STORIES.md": "# User Stories\n\n",
    "IMPLEMENTATION_PLAN.md": "# Implementation Plan\n\n",
    "PROGRESS.md": "# Progress\n\n| Conversation | Status |\n|---|---|\n",
    "CONVERSATION_PROMPTS.md": "# Conversation Prompts\n\n",
}

STANDARD_PLAN_FILES = {
    "HAPPY_FLOW.md",
    "EDGE_CASES.md",
    "ARCHITECTURE_PROPOSAL.md",
    "FLOW_DIAGRAM.md",
}

FEATURE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
PROMOTION_TARGET_RE = re.compile(
    r"^## Promotion Target\s*(?:\r?\n)+([A-Za-z-]+)\s*$",
    re.MULTILINE,
)

READ_ONLY_TOOLS = "Read,Glob,Grep,Agent"
PLAN_WRITE_TOOLS = "Read,Glob,Grep,Write,Edit,Agent"

MEET_ALLOWED_ROLES = {
    "planner": "requirements, stories, acceptance criteria, task breakdown",
    "architect": "design, layers, contracts, migrations, rollback",
    "reviewer": "review risks, contract violations, diff quality",
    "tester": "verification strategy, acceptance coverage, likely gaps",
    "po": "product scope, user value, success criteria, epic boundaries",
    "scout": "read-only codebase investigation",
}

MEET_ROLE_SETS = {
    "planning": ["planner", "po", "architect"],
    "building": ["planner", "architect", "reviewer", "tester", "scout"],
    "review feedback open": ["reviewer", "architect", "planner", "scout"],
    "architecture feedback open": ["architect", "planner", "reviewer", "scout"],
    "testing": ["tester", "planner", "architect", "reviewer", "scout"],
    "done / retro complete": ["reviewer", "tester", "planner"],
}

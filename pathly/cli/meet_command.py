"""Meet command orchestration for the candidate CLI."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

from .agents import TextAgent
from .constants import (
    MEET_ALLOWED_ROLES,
    MEET_ROLE_SETS,
    PLAN_WRITE_TOOLS,
    PROMOTION_TARGET_RE,
    READ_ONLY_TOOLS,
)
from .helpers import prompt_choice, return_route_for_state
from .menus import MenuPrinter
from .plans import PlanRepository


class MeetCommand:
    def __init__(self, plans: PlanRepository, menu: MenuPrinter, agent: TextAgent):
        self.plans = plans
        self.menu = menu
        self.agent = agent

    def run(self, args: argparse.Namespace) -> int:
        plan = self.plans.select(args.feature)
        if plan is None:
            print("meet requires an active feature plan. Start a feature first, then run meet again.")
            return 1
        if not shutil.which("claude"):
            print("meet requires the claude CLI for read-only role consultation.")
            return 1

        feature = plan.name
        state = self.plans.infer_meet_state(plan)
        roles = list(MEET_ROLE_SETS.get(state, ["planner", "architect", "reviewer", "tester", "scout"]))
        role = args.role.lower() if args.role else self._choose_role(feature, state, roles)
        if role is None:
            return 0
        if role not in roles:
            print(f"Role '{role}' is not available for meet in state: {state}")
            return 1

        question = self._question(args.question, role)
        if not question:
            print("meet requires a non-empty question.")
            return 1

        note_path = self._consult_note_path(plan, role)
        answer = self.agent.run(
            self._meet_prompt(feature, role, question, note_path),
            cwd=self.plans.root,
            allowed_tools=READ_ONLY_TOOLS,
        )
        note_path.write_text(answer + "\n", encoding="utf-8")

        promotion_target = self._parse_promotion_target(answer)
        self._print_next_actions(note_path, feature, state, promotion_target)
        return self._handle_next_choice(args.next, feature, state, note_path)

    def _choose_role(self, feature: str, state: str, roles: list[str]) -> str | None:
        self.menu.meet(feature, state, roles)
        choice = prompt_choice("", [str(i) for i in range(1, len(roles) + 2)])
        if choice == str(len(roles) + 1):
            print("Use `pathly help` to see the full command reference.")
            return None
        return roles[int(choice) - 1]

    def _question(self, raw: str | None, role: str) -> str:
        question = raw.strip() if raw else ""
        if question:
            return question
        return input(f"What is the one question you want to ask {role}? ").strip()

    def _consult_note_path(self, plan: Path, role: str) -> Path:
        consults = plan / "consults"
        consults.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return consults / f"{timestamp}-{role}.md"

    def _parse_promotion_target(self, answer: str) -> str:
        match = PROMOTION_TARGET_RE.search(answer)
        if not match:
            return "none"
        value = match.group(1).strip().lower()
        return value if value in {"none", "planner", "architect"} else "none"

    def _print_next_actions(
        self,
        note_path: Path,
        feature: str,
        state: str,
        promotion_target: str,
    ) -> None:
        print(f"Meet note written: {note_path}")
        print(f"Suggested promotion target: {promotion_target}")
        print()
        print("What do you want to do next?")
        print()
        print(f"[1] Return to {return_route_for_state(feature, state)}")
        print("[2] Promote to planner update")
        print("[3] Promote to architecture update")
        print("[4] Ask another meet question")
        print("[5] See all commands")
        print()

    def _handle_next_choice(
        self,
        raw_choice: str | None,
        feature: str,
        state: str,
        note_path: Path,
    ) -> int:
        choice = raw_choice.lower() if raw_choice else prompt_choice("Reply with 1-5:", ["1", "2", "3", "4", "5"])
        if choice in {"1", "return"}:
            print(f"Return route: {return_route_for_state(feature, state)}")
            return 0
        if choice in {"2", "planner"}:
            print(self.agent.run(
                self._promotion_prompt(feature, "planner", note_path),
                cwd=self.plans.root,
                allowed_tools=PLAN_WRITE_TOOLS,
            ))
            return 0
        if choice in {"3", "architect"}:
            print(self.agent.run(
                self._promotion_prompt(feature, "architect", note_path),
                cwd=self.plans.root,
                allowed_tools=PLAN_WRITE_TOOLS,
            ))
            return 0
        if choice in {"4", "another"}:
            follow_up = argparse.Namespace(feature=feature, role=None, question=None, next=None)
            return self.run(follow_up)
        print("Use `pathly help` to see the full command reference.")
        return 0

    def _meet_prompt(self, feature: str, role: str, question: str, note_path: Path) -> str:
        role_brief = MEET_ALLOWED_ROLES[role]
        return f"""You are acting as Pathly's {role} advisor for the active feature '{feature}'.

This is a read-only consultation. You may read the project and spawn read-only subagents if needed, but you must not edit code, edit plan files, delete feedback files, or claim the workflow has advanced.

Question: {question}

Focus area: {role_brief}

Answer in this exact markdown shape:
# Meet Note - {role} - {feature}

## Question
{question}

## Answer
<direct answer>

## Evidence
- <file, pattern, or reason 1>
- <file, pattern, or reason 2>

## Recommendation
<what the user should do next>

## Promotion Target
<none|planner|architect>

Choose planner only if the answer should change stories, acceptance criteria, ordering, or task decomposition.
Choose architect only if the answer should change design, contracts, layers, rollback, or integration shape.
Choose none if the answer is advisory only.

Do not wrap the answer in code fences. The note will be written to {note_path} by the CLI runtime."""

    def _promotion_prompt(self, feature: str, role: str, note_path: Path) -> str:
        if role == "planner":
            return (
                f"Read {note_path}. Update only the plan files directly affected by the consult note in plans/{feature}/. "
                "You may edit USER_STORIES.md, IMPLEMENTATION_PLAN.md, PROGRESS.md, and CONVERSATION_PROMPTS.md if warranted. "
                "Do not edit source code. Report exactly what changed."
            )
        return (
            f"Read {note_path}. Update only architecture-related plan files directly affected by the consult note in plans/{feature}/. "
            "You may edit ARCHITECTURE_PROPOSAL.md, FLOW_DIAGRAM.md, or IMPLEMENTATION_PLAN.md if warranted. "
            "Do not edit source code. Report exactly what changed."
        )

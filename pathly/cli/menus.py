"""Console menu rendering for the candidate CLI."""

from __future__ import annotations

from pathlib import Path

from .constants import MEET_ALLOWED_ROLES


class MenuPrinter:
    def banner(self, lines: list[str]) -> None:
        rule = "=" * 43
        print(rule)
        for line in lines:
            print(f"  {line}")
        print(rule)

    def no_feature(self) -> None:
        self.banner(["Pathly", "No active feature found"])
        print()
        print("  What do you want to do?")
        print()
        print("  [1] Brainstorm/refine an unclear idea       -> storm")
        print("  [2] Describe what you want (plain English)  -> director")
        print("  [3] Start a new feature (full pipeline)     -> team-flow")
        print("  [4] Start a new feature with a PRD/BMAD file")
        print("  [5] See all commands")
        print()
        print("Reply with 1, 2, 3, 4, or 5:")

    def build_done(self, feature: str, rigor: str) -> None:
        self.banner([f"{feature} - All conversations complete", f"Rigor: {rigor}"])
        print()
        print("  What do you want to do?")
        print()
        print("  [1] Run tests                 -> tester verifies all ACs")
        print("  [2] Run tests + retro         -> full finish")
        print(f"  [3] Write retro only          -> retro {feature}")
        print("  [4] See all commands")
        print()
        print("Reply with 1-4:")

    def plan_done(self, feature: str, rigor: str, done: int, remaining: int) -> None:
        self.banner(
            [
                f"{feature} - Plan ready",
                f"Conv: {done} done . {remaining} remaining",
                f"Rigor: {rigor}",
            ]
        )
        print()
        print("  What do you want to do?")
        print()
        print("  [1] Continue building         -> next TODO conversation")
        print("  [2] Run full pipeline         -> build + review + test + retro")
        print("  [3] Run full pipeline (fast)  -> no pause points")
        print("  [4] Review current code       -> review")
        print("  [5] Meet a role               -> meet <feature>")
        print("  [6] Change rigor              -> see options")
        print("  [7] See all commands")
        print()
        print("Reply with 1-7:")

    def feedback(self, feature: str, rigor: str, plan: Path) -> None:
        self.banner([f"{feature} - Open feedback requires action", f"Rigor: {rigor}"])
        print()
        print("  Open files:")
        for path in sorted((plan / "feedback").iterdir()):
            if path.is_file():
                print(f"    {path.name}")
        print()
        print("  What do you want to do?")
        print()
        print("  [1] Resume pipeline (routes to correct agent automatically)")
        print("  [2] See the feedback file contents")
        print("  [3] See all commands")
        print()
        print("Reply with 1, 2, or 3:")

    def retro_done(self, feature: str, rigor: str) -> None:
        self.banner([f"{feature} - DONE", "RETRO.md written", f"Rigor: {rigor}"])
        print()
        print("  What do you want to do?")
        print()
        print("  [1] Archive this feature      -> moves to plans/.archive/")
        print("  [2] Promote lessons           -> lessons")
        print("  [3] Start next feature        -> team-flow <new-feature>")
        print("  [4] Read the retro            -> show RETRO.md")
        print("  [5] See all commands")
        print()
        print("Reply with 1-5:")

    def meet(self, feature: str, state: str, roles: list[str]) -> None:
        self.banner([f"meet - {feature}", f"State: {state}"])
        print()
        print("  Pick a role to consult:")
        print()
        for index, role in enumerate(roles, start=1):
            print(f"  [{index}] {role:<12} -> {MEET_ALLOWED_ROLES[role]}")
        print(f"  [{len(roles) + 1}] See all commands")
        print()
        print(f"Reply with 1-{len(roles) + 1}:")

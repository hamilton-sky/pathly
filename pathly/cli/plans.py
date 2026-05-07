"""Plan filesystem queries and mutations for the candidate CLI."""

from __future__ import annotations

from pathlib import Path

from constants import CORE_PLAN_FILES, STANDARD_PLAN_FILES


class PlanRepository:
    def __init__(self, root: Path):
        self.root = root

    @property
    def plans_root(self) -> Path:
        return self.root / "plans"

    def create_core_plan(self, feature: str, *, force: bool = False) -> Path:
        plan_dir = self.plans_root / feature
        plan_dir.mkdir(parents=True, exist_ok=True)
        for name, content in CORE_PLAN_FILES.items():
            path = plan_dir / name
            if force or not path.exists():
                path.write_text(content, encoding="utf-8")
        return plan_dir

    def select(self, feature: str | None) -> Path | None:
        if feature:
            plan = self.plans_root / feature
            return plan if plan.exists() else None
        plans = self.list_active()
        return plans[0] if plans else None

    def list_active(self) -> list[Path]:
        if not self.plans_root.exists():
            return []
        plans = [
            path
            for path in self.plans_root.iterdir()
            if path.is_dir() and path.name != ".archive"
        ]
        return sorted(plans, key=lambda path: path.stat().st_mtime, reverse=True)

    def infer_rigor(self, plan: Path | None) -> str:
        if plan is None or not plan.exists():
            return "unknown"
        if (plan / "STATE.json").exists() and (plan / "EVENTS.jsonl").exists():
            return "strict"

        files = {path.name for path in plan.iterdir() if path.is_file()}
        return "standard" if STANDARD_PLAN_FILES <= files else "lite"

    def progress_counts(self, plan: Path) -> tuple[int, int, int]:
        progress = plan / "PROGRESS.md"
        if not progress.exists():
            return 0, 0, 0

        done = todo = active = 0
        for line in progress.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith("|") or "---" in stripped or "Conversation" in stripped:
                continue

            cells = [cell.strip().lower() for cell in stripped.strip("|").split("|")]
            if len(cells) < 2:
                continue

            status = cells[-1]
            if status in {"done", "complete", "completed"}:
                done += 1
            elif status in {"in_progress", "in progress", "active", "building"}:
                active += 1
            elif status:
                todo += 1
        return done, todo, active

    def has_open_feedback(self, plan: Path) -> bool:
        feedback = plan / "feedback"
        return feedback.exists() and any(path.is_file() for path in feedback.iterdir())

    def infer_meet_state(self, plan: Path) -> str:
        feedback = plan / "feedback"
        if feedback.exists():
            files = {path.name for path in feedback.iterdir() if path.is_file()}
            if "ARCH_FEEDBACK.md" in files or "DESIGN_QUESTIONS.md" in files:
                return "architecture feedback open"
            if files:
                return "review feedback open"
        if (plan / "RETRO.md").exists():
            return "done / retro complete"
        done, todo, active = self.progress_counts(plan)
        if active or todo:
            return "building"
        if done:
            return "testing"
        return "planning"

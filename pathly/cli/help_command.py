"""Help command orchestration for the candidate CLI."""

from __future__ import annotations

from .menus import MenuPrinter
from .plans import PlanRepository


class HelpCommand:
    def __init__(self, plans: PlanRepository, menu: MenuPrinter):
        self.plans = plans
        self.menu = menu

    def run(self, feature: str | None) -> int:
        plans = self.plans.list_active()
        if not plans:
            self.menu.no_feature()
            return 0

        plan = self.plans.root / "plans" / feature if feature else plans[0]
        if not plan.exists():
            self.menu.no_feature()
            return 0

        rigor = self.plans.infer_rigor(plan)
        if self.plans.has_open_feedback(plan):
            self.menu.feedback(plan.name, rigor, plan)
            return 0
        if (plan / "RETRO.md").exists():
            self.menu.retro_done(plan.name, rigor)
            return 0

        done, todo, active = self.plans.progress_counts(plan)
        remaining = todo + active
        if remaining:
            self.menu.plan_done(plan.name, rigor, done, remaining)
            return 0

        self.menu.build_done(plan.name, rigor)
        return 0

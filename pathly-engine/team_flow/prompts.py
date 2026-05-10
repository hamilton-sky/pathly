"""Prompt construction for the candidate team-flow runtime."""

from __future__ import annotations


class PromptFactory:
    def __init__(self, feature: str):
        self.feature = feature

    def storm(self) -> str:
        return f"/storm {self.feature}"

    def plan(self) -> str:
        return f"/plan {self.feature}"

    def build(self) -> str:
        return f"/build {self.feature} auto"

    def retro(self) -> str:
        return f"/retro {self.feature}"

    def review(self) -> str:
        return (
            f"You are an adversarial reviewer for the {self.feature} feature.\n\n"
            "Run: git diff HEAD -- . ':(exclude)plans/'\n"
            "Review changes against:\n"
            f"  - plans/{self.feature}/ARCHITECTURE_PROPOSAL.md if present\n"
            f"  - plans/{self.feature}/IMPLEMENTATION_PLAN.md\n"
            "  - .claude/rules/ (if present)\n\n"
            f"Architectural violations -> write plans/{self.feature}/feedback/ARCH_FEEDBACK.md:\n"
            "  [ARCH] <file>:<line> - <violation> - <what it should be>\n\n"
            f"Implementation violations -> write plans/{self.feature}/feedback/REVIEW_FAILURES.md:\n"
            "  [IMPL] <file>:<line> - <violation> - <fix required>\n\n"
            "If no violations: report PASS. Do NOT write any feedback files."
        )

    def fix_arch(self) -> str:
        return (
            f"Read plans/{self.feature}/feedback/ARCH_FEEDBACK.md.\n"
            "Redesign the affected architecture to resolve each [ARCH] item.\n"
            f"Update plans/{self.feature}/ARCHITECTURE_PROPOSAL.md.\n"
            f"If conv scopes need updating, update plans/{self.feature}/IMPLEMENTATION_PLAN.md.\n"
            f"Delete plans/{self.feature}/feedback/ARCH_FEEDBACK.md when resolved.\n"
            "Report what changed."
        )

    def fix_review(self) -> str:
        return (
            f"Read plans/{self.feature}/feedback/REVIEW_FAILURES.md.\n"
            "Step 1 - Apply [AUTO_FIX] patches first, if any.\n"
            "Step 2 - Fix remaining regular violations exactly as described.\n"
            "Do not change anything outside the listed violations.\n"
            f"Delete plans/{self.feature}/feedback/REVIEW_FAILURES.md when all items resolved."
        )

    def fix_design(self) -> str:
        return (
            f"Read plans/{self.feature}/feedback/DESIGN_QUESTIONS.md.\n"
            f"Resolve each [ARCH] question - update plans/{self.feature}/ARCHITECTURE_PROPOSAL.md.\n"
            f"Delete plans/{self.feature}/feedback/DESIGN_QUESTIONS.md when resolved."
        )

    def fix_impl_questions(self) -> str:
        return (
            f"Read plans/{self.feature}/feedback/IMPL_QUESTIONS.md.\n"
            f"Answer each [REQ] question - clarify in plans/{self.feature}/USER_STORIES.md "
            f"or plans/{self.feature}/CONVERSATION_PROMPTS.md.\n"
            f"Delete plans/{self.feature}/feedback/IMPL_QUESTIONS.md when resolved."
        )

    def test(self) -> str:
        return (
            f"You are a tester verifying the {self.feature} feature.\n\n"
            f"Read plans/{self.feature}/USER_STORIES.md.\n"
            "For each acceptance criterion: PASS / FAIL / NOT COVERED.\n"
            "Run verify commands from CONVERSATION_PROMPTS.md where available.\n\n"
            "Print: | Criterion | Status | Notes |\n\n"
            f"Any FAIL/NOT COVERED -> write plans/{self.feature}/feedback/TEST_FAILURES.md:\n"
            "  [TEST-FAIL] <criterion> - <what is wrong> - <what needs to change>\n\n"
            "All PASS -> report PASS. Do NOT write TEST_FAILURES.md."
        )

    def fix_tests(self) -> str:
        return (
            f"Read plans/{self.feature}/feedback/TEST_FAILURES.md.\n"
            "Fix each [TEST-FAIL] item so the criterion is satisfied.\n"
            "Do not change anything beyond what is needed to pass the listed criteria.\n"
            f"Delete plans/{self.feature}/feedback/TEST_FAILURES.md when resolved."
        )

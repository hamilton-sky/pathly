"""Engine side of the feedback protocol contract.

Verifies that every FeedbackFile constant in orchestrator/constants.py
exactly matches the names declared in protocol_contract.yaml.

When pathly-engine and pathly-adapters live in separate repos, each repo
tests its own half of the contract against its own copy of protocol_contract.yaml.
If the two YAML files drift apart, the tests in the OTHER repo will catch it.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

CONTRACT = yaml.safe_load(
    (Path(__file__).parent.parent / "protocol_contract.yaml").read_text(encoding="utf-8")
)
CONTRACT_FILES: set[str] = set(CONTRACT["feedback_files"])


def _feedback_constants() -> set[str]:
    from orchestrator.constants import FeedbackFile
    return {
        v for k, v in vars(FeedbackFile).items()
        if not k.startswith("_") and isinstance(v, str)
    }


class TestFeedbackProtocolEngine:
    def test_constants_match_contract_exactly(self):
        """FeedbackFile constants must be exactly the set declared in protocol_contract.yaml."""
        constants = _feedback_constants()
        extra = constants - CONTRACT_FILES
        missing = CONTRACT_FILES - constants

        msgs = []
        if extra:
            msgs.append(
                "Constants in FeedbackFile but NOT in protocol_contract.yaml "
                "(add to contract or remove constant):\n"
                + "\n".join(f"  + {n}" for n in sorted(extra))
            )
        if missing:
            msgs.append(
                "Names in protocol_contract.yaml but NOT in FeedbackFile "
                "(add constant or remove from contract):\n"
                + "\n".join(f"  - {n}" for n in sorted(missing))
            )
        assert not msgs, "\n\n".join(msgs)

    def test_all_constants_are_uppercase_md(self):
        """All FeedbackFile constants must be UPPER_CASE and end with .md."""
        bad = {n for n in _feedback_constants() if not n.endswith(".md") or n[:-3] != n[:-3].upper()}
        assert not bad, (
            "FeedbackFile constants that are not UPPER_CASE.md:\n"
            + "\n".join(f"  {n}" for n in sorted(bad))
        )

    def test_contract_file_is_valid_yaml(self):
        """protocol_contract.yaml must parse and contain a feedback_files list."""
        assert isinstance(CONTRACT_FILES, set) and len(CONTRACT_FILES) > 0, (
            "protocol_contract.yaml parsed but 'feedback_files' is empty or missing"
        )

"""Feedback protocol contract — SPLIT INTO PER-REPO TESTS.

This monorepo root test has been replaced by two independent tests,
one in each package, each tested against its own protocol_contract.yaml:

  pathly-engine/tests/test_feedback_protocol.py
    → verifies FeedbackFile constants match protocol_contract.yaml

  pathly-adapters/tests/test_feedback_protocol.py
    → verifies skill/agent Markdown files reference exactly the names
      in protocol_contract.yaml

When running the monorepo as a whole you can still run both:
  pytest pathly-engine/tests/test_feedback_protocol.py
  pytest pathly-adapters/tests/test_feedback_protocol.py

To verify the two protocol_contract.yaml files are identical across repos:
  diff pathly-engine/protocol_contract.yaml pathly-adapters/protocol_contract.yaml
"""

# engine-hardening — Happy Flow

## Ideal journey

1. **Conv 1** — developer runs `pytest` before and after; all existing tests pass; two new runner tests and one sanitization test appear green.

2. **Conv 2** — `_run_agent` has a clear docstring and a log line for non-required failures; two new tests cover each branch; no existing test breaks.

3. **Conv 3** — `test_e2e.py` creates a driver, runs it with a mock runner, finishes without raising, and asserts EVENTS.jsonl + STATE.json are consistent; test is green.

4. **Conv 4** — three new FSM tests for two-level blocking and full unwind are added to `test_fsm.py`; all pass green; no reducer source changes needed.

After all 4 conversations, the full test suite (`pytest pathly-engine/tests/ -x -q`) passes.

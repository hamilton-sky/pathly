"""Named constants for all protocol-level strings in the FSM orchestrator."""


class FSMState:
    IDLE               = "IDLE"
    PO_DISCUSSING      = "PO_DISCUSSING"    # PO Q&A phase (orchestrator-driven, option [5])
    PO_PAUSED          = "PO_PAUSED"        # PO done, waiting to proceed to architect storm
    EXPLORING          = "EXPLORING"        # Explorer maps codebase (option [4])
    EXPLORE_PAUSED     = "EXPLORE_PAUSED"   # Explorer done, waiting for A/B/C choice
    STORMING           = "STORMING"
    STORM_PAUSED       = "STORM_PAUSED"
    PLANNING           = "PLANNING"
    PLAN_PAUSED        = "PLAN_PAUSED"
    BUILDING           = "BUILDING"
    REVIEWING          = "REVIEWING"
    IMPLEMENT_PAUSED   = "IMPLEMENT_PAUSED"
    TESTING            = "TESTING"
    TEST_PAUSED        = "TEST_PAUSED"
    RETRO              = "RETRO"
    BLOCKED_ON_FEEDBACK = "BLOCKED_ON_FEEDBACK"
    BLOCKED_ON_HUMAN   = "BLOCKED_ON_HUMAN"
    DONE               = "DONE"


class Agent:
    ARCHITECT      = "architect"
    PLANNER        = "planner"
    BUILDER        = "builder"
    REVIEWER       = "reviewer"
    TESTER         = "tester"
    QUICK          = "quick"
    EXPLORER       = "explorer"        # codebase exploration (subagent_type: Explore)
    PO             = "po"              # product owner discussion (option [5] phase 1)
    DIRECTOR       = "director"
    WEB_RESEARCHER = "web-researcher"  # sub-agent spawned inline by architect/planner; transparent to FSM


MAX_RETRIES = 2  # max feedback-loop cycles before escalating to BLOCKED_ON_HUMAN


class FeedbackFile:
    REVIEW_FAILURES  = "REVIEW_FAILURES.md"
    HUMAN_QUESTIONS  = "HUMAN_QUESTIONS.md"
    IMPL_QUESTIONS   = "IMPL_QUESTIONS.md"
    ARCH_FEEDBACK    = "ARCH_FEEDBACK.md"
    DESIGN_QUESTIONS = "DESIGN_QUESTIONS.md"
    TEST_FAILURES    = "TEST_FAILURES.md"


class Events:
    COMMAND           = "COMMAND"
    AGENT_DONE        = "AGENT_DONE"
    FILE_CREATED      = "FILE_CREATED"
    FILE_DELETED      = "FILE_DELETED"
    HUMAN_RESPONSE    = "HUMAN_RESPONSE"    
    NO_DIFF_DETECTED  = "NO_DIFF_DETECTED"
    IMPLEMENT_COMPLETE = "IMPLEMENT_COMPLETE"
    STATE_TRANSITION    = "STATE_TRANSITION"
    SYSTEM_EVENT        = "SYSTEM_EVENT"

    
class Mode:
    FAST        = "fast"
    INTERACTIVE = "interactive"


class Rigor:
    NANO     = "nano"
    LITE     = "lite"
    STANDARD = "standard"
    STRICT   = "strict"

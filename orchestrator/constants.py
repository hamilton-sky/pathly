"""Named constants for all protocol-level strings in the FSM orchestrator."""


class FSMState:
    IDLE               = "IDLE"
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
    ARCHITECT = "architect"
    PLANNER   = "planner"
    BUILDER   = "builder"
    REVIEWER  = "reviewer"
    TESTER    = "tester"
    QUICK     = "quick"


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
    LITE     = "lite"
    STANDARD = "standard"
    STRICT   = "strict"

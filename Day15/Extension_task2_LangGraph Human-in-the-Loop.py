# pip install langgraph

from typing import TypedDict, Optional
from enum import Enum

from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ESCALATE = "escalate"


class LoanState(TypedDict):
    application_id: str
    loan_amount: float
    applicant_summary: str
    ai_recommendation: str
    risk_score: float
    review_required: bool
    final_decision: Optional[str]
    reviewer_id: Optional[str]
    review_notes: Optional[str]


HIGH_VALUE_THRESHOLD = 1_000_000   # INR 10 lakhs
HIGH_RISK_SCORE = 0.7


def route_loan(state: LoanState):
    """Decide whether loan needs human review."""
    if state["loan_amount"] >= HIGH_VALUE_THRESHOLD or state["risk_score"] >= HIGH_RISK_SCORE:
        return "human_review"

    return "auto_process"


def auto_process(state: LoanState):
    """Automatically approve low-risk loan."""
    return {
        "review_required": False,
        "final_decision": "auto_approved",
        "reviewer_id": None,
        "review_notes": "Auto processed by AI workflow"
    }


def human_review(state: LoanState):
    """Pause workflow for human decision."""

    human_input = interrupt({
        "message": "Human review required",
        "application_id": state["application_id"],
        "loan_amount": state["loan_amount"],
        "risk_score": state["risk_score"],
        "applicant_summary": state["applicant_summary"],
        "ai_recommendation": state["ai_recommendation"],
        "allowed_decisions": ["approve", "reject", "escalate"]
    })

    return {
        "review_required": True,
        "final_decision": human_input["decision"],
        "reviewer_id": human_input["reviewer_id"],
        "review_notes": human_input.get("notes", "")
    }


# Build LangGraph
builder = StateGraph(LoanState)

builder.add_node("auto_process", auto_process)
builder.add_node("human_review", human_review)

builder.add_conditional_edges(
    START,
    route_loan,
    {
        "auto_process": "auto_process",
        "human_review": "human_review"
    }
)

builder.add_edge("auto_process", END)
builder.add_edge("human_review", END)

checkpointer = InMemorySaver()
app = builder.compile(checkpointer=checkpointer)


# -----------------------------
# Test loans
# -----------------------------

test_loan = {
    "application_id": "APP100302",
    "loan_amount": 1_500_000,
    "applicant_summary": "Self-employed, credit score 660, DTI 45%",
    "ai_recommendation": "Borderline",
    "risk_score": 0.62,
    "review_required": False,
    "final_decision": None,
    "reviewer_id": None,
    "review_notes": None
}

config = {
    "configurable": {
        "thread_id": "loan_APP100302"
    }
}

print("\n🔄 Starting LangGraph HITL workflow")

result = app.invoke(test_loan, config=config)

print("\n⏸️ Graph paused for human review:")
print(result)


# -----------------------------
# Resume after human review
# -----------------------------

human_decision = {
    "decision": ReviewDecision.APPROVE.value,
    "reviewer_id": "UNDERWRITER_001",
    "notes": "Manual review complete. Income documents verified."
}

final_result = app.invoke(
    Command(resume=human_decision),
    config=config
)

print("\n✅ Final result after human review:")
print(final_result)
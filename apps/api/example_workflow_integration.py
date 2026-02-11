"""Example: How to use the rules engine in a LangGraph workflow node.

This is a reference implementation showing how to integrate the rules system
into `apps/api/app/langgraph/workflow.py`.
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph

from app.rules.engine import decide_project_rules
from app.rules.global_rules import GLOBAL_RULES
from app.rules.types import ProjectRuleSet, UserRule


# ---------------------------------------------------------------------------
# Example state definition
# ---------------------------------------------------------------------------


class WorkflowState(TypedDict, total=False):
    """Simplified LangGraph workflow state."""

    user_input: str
    user_rules_raw: list[dict]  # Raw user rules from frontend/upstream
    project_rules: dict  # Adjudicated rules (serialized ProjectRuleSet)
    current_module: str | None
    # ... other state fields ...


# ---------------------------------------------------------------------------
# Example node: rules adjudication
# ---------------------------------------------------------------------------


def adjudicate_rules_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node that processes user rules against global rules.

    This node:
    1. Deserializes user rules from state
    2. Runs adjudication
    3. Stores the result back in state (as dict for JSON serialization)

    The engineer agent can then read `state["project_rules"]` to know what
    rules to enforce.
    """
    # Parse user rules from upstream (e.g. from frontend or planner agent)
    user_rules_list = []
    for raw_rule in state.get("user_rules_raw", []):
        user_rules_list.append(UserRule.model_validate(raw_rule))

    # Run adjudication
    project_rules = decide_project_rules(GLOBAL_RULES, user_rules_list)

    # Store as dict (JSON-serializable for LangGraph persistence)
    return {
        **state,
        "project_rules": project_rules.model_dump(),
    }


def engineer_agent_node(state: WorkflowState) -> WorkflowState:
    """Example engineer agent that consumes the adjudicated rules.

    The agent can read:
    - Global rules (always enforced)
    - Accepted user rules (grouped by project/module)
    - Rejected user rules (for user feedback)
    """
    # Reconstruct ProjectRuleSet from dict
    rules_dict = state.get("project_rules", {})
    if rules_dict:
        project_rules = ProjectRuleSet.model_validate(rules_dict)

        # Access global rules (always apply)
        for gr in project_rules.global_rules:
            print(f"[GLOBAL] {gr.id}: {gr.title}")

        # Access module-specific rules if working on a module
        current_module = state.get("current_module")
        if current_module:
            for module_set in project_rules.module_rule_sets:
                if module_set.module == current_module:
                    for rule in module_set.rules:
                        print(f"[MODULE:{current_module}] {rule.id}: {rule.title}")

        # Access project-wide user rules
        for decision in project_rules.accepted_user_rules:
            if decision.rule.scope.value == "project":
                print(f"[PROJECT] {decision.rule.id}: {decision.rule.title}")

    # ... do actual engineering work ...

    return state


# ---------------------------------------------------------------------------
# Example workflow graph construction
# ---------------------------------------------------------------------------


def build_example_workflow() -> StateGraph:
    """Example workflow showing rules integration."""
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("adjudicate_rules", adjudicate_rules_node)
    workflow.add_node("engineer_agent", engineer_agent_node)

    # Define edges
    workflow.set_entry_point("adjudicate_rules")
    workflow.add_edge("adjudicate_rules", "engineer_agent")
    workflow.set_finish_point("engineer_agent")

    return workflow


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Simulate incoming user rules (from frontend)
    example_user_rules = [
        {
            "id": "U-001",
            "title": "Use type hints everywhere",
            "description": "All public functions must have type annotations.",
            "severity": "should",
            "scope": "project",
        },
        {
            "id": "U-002",
            "title": "Prefer SQLAlchemy 2.0 style",
            "severity": "should",
            "scope": "module",
            "module": "db",
        },
        # This will be rejected (conflicts with G-001)
        {
            "id": "U-003",
            "title": "No arbitrary code execution",
            "severity": "may",
            "scope": "project",
        },
    ]

    # Simulate workflow execution
    initial_state: WorkflowState = {
        "user_input": "Build a new feature",
        "user_rules_raw": example_user_rules,
        "current_module": "db",
    }

    # Run adjudication node
    state_after_adjudication = adjudicate_rules_node(initial_state)

    # Reconstruct to inspect
    project_rules = ProjectRuleSet.model_validate(state_after_adjudication["project_rules"])

    print("=" * 70)
    print("Adjudication Results:")
    print("=" * 70)
    print(f"Global rules: {len(project_rules.global_rules)}")
    print(f"Accepted user rules: {len(project_rules.accepted_user_rules)}")
    print(f"Rejected user rules: {len(project_rules.rejected_user_rules)}")

    if project_rules.rejected_user_rules:
        print("\nRejected:")
        for dec in project_rules.rejected_user_rules:
            print(f"  - {dec.rule.id}: {dec.rejected_reason}")

    print("\n" + "=" * 70)
    print("Engineer Agent Execution:")
    print("=" * 70)
    engineer_agent_node(state_after_adjudication)

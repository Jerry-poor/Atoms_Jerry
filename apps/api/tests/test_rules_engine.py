"""Tests for the rules adjudication engine.

Coverage targets:
1. Conflict rejection (by ID and by title)
2. Non-conflicting absorption
3. Scope annotation (project / module)
4. JSON round-trip stability
"""

from __future__ import annotations

import json

import pytest

from app.rules.engine import decide_project_rules
from app.rules.types import (
    GlobalRule,
    ModuleRuleSet,
    ProjectRuleSet,
    RuleDecision,
    Scope,
    Severity,
    UserRule,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_global_rules() -> list[GlobalRule]:
    return [
        GlobalRule(
            id="G-001",
            title="No arbitrary code execution",
            description="Do not use eval/exec.",
            severity=Severity.MUST,
            scope=Scope.PROJECT,
        ),
        GlobalRule(
            id="G-002",
            title="Respect license compatibility",
            description="Only use compatible licenses.",
            severity=Severity.MUST,
            scope=Scope.PROJECT,
        ),
        GlobalRule(
            id="G-005",
            title="Module test coverage required",
            description="Every new module needs tests.",
            severity=Severity.SHOULD,
            scope=Scope.MODULE,
        ),
    ]


# ---------------------------------------------------------------------------
# 1. Conflict rejection
# ---------------------------------------------------------------------------


class TestConflictRejection:
    """User rules that collide with global rules must be rejected."""

    def test_reject_by_id_collision(self, sample_global_rules: list[GlobalRule]) -> None:
        """If a user rule reuses a global rule ID, it is rejected."""
        user_rules = [
            UserRule(
                id="G-001",  # Same ID as global rule
                title="Allow eval for data transforms",
                severity=Severity.SHOULD,
                scope=Scope.PROJECT,
            ),
        ]
        result = decide_project_rules(sample_global_rules, user_rules)

        assert len(result.rejected_user_rules) == 1
        assert len(result.accepted_user_rules) == 0

        decision = result.rejected_user_rules[0]
        assert decision.accepted is False
        assert decision.conflicting_global_rule_id == "G-001"
        assert "G-001" in (decision.rejected_reason or "")

    def test_reject_by_title_collision(self, sample_global_rules: list[GlobalRule]) -> None:
        """If a user rule has the same title (case-insensitive), it is rejected."""
        user_rules = [
            UserRule(
                id="U-100",
                title="no arbitrary code execution",  # same title, lowercase
                severity=Severity.MAY,
                scope=Scope.PROJECT,
            ),
        ]
        result = decide_project_rules(sample_global_rules, user_rules)

        assert len(result.rejected_user_rules) == 1
        decision = result.rejected_user_rules[0]
        assert decision.accepted is False
        assert decision.conflicting_global_rule_id == "G-001"

    def test_rejected_reason_is_human_readable(self, sample_global_rules: list[GlobalRule]) -> None:
        user_rules = [
            UserRule(id="G-002", title="Something", scope=Scope.PROJECT),
        ]
        result = decide_project_rules(sample_global_rules, user_rules)
        reason = result.rejected_user_rules[0].rejected_reason
        assert reason is not None
        assert "global rules take precedence" in reason.lower()


# ---------------------------------------------------------------------------
# 2. Non-conflicting absorption
# ---------------------------------------------------------------------------


class TestAcceptance:
    """User rules that do not conflict are accepted."""

    def test_accept_non_conflicting_rule(self, sample_global_rules: list[GlobalRule]) -> None:
        user_rules = [
            UserRule(
                id="U-001",
                title="Use type hints everywhere",
                description="All public functions must have type annotations.",
                severity=Severity.SHOULD,
                scope=Scope.PROJECT,
            ),
        ]
        result = decide_project_rules(sample_global_rules, user_rules)

        assert len(result.accepted_user_rules) == 1
        assert len(result.rejected_user_rules) == 0

        decision = result.accepted_user_rules[0]
        assert decision.accepted is True
        assert decision.rejected_reason is None
        assert decision.conflicting_global_rule_id is None

    def test_mixed_accept_and_reject(self, sample_global_rules: list[GlobalRule]) -> None:
        """When some rules conflict and others don't, both lists are populated."""
        user_rules = [
            UserRule(id="G-001", title="Override eval", scope=Scope.PROJECT),  # conflict
            UserRule(id="U-010", title="Max function length 50 lines", scope=Scope.PROJECT),  # ok
            UserRule(id="U-011", title="Prefer composition over inheritance", scope=Scope.PROJECT),  # ok
        ]
        result = decide_project_rules(sample_global_rules, user_rules)

        assert len(result.rejected_user_rules) == 1
        assert len(result.accepted_user_rules) == 2

    def test_global_rules_always_present(self, sample_global_rules: list[GlobalRule]) -> None:
        """Global rules appear in the output regardless of user input."""
        result = decide_project_rules(sample_global_rules, [])
        assert len(result.global_rules) == len(sample_global_rules)
        assert result.global_rules == sample_global_rules


# ---------------------------------------------------------------------------
# 3. Scope annotation
# ---------------------------------------------------------------------------


class TestScopeAnnotation:
    """Accepted rules are grouped by scope in convenience fields."""

    def test_project_scope_in_project_list(self, sample_global_rules: list[GlobalRule]) -> None:
        user_rules = [
            UserRule(id="U-020", title="PEP-8 compliance", scope=Scope.PROJECT),
        ]
        result = decide_project_rules(sample_global_rules, user_rules)

        assert len(result.project_scoped_user_rules) == 1
        assert result.project_scoped_user_rules[0].id == "U-020"
        assert len(result.module_rule_sets) == 0

    def test_module_scope_in_module_rule_sets(self, sample_global_rules: list[GlobalRule]) -> None:
        user_rules = [
            UserRule(
                id="U-030",
                title="Use SQLAlchemy 2.0 style",
                scope=Scope.MODULE,
                module="db",
            ),
            UserRule(
                id="U-031",
                title="Use httpx for HTTP calls",
                scope=Scope.MODULE,
                module="services",
            ),
        ]
        result = decide_project_rules(sample_global_rules, user_rules)

        assert len(result.module_rule_sets) == 2
        modules = {mrs.module for mrs in result.module_rule_sets}
        assert modules == {"db", "services"}

        db_set = next(mrs for mrs in result.module_rule_sets if mrs.module == "db")
        assert len(db_set.rules) == 1
        assert db_set.rules[0].id == "U-030"

    def test_module_scope_without_module_field_goes_to_project(
        self, sample_global_rules: list[GlobalRule]
    ) -> None:
        """If scope is MODULE but module is None, fall back to project bucket."""
        user_rules = [
            UserRule(id="U-040", title="Orphan module rule", scope=Scope.MODULE, module=None),
        ]
        result = decide_project_rules(sample_global_rules, user_rules)

        assert len(result.module_rule_sets) == 0
        assert len(result.project_scoped_user_rules) == 1


# ---------------------------------------------------------------------------
# 4. JSON serialization stability
# ---------------------------------------------------------------------------


class TestJsonStability:
    """ProjectRuleSet must round-trip through JSON cleanly."""

    def test_model_dump_json_roundtrip(self, sample_global_rules: list[GlobalRule]) -> None:
        user_rules = [
            UserRule(id="U-050", title="Use async everywhere", scope=Scope.PROJECT),
            UserRule(id="U-051", title="Custom DB rule", scope=Scope.MODULE, module="db"),
            UserRule(id="G-001", title="Override global", scope=Scope.PROJECT),  # conflict
        ]
        result = decide_project_rules(sample_global_rules, user_rules)

        json_str = result.model_dump_json(indent=2)
        parsed = json.loads(json_str)

        # Reconstruct from dict ⇒ must produce identical object.
        reconstructed = ProjectRuleSet.model_validate(parsed)
        assert reconstructed == result

    def test_all_top_level_keys_present(self, sample_global_rules: list[GlobalRule]) -> None:
        result = decide_project_rules(sample_global_rules, [])
        data = result.model_dump()
        expected_keys = {
            "global_rules",
            "accepted_user_rules",
            "rejected_user_rules",
            "module_rule_sets",
            "project_scoped_user_rules",
        }
        assert set(data.keys()) == expected_keys

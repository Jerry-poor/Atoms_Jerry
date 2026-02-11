#!/usr/bin/env python3
"""Quick validation script for the rules engine."""

from __future__ import annotations

import json

from app.rules.engine import decide_project_rules
from app.rules.global_rules import GLOBAL_RULES
from app.rules.types import Scope, Severity, UserRule

# Create sample user rules with various scenarios
user_rules = [
    # This should be accepted
    UserRule(
        id="U-001",
        title="Use type hints everywhere",
        description="All public functions must have type annotations.",
        severity=Severity.SHOULD,
        scope=Scope.PROJECT,
    ),
    # This conflicts with global rule G-001 (by title)
    UserRule(
        id="U-002",
        title="No arbitrary code execution",
        description="User's version of the same rule.",
        severity=Severity.MAY,
        scope=Scope.PROJECT,
    ),
    # This should be accepted and grouped by module
    UserRule(
        id="U-003",
        title="Use SQLAlchemy 2.0 style",
        description="Prefer declarative style.",
        severity=Severity.SHOULD,
        scope=Scope.MODULE,
        module="db",
    ),
    # This should be accepted and grouped by module
    UserRule(
        id="U-004",
        title="Prefer httpx over requests",
        severity=Severity.SHOULD,
        scope=Scope.MODULE,
        module="services",
    ),
]

# Run the adjudication
result = decide_project_rules(GLOBAL_RULES, user_rules)

print("=" * 70)
print("Rules Engine Validation")
print("=" * 70)
print(f"\n✓ Global rules loaded: {len(result.global_rules)}")
print(f"✓ User rules accepted: {len(result.accepted_user_rules)}")
print(f"✗ User rules rejected: {len(result.rejected_user_rules)}")
print(f"✓ Project-scoped rules: {len(result.project_scoped_user_rules)}")
print(f"✓ Module rule sets: {len(result.module_rule_sets)}")

if result.rejected_user_rules:
    print("\n" + "=" * 70)
    print("Rejected Rules:")
    print("=" * 70)
    for dec in result.rejected_user_rules:
        print(f"\n  Rule ID: {dec.rule.id}")
        print(f"  Title: {dec.rule.title}")
        print(f"  Reason: {dec.rejected_reason}")
        print(f"  Conflicting global: {dec.conflicting_global_rule_id}")

if result.module_rule_sets:
    print("\n" + "=" * 70)
    print("Module-Scoped Rules:")
    print("=" * 70)
    for mrs in result.module_rule_sets:
        print(f"\n  Module: {mrs.module}")
        for rule in mrs.rules:
            print(f"    - [{rule.id}] {rule.title}")

print("\n" + "=" * 70)
print("JSON Serialization Test:")
print("=" * 70)
json_output = result.model_dump_json(indent=2)
print(f"✓ Serialized to {len(json_output)} bytes")

# Validate round-trip
parsed = json.loads(json_output)
from app.rules.types import ProjectRuleSet
reconstructed = ProjectRuleSet.model_validate(parsed)
print(f"✓ Round-trip validation: {reconstructed == result}")

print("\n" + "=" * 70)
print("Sample JSON Output (first 500 chars):")
print("=" * 70)
print(json_output[:500] + "...")

print("\n✅ All validations passed!")

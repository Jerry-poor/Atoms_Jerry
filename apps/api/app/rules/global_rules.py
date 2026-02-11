"""Built-in global rules.

These are platform-level, read-only constraints that always take precedence
over user-supplied rules.  They are intentionally kept as a plain Python list
so they are easy to version-control, review, and extend.
"""

from __future__ import annotations

from app.rules.types import GlobalRule, Scope, Severity

GLOBAL_RULES: list[GlobalRule] = [
    GlobalRule(
        id="G-001",
        title="No arbitrary code execution",
        description=(
            "Generated code must never use eval(), exec(), or equivalent "
            "dynamic-execution primitives unless explicitly sandboxed."
        ),
        severity=Severity.MUST,
        scope=Scope.PROJECT,
    ),
    GlobalRule(
        id="G-002",
        title="Respect license compatibility",
        description=(
            "All third-party dependencies introduced by the engineer agent "
            "must have licenses compatible with the project license."
        ),
        severity=Severity.MUST,
        scope=Scope.PROJECT,
    ),
    GlobalRule(
        id="G-003",
        title="No secrets in source code",
        description=(
            "API keys, passwords, tokens, and other credentials must never "
            "appear as literals in source files."
        ),
        severity=Severity.MUST,
        scope=Scope.PROJECT,
    ),
    GlobalRule(
        id="G-004",
        title="Follow project coding style",
        description=(
            "Generated code should conform to the linter and formatter "
            "configuration already present in the repository (e.g. ruff, "
            "eslint, prettier)."
        ),
        severity=Severity.SHOULD,
        scope=Scope.PROJECT,
    ),
    GlobalRule(
        id="G-005",
        title="Module test coverage required",
        description=(
            "Every new module must include at least one unit-test file "
            "covering its public interface."
        ),
        severity=Severity.SHOULD,
        scope=Scope.MODULE,
    ),
]

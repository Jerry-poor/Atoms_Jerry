"""Rule adjudication engine.

The single public entry-point is :func:`decide_project_rules`.

Priority model
--------------
* **Global rules always win.**  They are copied verbatim into the output and
  are treated as read-only.
* A user rule *conflicts* with a global rule when **both rules share the same
  ``scope``** *and* their **``id`` values match** (i.e. the user tried to
  redefine a platform rule) **or** their ``title`` values match
  (case-insensitive).
* Conflicting user rules are **rejected** with a human-readable reason.
* Non-conflicting user rules are **accepted** and sorted into project-level
  or module-level buckets.
"""

from __future__ import annotations

from collections import defaultdict

from app.rules.types import (
    GlobalRule,
    ModuleRuleSet,
    ProjectRuleSet,
    RuleDecision,
    Scope,
    UserRule,
)


def _find_conflict(user_rule: UserRule, global_rules: list[GlobalRule]) -> GlobalRule | None:
    """Return the first global rule that conflicts with *user_rule*, or ``None``."""
    for gr in global_rules:
        # Direct ID collision – user tried to override a global rule.
        if user_rule.id == gr.id:
            return gr
        # Title collision (case-insensitive) – semantically the same rule.
        if user_rule.title.strip().lower() == gr.title.strip().lower():
            return gr
    return None


def decide_project_rules(
    global_rules: list[GlobalRule],
    user_rules: list[UserRule],
) -> ProjectRuleSet:
    """Adjudicate *user_rules* against *global_rules* and return a stable
    :class:`ProjectRuleSet`.

    Parameters
    ----------
    global_rules:
        Platform-defined rules (read-only, always enforced).
    user_rules:
        Rules submitted by the user or upstream agent.

    Returns
    -------
    ProjectRuleSet
        A frozen, JSON-serializable result containing:
        - all global rules,
        - accepted / rejected user rules with reasons,
        - convenience groupings by scope.
    """
    accepted: list[RuleDecision] = []
    rejected: list[RuleDecision] = []

    for ur in user_rules:
        conflict = _find_conflict(ur, global_rules)
        if conflict is not None:
            rejected.append(
                RuleDecision(
                    rule=ur,
                    accepted=False,
                    rejected_reason=(
                        f"Conflicts with global rule '{conflict.id}' "
                        f"(\"{conflict.title}\"): global rules take precedence."
                    ),
                    conflicting_global_rule_id=conflict.id,
                )
            )
        else:
            accepted.append(
                RuleDecision(
                    rule=ur,
                    accepted=True,
                    rejected_reason=None,
                    conflicting_global_rule_id=None,
                )
            )

    # ---- Build convenience groupings ----

    project_scoped: list[UserRule] = []
    module_buckets: dict[str, list[UserRule]] = defaultdict(list)

    for dec in accepted:
        rule = dec.rule
        if rule.scope == Scope.MODULE and rule.module:
            module_buckets[rule.module].append(rule)
        else:
            project_scoped.append(rule)

    module_rule_sets = [
        ModuleRuleSet(module=mod, rules=rules)
        for mod, rules in sorted(module_buckets.items())
    ]

    return ProjectRuleSet(
        global_rules=list(global_rules),
        accepted_user_rules=accepted,
        rejected_user_rules=rejected,
        module_rule_sets=module_rule_sets,
        project_scoped_user_rules=project_scoped,
    )

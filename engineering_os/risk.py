"""Deterministic maximum-risk computation over mission and base policy."""

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Tuple

from .schema import validate_document
from .scope import PathInputError, _policy_patterns, normalize_paths, path_matches


_TIER_VALUE = {"Tier 0": 0, "Tier 1": 1, "Tier 2": 2}
_TIER_NAME = {value: name for name, value in _TIER_VALUE.items()}
_TIER_TWO_CAPABILITIES = frozenset(
    ("deploy", "cloud_mutation", "secrets", "customer_data", "spend", "cutover")
)
_CAPABILITIES = frozenset(("read", "write", "merge")) | _TIER_TWO_CAPABILITIES
_TIER_TWO_SIGNALS = frozenset((
    "methodology", "destructive", "security", "privacy", "public_claim",
    "cross_module", "cross_repository", "residual_risk",
))


@dataclass(frozen=True)
class RiskDecision:
    allowed: bool
    code: str
    declared_tier: str
    computed_tier: str
    effective_tier: str
    triggers: Tuple[str, ...] = ()


def _invalid(declared: Any, trigger: str, code: str = "RISK_INPUT_INVALID") -> RiskDecision:
    declared_name = declared if declared in _TIER_VALUE else "Tier 2"
    return RiskDecision(False, code, declared_name, "Tier 2", "Tier 2", (trigger,))


def compute_tier(
    mission: Mapping[str, Any], policy: Mapping[str, Any], changed_files: Sequence[str]
) -> RiskDecision:
    """Compute maximum supported tier; policy and evidence can only raise it."""

    if not isinstance(mission, Mapping) or not isinstance(policy, Mapping):
        return _invalid(None, "malformed-input")
    declared = mission.get("risk_tier")
    if declared not in _TIER_VALUE:
        return _invalid(declared, "invalid-declared-tier")
    capabilities = mission.get("capabilities")
    if (
        not isinstance(capabilities, list)
        or any(not isinstance(item, str) or item not in _CAPABILITIES for item in capabilities)
    ):
        return _invalid(declared, "invalid-capabilities")
    signals = mission.get("risk_signals", [])
    if (
        not isinstance(signals, list)
        or any(not isinstance(item, str) or item not in _TIER_TWO_SIGNALS for item in signals)
    ):
        return _invalid(declared, "invalid-risk-signals")
    if validate_document("mission", dict(mission)):
        return _invalid(declared, "invalid-mission-schema", "RISK_MISSION_INVALID")
    if validate_document("repository-policy", dict(policy)):
        return _invalid(declared, "invalid-policy-schema", "RISK_POLICY_INVALID")
    try:
        changed = normalize_paths(changed_files)
        tier_two_patterns, domains = _policy_patterns(policy)
    except (PathInputError, TypeError):
        return _invalid(declared, "invalid-path-or-policy")

    computed = 1
    triggers = []
    matched_domains = set()
    all_explicit_tier_zero = bool(changed)
    for path in changed:
        matching = [
            domain for domain in domains
            if any(path_matches(path, pattern) for pattern in domain["paths"])
        ]
        if not matching:
            all_explicit_tier_zero = False
        for domain in matching:
            name = domain.get("name")
            if isinstance(name, str):
                matched_domains.add(name)
            minimum = domain.get("minimum_tier")
            if minimum not in _TIER_VALUE:
                return _invalid(declared, "invalid-domain-tier")
            computed = max(computed, _TIER_VALUE[minimum])
            if minimum == "Tier 2":
                triggers.append("domain:%s" % name)
            if minimum != "Tier 0":
                all_explicit_tier_zero = False
        if any(path_matches(path, pattern) for pattern in tier_two_patterns):
            computed = 2
            triggers.append("policy-path:%s" % path)
    if all_explicit_tier_zero:
        computed = 0

    for capability in sorted(set(capabilities) & _TIER_TWO_CAPABILITIES):
        computed = 2
        triggers.append("capability:%s" % capability)

    for signal in signals:
        computed = 2
        triggers.append("signal:%s" % signal)

    if len(matched_domains) > 1:
        computed = 2
        triggers.append("cross-module")
    if mission.get("repository") != policy.get("repository"):
        computed = 2
        triggers.append("cross-repository")
    rollback = mission.get("rollback", {})
    if not isinstance(rollback, Mapping):
        return _invalid(declared, "invalid-rollback")
    if rollback.get("class") == "irreversible":
        computed = 2
        triggers.append("irreversible")

    computed_name = _TIER_NAME[computed]
    effective_name = _TIER_NAME[max(computed, _TIER_VALUE[declared])]
    if _TIER_VALUE[declared] < computed:
        return RiskDecision(
            False, "RISK_TIER_UNDER_DECLARED", declared, computed_name,
            effective_name, tuple(sorted(set(triggers))),
        )
    return RiskDecision(
        True, "RISK_TIER_ALLOWED", declared, computed_name,
        effective_name, tuple(sorted(set(triggers))),
    )

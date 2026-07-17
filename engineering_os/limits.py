"""Pure resource-limit evaluation for a mission observation."""

import math
from dataclasses import dataclass
from typing import Dict, Mapping, Tuple, Union


Number = Union[int, float]
LIMIT_NAMES = (
    "model_cost_usd", "model_tokens", "wall_clock_minutes",
    "remediation_cycles", "concurrent_agents", "ci_reruns",
)


@dataclass(frozen=True)
class LimitBreach:
    name: str
    measured_value: Number
    cap: Number
    preserve_state: bool = True
    recommended_action: str = "Parked"


@dataclass(frozen=True)
class LimitDecision:
    allowed: bool
    code: str
    current_state: str
    breaches: Tuple[LimitBreach, ...] = ()
    preserve_state: bool = True
    recommended_action: str = "continue"


def _valid_number(value: object, *, positive: bool) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if isinstance(value, float) and not math.isfinite(value):
        return False
    return (
        value > 0 if positive else value >= 0
    )


def evaluate_limits(
    measured: Mapping[str, Number], caps: Mapping[str, Number], *, current_state: str
) -> LimitDecision:
    """Compare all closed limit fields and recommend, but never enact, Parked."""

    if (
        not isinstance(measured, Mapping)
        or not isinstance(caps, Mapping)
        or set(measured) != set(LIMIT_NAMES)
        or set(caps) != set(LIMIT_NAMES)
        or any(not _valid_number(measured[name], positive=False) for name in LIMIT_NAMES)
        or any(not _valid_number(caps[name], positive=True) for name in LIMIT_NAMES)
        or not isinstance(current_state, str)
        or not current_state
    ):
        return LimitDecision(False, "LIMIT_INPUT_INVALID", str(current_state), recommended_action="Parked")
    breaches = tuple(
        LimitBreach(name, measured[name], caps[name])
        for name in LIMIT_NAMES if measured[name] > caps[name]
    )
    if breaches:
        return LimitDecision(
            False, "LIMIT_EXCEEDED", current_state, breaches,
            preserve_state=True, recommended_action="Parked",
        )
    return LimitDecision(True, "LIMITS_WITHIN_CAPS", current_state)

"""Declarations: the conditions the experiment compares, as data with no logic."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Condition:
    """One condition of the experiment.

    Attributes:
        name: Short name used in tables.
        window: Number of past values the forecast averages.
    """

    name: str
    window: int


CONDITIONS: tuple[Condition, ...] = (Condition("short", 3), Condition("long", 12))

# The condition every other one is compared with.
REFERENCE: str = CONDITIONS[0].name

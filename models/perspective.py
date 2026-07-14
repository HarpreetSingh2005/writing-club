from dataclasses import dataclass


@dataclass
class Perspective:
    """
    Permanent entry stored in the Perspective Library.
    Defines how a discipline thinks.
    """

    name: str
    thinking_framework: str
    keywords: list[str]


@dataclass
class DiscoveredPerspective:
    """
    Temporary perspective discovered during one workflow execution.
    """

    name: str
    reason: str
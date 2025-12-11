from dataclasses import dataclass
from typing import Any

import numpy as np

from arseille.vending.enums import (
    AgeGroup,
    InboundInstruction,
    OutboundInstruction,
    Weather,
)
from arseille.vending.schemas import ArseilleBase


@dataclass
class DetectionMetadata:
    """
    Metadata information after a successful detection.

    The object that will be continuously serialized to be sent to the
    frontend through the websocket.

    **Only used during checkpoints.**
    """

    annotated_image: np.ndarray | None = None
    age: int | None = None
    weather: Weather | None = None
    timestamp: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the dataclass object to a dictionary."""
        return {"age": self.age, "weather": self.weather, "timestamp": self.timestamp}

    def clear(self) -> None:
        """Reset all values of attributes to None."""
        self.annotated_image = None
        self.age = None
        self.weather = None
        self.timestamp = None


class DetectionData(ArseilleBase):
    age: int
    age_group: AgeGroup
    weather: Weather


class InboundMessage(ArseilleBase):
    type: InboundInstruction
    transaction_data: dict[str, Any] | None = None


class OutboundMessage(ArseilleBase):
    type: OutboundInstruction
    detection_data: dict[str, Any] | None = None

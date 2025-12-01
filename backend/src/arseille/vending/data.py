from dataclasses import dataclass
from typing import Any

import numpy as np

from arseille.vending.enums import Weather


@dataclass
class DetectionMetadata:
    """
    Metadata information after a successful detection.

    This will be continuously streamed to the frontend through a websocket connection
    during checkpoints since checkpoints do not include user interaction.
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

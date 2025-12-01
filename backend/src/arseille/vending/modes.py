from enum import Enum


class VendingMode(Enum):
    """Different modes of the vending machine."""

    CHECKPOINT_25 = 1
    """Does face detection."""

    CHECKPOINT_50 = 2
    """Does face detection then age estimation."""

    CHECKPOINT_75 = 3
    """
    Does face detection then age estimation. Also determines the current weather
    conditions.
    """

    FULL_SYSTEM = 4
    """
    The full operation of the vending machine. Contains the functionalities of all
    checkpoints. This includes user interaction, where it is simulated in the browser.
    The interaction is similar on how you would interact with an actual vending machine.
    """

from enum import Enum, StrEnum, auto


class AgeGroup(StrEnum):
    CHILD = auto()
    TEEN = auto()
    ADULT = auto()
    SENIOR = auto()


class Weather(StrEnum):
    COLD = auto()
    MODERATE = auto()
    HOT = auto()


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


class InboundInstruction(StrEnum):
    START_ORDER = auto()
    VEND = auto()
    TAKE_DRINK = auto()
    CANCEL = auto()


class OutboundInstruction(StrEnum):
    PROCESSING_USER = auto()
    DISPLAY_DRINKS = auto()
    PREPARING_DRINK = auto()
    DRINK_READY = auto()
    RESET = auto()

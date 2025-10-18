from enum import StrEnum, auto


class AgeGroup(StrEnum):
    CHILD = auto()
    TEEN = auto()
    ADULT = auto()
    SENIOR = auto()


class Weather(StrEnum):
    COLD = auto()
    MODERATE = auto()
    HOT = auto()

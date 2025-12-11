from datetime import datetime, timezone
from typing import Annotated

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from arseille.vending.enums import AgeGroup, Weather


class ArseilleBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class TransactionBase(ArseilleBase):
    drink: str
    age: int
    age_group: AgeGroup
    weather: Weather
    timestamp: Annotated[
        datetime, Field(default_factory=lambda: datetime.now(timezone.utc))
    ]


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    id: Annotated[str, Field(validation_alias="_id")]

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid_to_str(cls, value: str | ObjectId) -> str:
        return str(value)

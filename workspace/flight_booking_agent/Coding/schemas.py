from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class FlightQuery(BaseModel):
    origin: str
    destination: str
    departure_date: date
    passengers: int = Field(default=1, ge=1)
    max_budget: Optional[float] = Field(default=None, ge=0)
    seat_preference: Optional[Literal["window", "aisle", "middle"]] = None
    bags: int = Field(default=0, ge=0)
    nonstop_only: bool = False
    book: bool = False

    @field_validator("origin", "destination")
    @classmethod
    def normalize_airport_code(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("airport codes must be three letters")
        return value


class FlightOption(BaseModel):
    flight_number: str
    origin: str
    destination: str
    departure_date: date
    arrival_date: date
    price: float = Field(ge=0)
    seat_preference: Literal["window", "aisle", "middle"]
    bags_allowed: int = Field(ge=0)
    nonstop: bool = True
    seats_available: int = Field(ge=0)

    @field_validator("origin", "destination")
    @classmethod
    def normalize_airport_code(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("airport codes must be three letters")
        return value


class BookingConfirmation(BaseModel):
    booking_id: str
    flight_number: str
    status: Literal["confirmed", "rejected"]
    message: str
    total_price: float = Field(ge=0)


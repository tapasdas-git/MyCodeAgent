from __future__ import annotations

from decimal import Decimal
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

SUPPORTED_CURRENCIES: frozenset[str] = frozenset({"USD", "INR", "EUR", "GBP"})


def _normalize_currency_code(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("currency code must be a string")

    normalized = value.strip().upper()
    if len(normalized) != 3 or not normalized.isalpha():
        raise ValueError("currency code must be a three-letter ISO code")
    return normalized


class ConversionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    amount: Decimal = Field(gt=0)
    source_currency: str
    target_currency: str

    _supported_currencies: ClassVar[frozenset[str]] = SUPPORTED_CURRENCIES

    @field_validator("source_currency", "target_currency")
    @classmethod
    def _validate_currency_code(cls, value: str) -> str:
        normalized = _normalize_currency_code(value)
        if normalized not in cls._supported_currencies:
            raise ValueError(f"unsupported currency code: {normalized}")
        return normalized

class ConversionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request: ConversionRequest
    exchange_rate: Decimal = Field(gt=0)
    converted_amount: Decimal = Field(gt=0)
    rate_source: str
    api_key_present: bool = False

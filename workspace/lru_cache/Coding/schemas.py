from __future__ import annotations

from math import isclose
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")


class CacheEntry(BaseModel, Generic[KeyT, ValueT]):
    model_config = ConfigDict(extra="forbid")

    key: KeyT
    value: ValueT


class CacheStats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hits: int = Field(ge=0)
    misses: int = Field(ge=0)
    hit_rate: float = Field(ge=0.0, le=1.0)
    miss_rate: float = Field(ge=0.0, le=1.0)
    current_size: int = Field(ge=0)
    capacity: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_internal_consistency(self) -> "CacheStats":
        if self.current_size > self.capacity:
            raise ValueError("current_size cannot exceed capacity")

        total_requests = self.hits + self.misses
        if total_requests == 0:
            if self.hit_rate != 0.0 or self.miss_rate != 0.0:
                raise ValueError("zero-request stats must have zero hit and miss rates")
            return self

        expected_hit_rate = self.hits / total_requests
        expected_miss_rate = self.misses / total_requests
        if not isclose(self.hit_rate, expected_hit_rate, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("hit_rate must match hits / total_requests")
        if not isclose(self.miss_rate, expected_miss_rate, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("miss_rate must match misses / total_requests")
        return self

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Protocol

from .schemas import ConversionRequest, ConversionResult, SUPPORTED_CURRENCIES

_UNITS_PER_USD: dict[str, Decimal] = {
    "USD": Decimal("1"),
    "INR": Decimal("83.0"),
    "EUR": Decimal("0.92"),
    "GBP": Decimal("0.79"),
}


class ExchangeRateProvider(Protocol):
    """Protocol for exchange-rate lookup tools."""

    rate_source: str
    api_key_present: bool

    def get_rate(self, source_currency: str, target_currency: str) -> Decimal:
        raise NotImplementedError


@dataclass(frozen=True)
class MockExchangeRateProvider:
    """Deterministic rate provider backed by an in-memory rate table."""

    api_key: str | None = None
    rates_per_usd: dict[str, Decimal] | None = None
    rate_source: str = "mock-exchange-rate-table"

    def __post_init__(self) -> None:
        rates = self.rates_per_usd or _UNITS_PER_USD
        normalized_rates = {
            code.upper(): Decimal(str(rate)) for code, rate in rates.items()
        }
        missing = SUPPORTED_CURRENCIES.difference(normalized_rates)
        if missing:
            raise ValueError(f"missing supported currency rates: {sorted(missing)}")
        object.__setattr__(self, "rates_per_usd", normalized_rates)
        object.__setattr__(self, "api_key_present", bool(self.api_key))

    api_key_present: bool = False

    def get_rate(self, source_currency: str, target_currency: str) -> Decimal:
        source = source_currency.upper()
        target = target_currency.upper()
        if source not in self.rates_per_usd or target not in self.rates_per_usd:
            raise ValueError("unsupported currency code requested")
        if source == target:
            return Decimal("1")
        source_units_per_usd = self.rates_per_usd[source]
        target_units_per_usd = self.rates_per_usd[target]
        return (target_units_per_usd / source_units_per_usd).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )


class CurrencyConverter:
    """Core conversion engine using an injectable exchange-rate provider."""

    def __init__(self, rate_provider: ExchangeRateProvider) -> None:
        self._rate_provider = rate_provider

    @property
    def rate_provider(self) -> ExchangeRateProvider:
        return self._rate_provider

    def convert(self, request: ConversionRequest) -> ConversionResult:
        exchange_rate = self._rate_provider.get_rate(request.source_currency, request.target_currency)
        converted_amount = (request.amount * exchange_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return ConversionResult(
            request=request,
            exchange_rate=exchange_rate,
            converted_amount=converted_amount,
            rate_source=self._rate_provider.rate_source,
            api_key_present=self._rate_provider.api_key_present,
        )


def build_converter(
    *,
    rate_provider: ExchangeRateProvider | None = None,
    api_key: str | None = None,
) -> CurrencyConverter:
    """Build a converter with validated configuration and injectable dependencies."""

    if rate_provider is None:
        resolved_api_key = api_key if api_key is not None else os.getenv("EXCHANGE_API_KEY")
        rate_provider = MockExchangeRateProvider(api_key=resolved_api_key)
    return CurrencyConverter(rate_provider=rate_provider)


def format_conversion_result(result: ConversionResult) -> str:
    return (
        f"{result.request.amount} {result.request.source_currency} = "
        f"{result.converted_amount} {result.request.target_currency} "
        f"at rate {result.exchange_rate} ({result.rate_source})"
    )

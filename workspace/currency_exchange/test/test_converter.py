from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest

from currency_exchange.Coding.converter import CurrencyConverter, MockExchangeRateProvider, build_converter, format_conversion_result
from currency_exchange.Coding.schemas import ConversionRequest


@pytest.fixture()
def converter() -> CurrencyConverter:
    return build_converter(api_key="test-key")


def test_request_normalizes_currency_codes() -> None:
    request = ConversionRequest(amount=Decimal("10"), source_currency="usd", target_currency="inr")

    assert request.source_currency == "USD"
    assert request.target_currency == "INR"


def test_request_rejects_unsupported_currency_code() -> None:
    with pytest.raises(ValueError, match="unsupported currency code"):
        ConversionRequest(amount=Decimal("10"), source_currency="USD", target_currency="AUD")


def test_request_rejects_non_positive_amount() -> None:
    with pytest.raises(ValueError, match="greater than 0"):
        ConversionRequest(amount=Decimal("0"), source_currency="USD", target_currency="EUR")


def test_converter_uses_mock_rate_table_and_formats_output(converter: CurrencyConverter) -> None:
    request = ConversionRequest(amount=Decimal("10"), source_currency="USD", target_currency="INR")

    result = converter.convert(request)

    assert result.exchange_rate == Decimal("83.0000")
    assert result.converted_amount == Decimal("830.00")
    assert result.rate_source == "mock-exchange-rate-table"
    assert result.api_key_present is True
    assert format_conversion_result(result) == "10 USD = 830.00 INR at rate 83.0000 (mock-exchange-rate-table)"


def test_converter_supports_cross_currency_conversion() -> None:
    provider = MockExchangeRateProvider(api_key="offline-key")
    converter = CurrencyConverter(rate_provider=provider)
    request = ConversionRequest(amount=Decimal("25"), source_currency="EUR", target_currency="GBP")

    result = converter.convert(request)

    assert result.exchange_rate == Decimal("0.8587")
    assert result.converted_amount == Decimal("21.47")


def test_build_converter_reads_api_key_from_environment() -> None:
    with patch("currency_exchange.Coding.converter.os.getenv", return_value="env-key") as getenv:
        converter = build_converter()

    assert isinstance(converter.rate_provider, MockExchangeRateProvider)
    assert converter.rate_provider.api_key == "env-key"
    assert converter.rate_provider.api_key_present is True
    getenv.assert_called_once_with("EXCHANGE_API_KEY")

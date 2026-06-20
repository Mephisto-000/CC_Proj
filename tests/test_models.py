"""領域模型測試。"""

from decimal import Decimal

import pytest

from fund_nav.domain.exceptions import InvalidHoldingError
from fund_nav.domain.models import Fund, Holding, to_decimal


class TestToDecimal:
    def test_passthrough_decimal(self) -> None:
        value = Decimal("1.5")
        assert to_decimal(value) is value

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(1, Decimal("1")), ("2.5", Decimal("2.5")), (0.1, Decimal("0.1"))],
    )
    def test_converts_without_float_error(self, value: object, expected: Decimal) -> None:
        assert to_decimal(value) == expected


class TestHolding:
    def test_market_value(self) -> None:
        holding = Holding(symbol="2330", name="台積電", quantity=Decimal("10"), price=Decimal("950"))
        assert holding.market_value == Decimal("9500")

    def test_coerces_numeric_inputs(self) -> None:
        holding = Holding(symbol="X", name="X", quantity="3", price="2.5")
        assert holding.quantity == Decimal("3")
        assert holding.price == Decimal("2.5")
        assert holding.market_value == Decimal("7.5")

    def test_blank_symbol_raises(self) -> None:
        with pytest.raises(InvalidHoldingError):
            Holding(symbol="  ", name="X", quantity=1, price=1)

    def test_negative_quantity_raises(self) -> None:
        with pytest.raises(InvalidHoldingError):
            Holding(symbol="X", name="X", quantity=-1, price=1)

    def test_negative_price_raises(self) -> None:
        with pytest.raises(InvalidHoldingError):
            Holding(symbol="X", name="X", quantity=1, price=-1)

    def test_is_frozen(self) -> None:
        holding = Holding(symbol="X", name="X", quantity=1, price=1)
        with pytest.raises(Exception):
            holding.price = Decimal("2")  # type: ignore[misc]


class TestFund:
    def test_total_market_value_sums_holdings(self) -> None:
        fund = Fund(
            name="F",
            holdings=[
                Holding(symbol="A", name="A", quantity=2, price=3),
                Holding(symbol="B", name="B", quantity=5, price=4),
            ],
        )
        assert fund.total_market_value == Decimal("26")

    def test_total_market_value_empty(self) -> None:
        assert Fund(name="F").total_market_value == Decimal("0")

    def test_defaults_are_zero_decimal(self) -> None:
        fund = Fund(name="F")
        assert fund.cash == Decimal("0")
        assert fund.liabilities == Decimal("0")
        assert fund.units_outstanding == Decimal("0")

    def test_coerces_numeric_inputs(self) -> None:
        fund = Fund(name="F", cash="100", liabilities=10, units_outstanding="5")
        assert fund.cash == Decimal("100")
        assert fund.liabilities == Decimal("10")
        assert fund.units_outstanding == Decimal("5")

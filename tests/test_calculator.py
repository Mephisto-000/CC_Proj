"""淨值計算測試。"""

from datetime import datetime
from decimal import Decimal

import pytest

from fund_nav.domain.exceptions import InvalidFundError
from fund_nav.domain.models import Fund, Holding
from fund_nav.services.calculator import NavCalculator


@pytest.fixture
def calculator() -> NavCalculator:
    return NavCalculator()


class TestCalculate:
    def test_basic_calculation(self, calculator: NavCalculator, sample_fund: Fund) -> None:
        result = calculator.calculate(sample_fund)
        # 持倉市值 = 1000*950 + 2000*165 = 950000 + 330000 = 1280000
        assert result.total_market_value == Decimal("1280000")
        # 總資產 = 1280000 + 1000000 = 2280000
        assert result.total_assets == Decimal("2280000")
        # NAV = 2280000 - 50000 = 2230000
        assert result.net_asset_value == Decimal("2230000")
        # 每單位淨值 = 2230000 / 100000 = 22.3
        assert result.nav_per_unit == Decimal("22.3000")
        assert result.fund_name == "測試基金"

    def test_nav_per_unit_rounding(self, calculator: NavCalculator) -> None:
        fund = Fund(name="F", cash=Decimal("100"), units_outstanding=Decimal("3"))
        result = calculator.calculate(fund)
        # 100 / 3 = 33.3333... → 四捨五入到小數第四位
        assert result.nav_per_unit == Decimal("33.3333")

    def test_cash_only_fund(self, calculator: NavCalculator) -> None:
        fund = Fund(name="現金基金", cash=Decimal("500"), units_outstanding=Decimal("100"))
        result = calculator.calculate(fund)
        assert result.total_market_value == Decimal("0")
        assert result.nav_per_unit == Decimal("5.0000")

    def test_custom_precision(self) -> None:
        calculator = NavCalculator(precision=Decimal("0.01"))
        fund = Fund(name="F", cash=Decimal("100"), units_outstanding=Decimal("3"))
        result = calculator.calculate(fund)
        assert result.nav_per_unit == Decimal("33.33")

    def test_as_of_passthrough(self, calculator: NavCalculator, sample_fund: Fund) -> None:
        moment = datetime(2026, 6, 20, 12, 0, 0)
        result = calculator.calculate(sample_fund, as_of=moment)
        assert result.as_of == moment

    def test_as_of_defaults_to_now(self, calculator: NavCalculator, sample_fund: Fund) -> None:
        before = datetime.now()
        result = calculator.calculate(sample_fund)
        assert result.as_of >= before

    def test_zero_units_raises(self, calculator: NavCalculator) -> None:
        fund = Fund(name="F", cash=Decimal("100"), units_outstanding=Decimal("0"))
        with pytest.raises(InvalidFundError):
            calculator.calculate(fund)

    def test_negative_units_raises(self, calculator: NavCalculator) -> None:
        fund = Fund(name="F", cash=Decimal("100"), units_outstanding=Decimal("-1"))
        with pytest.raises(InvalidFundError):
            calculator.calculate(fund)

    def test_negative_liabilities_raises(self, calculator: NavCalculator) -> None:
        fund = Fund(
            name="F",
            cash=Decimal("100"),
            liabilities=Decimal("-1"),
            units_outstanding=Decimal("10"),
        )
        with pytest.raises(InvalidFundError):
            calculator.calculate(fund)

    def test_negative_nav_allowed(self, calculator: NavCalculator) -> None:
        fund = Fund(
            name="虧損基金",
            holdings=[Holding(symbol="A", name="A", quantity=1, price=10)],
            liabilities=Decimal("1000"),
            units_outstanding=Decimal("100"),
        )
        result = calculator.calculate(fund)
        assert result.net_asset_value == Decimal("-990")
        assert result.nav_per_unit == Decimal("-9.9000")

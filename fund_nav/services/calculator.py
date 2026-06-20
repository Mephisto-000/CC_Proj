"""淨值（NAV）計算邏輯。"""

import logging
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from fund_nav.domain.exceptions import InvalidFundError
from fund_nav.domain.models import Fund, NavResult

logger = logging.getLogger(__name__)

# 每單位淨值精度：小數點後四位。
DEFAULT_PRECISION = Decimal("0.0001")


class NavCalculator:
    """依基金資料計算淨值。

    NAV＝（持倉市值＋現金）－負債
    每單位淨值＝NAV÷流通在外單位數
    """

    def __init__(self, precision: Decimal = DEFAULT_PRECISION) -> None:
        self._precision = precision

    def calculate(self, fund: Fund, *, as_of: datetime | None = None) -> NavResult:
        """計算基金淨值。

        Args:
            fund: 欲計算的基金。
            as_of: 計算基準時間，預設為呼叫當下。

        Returns:
            ``NavResult`` 計算結果。

        Raises:
            InvalidFundError: 流通在外單位數不為正數，或負債為負數時。
        """
        if fund.units_outstanding <= 0:
            raise InvalidFundError("流通在外單位數必須大於 0")
        if fund.liabilities < 0:
            raise InvalidFundError("負債不可為負數")

        as_of = as_of or datetime.now()

        total_market_value = fund.total_market_value
        total_assets = total_market_value + fund.cash
        net_asset_value = total_assets - fund.liabilities
        nav_per_unit = (net_asset_value / fund.units_outstanding).quantize(
            self._precision, rounding=ROUND_HALF_UP
        )

        result = NavResult(
            fund_name=fund.name,
            total_market_value=total_market_value,
            cash=fund.cash,
            total_assets=total_assets,
            total_liabilities=fund.liabilities,
            net_asset_value=net_asset_value,
            units_outstanding=fund.units_outstanding,
            nav_per_unit=nav_per_unit,
            as_of=as_of,
        )

        logger.info(
            "完成淨值計算：基金=%s，NAV=%s，每單位淨值=%s",
            fund.name,
            net_asset_value,
            nav_per_unit,
        )
        return result

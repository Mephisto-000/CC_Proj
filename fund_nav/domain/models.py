"""基金淨值計算所需的資料模型。

金額一律使用 ``Decimal`` 以避免浮點數誤差。
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from fund_nav.domain.exceptions import InvalidHoldingError

Number = Decimal | int | float | str


def to_decimal(value: Number) -> Decimal:
    """將數值安全轉換為 ``Decimal``。

    透過 ``str`` 轉換以避免 float 的二進位誤差。
    """
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass(frozen=True)
class Holding:
    """單一持倉部位。

    Attributes:
        symbol: 標的代號。
        name: 標的名稱。
        quantity: 持有數量。
        price: 每單位市價。
    """

    symbol: str
    name: str
    quantity: Decimal
    price: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "quantity", to_decimal(self.quantity))
        object.__setattr__(self, "price", to_decimal(self.price))

        if not self.symbol.strip():
            raise InvalidHoldingError("symbol 不可為空")
        if self.quantity < 0:
            raise InvalidHoldingError(f"quantity 不可為負數：{self.quantity}")
        if self.price < 0:
            raise InvalidHoldingError(f"price 不可為負數：{self.price}")

    @property
    def market_value(self) -> Decimal:
        """市值＝數量×市價。"""
        return self.quantity * self.price


@dataclass
class Fund:
    """基金，包含持倉、現金與負債等資訊。

    Attributes:
        name: 基金名稱。
        holdings: 持倉清單。
        cash: 現金部位。
        liabilities: 負債總額（如應付管理費）。
        units_outstanding: 流通在外單位數。
    """

    name: str
    holdings: list[Holding] = field(default_factory=list)
    cash: Decimal = field(default_factory=lambda: Decimal("0"))
    liabilities: Decimal = field(default_factory=lambda: Decimal("0"))
    units_outstanding: Decimal = field(default_factory=lambda: Decimal("0"))

    def __post_init__(self) -> None:
        self.cash = to_decimal(self.cash)
        self.liabilities = to_decimal(self.liabilities)
        self.units_outstanding = to_decimal(self.units_outstanding)

    @property
    def total_market_value(self) -> Decimal:
        """所有持倉市值加總。"""
        return sum((h.market_value for h in self.holdings), Decimal("0"))


@dataclass(frozen=True)
class NavResult:
    """淨值計算結果。

    Attributes:
        fund_name: 基金名稱。
        total_market_value: 持倉市值總額。
        cash: 現金部位。
        total_assets: 總資產（持倉市值＋現金）。
        total_liabilities: 總負債。
        net_asset_value: 淨資產價值（總資產－總負債）。
        units_outstanding: 流通在外單位數。
        nav_per_unit: 每單位淨值。
        as_of: 計算時間。
    """

    fund_name: str
    total_market_value: Decimal
    cash: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    net_asset_value: Decimal
    units_outstanding: Decimal
    nav_per_unit: Decimal
    as_of: datetime

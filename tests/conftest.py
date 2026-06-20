"""共用測試 fixtures。"""

from decimal import Decimal

import pytest

from fund_nav.domain.models import Fund, Holding


@pytest.fixture
def sample_fund() -> Fund:
    """提供一檔具代表性的測試基金。"""
    return Fund(
        name="測試基金",
        holdings=[
            Holding(symbol="2330", name="台積電", quantity=Decimal("1000"), price=Decimal("950")),
            Holding(symbol="2317", name="鴻海", quantity=Decimal("2000"), price=Decimal("165")),
        ],
        cash=Decimal("1000000"),
        liabilities=Decimal("50000"),
        units_outstanding=Decimal("100000"),
    )

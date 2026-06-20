"""基金資料持久化測試。"""

from decimal import Decimal
from pathlib import Path

import pytest

from fund_nav.domain.models import Fund
from fund_nav.services.repository import FundRepository


@pytest.fixture
def repository() -> FundRepository:
    return FundRepository()


class TestRepository:
    def test_save_and_load_roundtrip(
        self, repository: FundRepository, sample_fund: Fund, tmp_path: Path
    ) -> None:
        path = tmp_path / "fund.json"
        repository.save(sample_fund, path)
        loaded = repository.load(path)

        assert loaded.name == sample_fund.name
        assert loaded.cash == sample_fund.cash
        assert loaded.liabilities == sample_fund.liabilities
        assert loaded.units_outstanding == sample_fund.units_outstanding
        assert len(loaded.holdings) == len(sample_fund.holdings)
        assert loaded.holdings[0].symbol == "2330"
        assert loaded.total_market_value == sample_fund.total_market_value

    def test_save_creates_parent_dirs(
        self, repository: FundRepository, sample_fund: Fund, tmp_path: Path
    ) -> None:
        path = tmp_path / "nested" / "dir" / "fund.json"
        repository.save(sample_fund, path)
        assert path.exists()

    def test_decimal_precision_preserved(
        self, repository: FundRepository, tmp_path: Path
    ) -> None:
        fund = Fund(name="F", cash=Decimal("0.1"), units_outstanding=Decimal("3"))
        path = tmp_path / "fund.json"
        repository.save(fund, path)
        loaded = repository.load(path)
        assert loaded.cash == Decimal("0.1")
        assert loaded.units_outstanding == Decimal("3")

    def test_load_missing_file_raises(
        self, repository: FundRepository, tmp_path: Path
    ) -> None:
        with pytest.raises(FileNotFoundError):
            repository.load(tmp_path / "missing.json")

    def test_load_accepts_str_path(
        self, repository: FundRepository, sample_fund: Fund, tmp_path: Path
    ) -> None:
        path = tmp_path / "fund.json"
        repository.save(sample_fund, str(path))
        loaded = repository.load(str(path))
        assert loaded.name == sample_fund.name

    def test_empty_holdings_roundtrip(
        self, repository: FundRepository, tmp_path: Path
    ) -> None:
        fund = Fund(name="空基金", units_outstanding=Decimal("1"))
        path = tmp_path / "empty.json"
        repository.save(fund, path)
        loaded = repository.load(path)
        assert loaded.holdings == []

"""基金資料的 JSON 持久化。

金額以字串序列化，避免 JSON 浮點數造成精度損失。
"""

import json
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any

from fund_nav.domain.models import Fund, Holding

logger = logging.getLogger(__name__)


class FundRepository:
    """負責基金資料的讀寫。"""

    def save(self, fund: Fund, path: Path) -> None:
        """將基金資料儲存為 JSON 檔案。

        Args:
            fund: 欲儲存的基金。
            path: 目標檔案路徑，會自動建立上層目錄。
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._to_dict(fund), ensure_ascii=False, indent=2)
        path.write_text(payload, encoding="utf-8")
        logger.info("已儲存基金資料至 %s", path)

    def load(self, path: Path) -> Fund:
        """從 JSON 檔案載入基金資料。

        Args:
            path: 來源檔案路徑。

        Returns:
            ``Fund`` 物件。

        Raises:
            FileNotFoundError: 檔案不存在時。
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"找不到基金資料檔：{path}")

        data = json.loads(path.read_text(encoding="utf-8"))
        fund = self._from_dict(data)
        logger.info("已從 %s 載入基金資料", path)
        return fund

    @staticmethod
    def _to_dict(fund: Fund) -> dict[str, Any]:
        return {
            "name": fund.name,
            "cash": str(fund.cash),
            "liabilities": str(fund.liabilities),
            "units_outstanding": str(fund.units_outstanding),
            "holdings": [
                {
                    "symbol": h.symbol,
                    "name": h.name,
                    "quantity": str(h.quantity),
                    "price": str(h.price),
                }
                for h in fund.holdings
            ],
        }

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> Fund:
        holdings = [
            Holding(
                symbol=item["symbol"],
                name=item["name"],
                quantity=Decimal(item["quantity"]),
                price=Decimal(item["price"]),
            )
            for item in data.get("holdings", [])
        ]
        return Fund(
            name=data["name"],
            holdings=holdings,
            cash=Decimal(data.get("cash", "0")),
            liabilities=Decimal(data.get("liabilities", "0")),
            units_outstanding=Decimal(data.get("units_outstanding", "0")),
        )

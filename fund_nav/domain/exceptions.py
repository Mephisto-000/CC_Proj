"""領域層自訂例外。"""


class FundNavError(Exception):
    """Fund NAV Workbench 領域例外的基底類別。"""


class InvalidHoldingError(FundNavError):
    """持倉資料不合法時拋出。"""


class InvalidFundError(FundNavError):
    """基金資料不符合淨值計算前提時拋出。"""

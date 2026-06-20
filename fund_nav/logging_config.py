"""集中化的 logging 設定。

依專案規範，全程使用 logging，禁止使用 print。
"""

import logging
from pathlib import Path

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(
    level: int = logging.INFO,
    log_file: Path | None = None,
    *,
    force: bool = True,
) -> None:
    """設定 root logger。

    Args:
        level: 日誌等級，預設 ``logging.INFO``。
        log_file: 若提供，額外將日誌寫入此檔案（自動建立上層目錄）。
        force: 是否強制重設既有 handlers，預設為 True 以利重複呼叫。
    """
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_file is not None:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=handlers,
        force=force,
    )

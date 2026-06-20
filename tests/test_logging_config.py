"""logging 設定測試。"""

import logging
from pathlib import Path

from fund_nav.logging_config import setup_logging


class TestSetupLogging:
    def test_configures_stream_handler(self) -> None:
        setup_logging(level=logging.DEBUG)
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)

    def test_adds_file_handler_and_creates_dirs(self, tmp_path: Path) -> None:
        log_file = tmp_path / "logs" / "app.log"
        setup_logging(log_file=log_file)
        logging.getLogger(__name__).info("測試訊息")

        assert log_file.exists()
        assert any(
            isinstance(h, logging.FileHandler) for h in logging.getLogger().handlers
        )
        # 關閉 file handler 以釋放檔案 handle，避免影響其他測試。
        for handler in list(logging.getLogger().handlers):
            if isinstance(handler, logging.FileHandler):
                handler.close()
                logging.getLogger().removeHandler(handler)

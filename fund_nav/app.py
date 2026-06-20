"""應用程式進入點。"""

import logging

from fund_nav.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """設定日誌並啟動桌面應用程式。"""
    setup_logging()
    logger.info("啟動 Fund NAV Workbench")

    # 延遲匯入 UI，避免在無顯示器環境（如測試）匯入 CustomTkinter。
    from fund_nav.ui.app import NavWorkbenchApp

    app = NavWorkbenchApp()
    app.run()


if __name__ == "__main__":
    main()

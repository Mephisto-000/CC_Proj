"""每日 git commit 紀錄產生工具的進入點。"""

import argparse
import logging
from datetime import date, datetime
from pathlib import Path

from daily_git_history.domain.exceptions import DailyGitHistoryError
from daily_git_history.services.git_log_reader import DEFAULT_TIMEZONE, GitLogReader
from daily_git_history.services.xlsx_writer import CommitHistoryWriter
from fund_nav.logging_config import setup_logging

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("DailyGitHistory")


def build_output_path(target_date: date, output_dir: Path) -> Path:
    """依日期產生輸出檔案路徑（檔名為 8 碼 ``YYYYMMDD.xlsx``）。

    Args:
        target_date: 報表對應的日期。
        output_dir: 輸出資料夾路徑。

    Returns:
        完整輸出檔案路徑。
    """
    filename = f"{target_date.strftime('%Y%m%d')}.xlsx"
    return Path(output_dir) / filename


def resolve_target_date(explicit_date: date | None) -> date:
    """解析欲查詢的日期。

    未明確指定時，使用台灣時區（``Asia/Taipei``）的今日日期，
    避免排程在不同時區的伺服器上執行時，因系統本地時區不同而誤判日期。

    Args:
        explicit_date: 使用者透過 ``--date`` 指定的日期，``None`` 表示未指定。

    Returns:
        欲查詢的日期。
    """
    return explicit_date or datetime.now(DEFAULT_TIMEZONE).date()


def run(
    repo_path: Path,
    output_dir: Path,
    target_date: date,
    *,
    reader: GitLogReader | None = None,
    writer: CommitHistoryWriter | None = None,
) -> Path:
    """執行每日 git commit 紀錄產生流程。

    Args:
        repo_path: 欲查詢的 git repository 路徑。
        output_dir: 輸出資料夾路徑。
        target_date: 欲查詢的日期。
        reader: 可選的 ``GitLogReader``，未提供時依 ``repo_path`` 建立（供測試注入）。
        writer: 可選的 ``CommitHistoryWriter``，未提供時建立預設實例（供測試注入）。

    Returns:
        輸出檔案的路徑。

    Raises:
        DailyGitHistoryError: 讀取 git log 或寫入檔案失敗時。
    """
    reader = reader or GitLogReader(repo_path)
    writer = writer or CommitHistoryWriter()

    records = reader.read(target_date)
    output_path = build_output_path(target_date, output_dir)
    writer.write(records, output_path)
    return output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令列參數。

    Args:
        argv: 命令列參數清單，``None`` 時使用 ``sys.argv``。

    Returns:
        解析後的參數物件。
    """
    parser = argparse.ArgumentParser(description="產生每日 git commit 紀錄 xlsx")
    parser.add_argument(
        "--repo", type=Path, default=Path("."), help="git repository 路徑"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="輸出資料夾路徑",
    )
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=None,
        help="欲查詢的日期（格式 YYYY-MM-DD），預設為今日",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """CLI 主流程。

    Args:
        argv: 命令列參數清單，``None`` 時使用 ``sys.argv``。

    Raises:
        DailyGitHistoryError: 流程執行失敗時，於記錄錯誤日誌後重新拋出。
    """
    setup_logging()
    args = parse_args(argv)
    target_date = resolve_target_date(args.date)

    try:
        output_path = run(args.repo, args.output_dir, target_date)
    except DailyGitHistoryError:
        logger.exception("產生每日 git commit 紀錄失敗")
        raise

    logger.info("完成，輸出檔案：%s", output_path)


if __name__ == "__main__":
    main()

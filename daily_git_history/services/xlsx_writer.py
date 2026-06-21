"""將 commit 紀錄寫入 xlsx 檔案。"""

import logging
from pathlib import Path

from openpyxl import Workbook

from daily_git_history.domain.models import CommitRecord

logger = logging.getLogger(__name__)

_HEADERS = ("作者", "Commit 訊息", "變動檔案")


class CommitHistoryWriter:
    """負責將 ``CommitRecord`` 清單輸出為 xlsx 報表。

    規則：
        - 每一 row 依 commit 時間先後由上到下排列。
        - 單一 commit 變動多個檔案時，每個檔案各佔一 row，並依副檔名字母排序。
        - 若 commit 未變動任何檔案，仍輸出一 row，變動檔案欄位留空。
    """

    def write(self, records: list[CommitRecord], path: Path) -> None:
        """寫入 xlsx 檔案。

        Args:
            records: 依時間先後排序的 commit 紀錄。
            path: 輸出檔案路徑，會自動建立上層目錄。
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        workbook = Workbook()
        sheet = workbook.active
        sheet.append(_HEADERS)

        row_count = 0
        for record in records:
            sorted_files = record.sorted_files
            if not sorted_files:
                sheet.append((record.author, record.subject, ""))
                row_count += 1
                continue
            for file_change in sorted_files:
                sheet.append((record.author, record.subject, file_change.path))
                row_count += 1

        workbook.save(path)
        logger.info(
            "已輸出 %d 筆 commit（共 %d row）至 %s", len(records), row_count, path
        )

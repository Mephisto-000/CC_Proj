"""讀取並解析指定日期內的 git commit 紀錄。"""

import logging
import subprocess
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

from daily_git_history.domain.exceptions import GitCommandError
from daily_git_history.domain.models import CommitRecord, FileChange

logger = logging.getLogger(__name__)

_RECORD_SEPARATOR = "\x1e"
_FIELD_SEPARATOR = "\x1f"
_PRETTY_FIELDS = ("%H", "%an", "%cI", "%s")

#: 排程任務可能在任意時區的伺服器上執行，固定以台灣時區判斷「今天」的範圍，
#: 避免因執行環境時區不同（例如 UTC）導致日期判斷偏差一天。
DEFAULT_TIMEZONE = ZoneInfo("Asia/Taipei")


class GitLogReader:
    """負責透過 ``git log`` 取得指定日期的 commit 紀錄。"""

    def __init__(self, repo_path: Path, timezone: ZoneInfo = DEFAULT_TIMEZONE) -> None:
        self._repo_path = Path(repo_path)
        self._timezone = timezone

    def read(self, target_date: date) -> list[CommitRecord]:
        """取得指定日期（依 commit date，00:00:00–23:59:59）內的所有 commit。

        Args:
            target_date: 欲查詢的日期。

        Returns:
            依 commit 時間由舊到新排序的 ``CommitRecord`` 清單。

        Raises:
            GitCommandError: 找不到 git 執行檔，或 ``git log`` 執行失敗時。
        """
        since = datetime.combine(target_date, time.min, tzinfo=self._timezone)
        until = datetime.combine(target_date, time(23, 59, 59), tzinfo=self._timezone)
        output = self._run_git_log(since, until)
        records = self._parse(output)
        logger.info("讀取到 %d 筆 commit（%s）", len(records), target_date.isoformat())
        return records

    def _run_git_log(self, since: datetime, until: datetime) -> str:
        pretty_format = _FIELD_SEPARATOR.join(_PRETTY_FIELDS)
        command = [
            "git",
            "-C",
            str(self._repo_path),
            "log",
            f"--since={since.isoformat(sep=' ')}",
            f"--until={until.isoformat(sep=' ')}",
            f"--pretty=format:{_RECORD_SEPARATOR}{pretty_format}",
            "--name-only",
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                check=True,
                text=True,
                encoding="utf-8",
            )
        except FileNotFoundError as exc:
            raise GitCommandError("找不到 git 執行檔，請確認已安裝 git") from exc
        except subprocess.CalledProcessError as exc:
            raise GitCommandError(f"git log 執行失敗：{exc.stderr.strip()}") from exc
        return result.stdout

    @staticmethod
    def _parse(output: str) -> list[CommitRecord]:
        blocks = [block for block in output.split(_RECORD_SEPARATOR) if block.strip()]
        records: list[CommitRecord] = []
        for block in blocks:
            lines = block.splitlines()
            commit_hash, author, committed_at_raw, subject = lines[0].split(
                _FIELD_SEPARATOR, maxsplit=3
            )
            files = tuple(
                FileChange(path=line.strip()) for line in lines[1:] if line.strip()
            )
            records.append(
                CommitRecord(
                    commit_hash=commit_hash,
                    author=author,
                    committed_at=datetime.fromisoformat(committed_at_raw),
                    subject=subject,
                    files=files,
                )
            )
        # git log 預設由新到舊輸出，反轉為由舊到新（與 git 內部拓樸順序一致，
        # 避免時間戳記秒數相同時用排序造成順序錯亂）。
        records.reverse()
        return records

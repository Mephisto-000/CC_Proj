"""每日 git commit 紀錄的資料模型。"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import PurePosixPath


@dataclass(frozen=True)
class FileChange:
    """單一 commit 中變動的檔案。

    Attributes:
        path: 變動檔案的相對路徑（以 ``/`` 分隔，與 git 輸出一致）。
    """

    path: str

    @property
    def extension(self) -> str:
        """副檔名（含點、小寫）；無副檔名（如隱藏檔）則回傳空字串。"""
        return PurePosixPath(self.path).suffix.lower()


@dataclass(frozen=True)
class CommitRecord:
    """單一 git commit 的紀錄。

    Attributes:
        commit_hash: commit hash。
        author: commit 作者名稱。
        committed_at: commit 時間（commit date）。
        subject: commit message 第一行。
        files: 此 commit 變動到的檔案清單，依 ``git log`` 原始順序。
    """

    commit_hash: str
    author: str
    committed_at: datetime
    subject: str
    files: tuple[FileChange, ...] = field(default_factory=tuple)

    @property
    def sorted_files(self) -> tuple[FileChange, ...]:
        """依副檔名字母排序（次序鍵為路徑）後的檔案清單。"""
        return tuple(sorted(self.files, key=lambda f: (f.extension, f.path)))

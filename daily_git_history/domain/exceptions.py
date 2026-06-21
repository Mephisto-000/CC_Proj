"""領域層自訂例外。"""


class DailyGitHistoryError(Exception):
    """Daily Git History 領域例外的基底類別。"""


class GitCommandError(DailyGitHistoryError):
    """執行 git 指令失敗時拋出。"""

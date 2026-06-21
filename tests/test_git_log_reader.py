"""GitLogReader 單元測試（以 subprocess mock 隔離真實 git 指令）。"""

import subprocess
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from daily_git_history.domain.exceptions import GitCommandError
from daily_git_history.services.git_log_reader import GitLogReader

RS = "\x1e"
FS = "\x1f"


def _fake_completed_process(stdout: str) -> MagicMock:
    process = MagicMock()
    process.stdout = stdout
    return process


class TestGitLogReader:
    def test_parses_single_commit_with_multiple_files(self) -> None:
        stdout = (
            f"{RS}abc123{FS}Mephisto{FS}2026-06-22T10:00:00+08:00{FS}feat: 新增功能\n"
            "fund_nav/cli.py\n"
            "README.md\n"
        )
        with patch("subprocess.run", return_value=_fake_completed_process(stdout)):
            records = GitLogReader(Path(".")).read(date(2026, 6, 22))

        assert len(records) == 1
        record = records[0]
        assert record.commit_hash == "abc123"
        assert record.author == "Mephisto"
        assert record.subject == "feat: 新增功能"
        assert [f.path for f in record.files] == ["fund_nav/cli.py", "README.md"]

    def test_parses_commit_with_no_files(self) -> None:
        stdout = f"{RS}abc123{FS}Mephisto{FS}2026-06-22T10:00:00+08:00{FS}merge commit\n"
        with patch("subprocess.run", return_value=_fake_completed_process(stdout)):
            records = GitLogReader(Path(".")).read(date(2026, 6, 22))

        assert len(records) == 1
        assert records[0].files == ()

    def test_orders_oldest_to_newest(self) -> None:
        # git log 預設輸出新到舊，reader 需反轉為舊到新。
        stdout = (
            f"{RS}newer{FS}A{FS}2026-06-22T18:00:00+08:00{FS}second\n"
            "b.py\n"
            f"{RS}older{FS}A{FS}2026-06-22T09:00:00+08:00{FS}first\n"
            "a.py\n"
        )
        with patch("subprocess.run", return_value=_fake_completed_process(stdout)):
            records = GitLogReader(Path(".")).read(date(2026, 6, 22))

        assert [r.commit_hash for r in records] == ["older", "newer"]

    def test_empty_output_returns_empty_list(self) -> None:
        with patch("subprocess.run", return_value=_fake_completed_process("")):
            records = GitLogReader(Path(".")).read(date(2026, 6, 22))
        assert records == []

    def test_missing_git_executable_raises(self) -> None:
        with patch("subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(GitCommandError, match="找不到 git"):
                GitLogReader(Path(".")).read(date(2026, 6, 22))

    def test_git_command_failure_raises(self) -> None:
        error = subprocess.CalledProcessError(
            returncode=128, cmd=["git", "log"], stderr="fatal: not a git repository"
        )
        with patch("subprocess.run", side_effect=error):
            with pytest.raises(GitCommandError, match="git log 執行失敗"):
                GitLogReader(Path(".")).read(date(2026, 6, 22))

    def test_invokes_git_with_repo_path_and_date_range(self) -> None:
        with patch(
            "subprocess.run", return_value=_fake_completed_process("")
        ) as mock_run:
            GitLogReader(Path("/tmp/some-repo")).read(date(2026, 6, 22))

        command = mock_run.call_args.args[0]
        assert command[:3] == ["git", "-C", "/tmp/some-repo"]
        assert any("--since=2026-06-22 00:00:00+08:00" in part for part in command)
        assert any("--until=2026-06-22 23:59:59+08:00" in part for part in command)

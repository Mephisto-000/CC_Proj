"""Daily Git History 領域模型測試。"""

from datetime import datetime

from daily_git_history.domain.models import CommitRecord, FileChange


class TestFileChange:
    def test_extension_returns_lowercase_suffix(self) -> None:
        assert FileChange(path="daily_git_history/cli.py").extension == ".py"

    def test_extension_uppercase_normalized_to_lowercase(self) -> None:
        assert FileChange(path="README.MD").extension == ".md"

    def test_extension_empty_for_dotfile(self) -> None:
        assert FileChange(path=".gitignore").extension == ""

    def test_extension_empty_when_no_suffix(self) -> None:
        assert FileChange(path="Makefile").extension == ""

    def test_extension_nested_path(self) -> None:
        assert FileChange(path="fund_nav/domain/models.py").extension == ".py"


class TestCommitRecord:
    def test_sorted_files_orders_by_extension_then_path(self) -> None:
        record = CommitRecord(
            commit_hash="abc123",
            author="Mephisto",
            committed_at=datetime(2026, 6, 22, 19, 0, 0),
            subject="feat: 範例",
            files=(
                FileChange(path="b.py"),
                FileChange(path="README.md"),
                FileChange(path="a.py"),
                FileChange(path=".gitignore"),
            ),
        )
        assert [f.path for f in record.sorted_files] == [
            ".gitignore",
            "README.md",
            "a.py",
            "b.py",
        ]

    def test_default_files_is_empty_tuple(self) -> None:
        record = CommitRecord(
            commit_hash="abc123",
            author="Mephisto",
            committed_at=datetime(2026, 6, 22, 19, 0, 0),
            subject="feat: 範例",
        )
        assert record.files == ()
        assert record.sorted_files == ()

"""Test the PavedPath class."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Generator

import pytest

from paved_path import PavedPath

if TYPE_CHECKING:
    from paved_path import PathableType


class TestConversions:
    """Test that various types of input are correctly converted to a PavedPath."""

    PARAMATERS = (
        (123, "123"),
        (123.456, "123.456"),
        (datetime(2020, 1, 1).astimezone(), "1577865600.0"),
        (date(2020, 1, 1), "2020-01-01"),
        ("abc", "abc"),
        (Path("def"), "def"),
        (PavedPath("hij"), "hij"),
    )

    @pytest.mark.parametrize(("input_value", "expected_output"), PARAMATERS)
    def test_initialize_single(self, input_value: PathableType, expected_output: str) -> None:
        """Test that a value is correctly converted to a PavedPath."""
        assert PavedPath(input_value) == PavedPath(expected_output)

    @pytest.mark.parametrize(("input_value", "expected_output"), PARAMATERS)
    def test_initialize_multiple(self, input_value: PathableType, expected_output: str) -> None:
        """Test that a value is correctly converted to a PavedPath."""
        assert PavedPath(input_value, input_value) == PavedPath(f"{expected_output}/{expected_output}")

    @pytest.mark.parametrize(("input_value", "expected_output"), PARAMATERS)
    def test_append(self, input_value: PathableType, expected_output: str) -> None:
        """Test that a value is correctly converted to a PavedPath."""
        assert PavedPath(input_value) / input_value == PavedPath(f"{expected_output}/{expected_output}")


@pytest.fixture()
def temporary_file() -> Generator[PavedPath, None, None]:
    """Get a file path for testing and delete the test_data folder if it exists after the test."""
    temporary_file = PavedPath("test_data/file.txt")
    yield temporary_file
    if temporary_file.parent == PavedPath("test_data"):
        temporary_file.parent.delete()


class TestUpToDate:
    """Test the up_to_date method."""

    def test_up_to_date_no_file_or_timestamp(self, temporary_file: PavedPath) -> None:
        """Test that up_to_date returns False if the file does not exist and no timestamp is given."""
        assert not temporary_file.up_to_date()
        assert temporary_file.outdated()

    def test_up_to_date_no_file(self, temporary_file: PavedPath) -> None:
        """Test that up_to_date returns False if the file does not exist."""
        timestamp = datetime.now().astimezone()
        assert not temporary_file.up_to_date(timestamp)
        assert temporary_file.outdated(timestamp)

    def test_up_to_date_new_file(self, temporary_file: PavedPath) -> None:
        """Test that up_to_date returns True if the file is newer than the timestamp."""
        timestamp = datetime.now().astimezone()
        temporary_file.write("Text")
        assert temporary_file.up_to_date(timestamp)
        assert not temporary_file.outdated(timestamp)

    def test_up_to_date_old_file(self, temporary_file: PavedPath) -> None:
        """Test that up_to_date returns False if the file is older than the timestamp."""
        temporary_file.write("Text")
        timestamp = datetime.now().astimezone()
        assert not temporary_file.up_to_date(timestamp)
        assert temporary_file.outdated(timestamp)


class TestWrite:
    """Test the write method."""

    def test_write_text(self, temporary_file: PavedPath) -> None:
        """Test that write_text writes a string to a file."""
        # Test empty cache without write_through
        temporary_file.write("abc", write_through=False)
        assert temporary_file.cache.read_text is None

        # Test empty cache with write_through
        temporary_file.write("abc")
        assert temporary_file.cache.read_text == "abc"

        # Test non-empty cache without write_through
        temporary_file.write("def", write_through=False)
        assert temporary_file.cache.read_text is None

        # Test non-empty cache with write_through
        temporary_file.write("def")
        assert temporary_file.cache.read_text == "def"

    def test_write_bytes(self, temporary_file: PavedPath) -> None:
        """Test that write_text writes a bytes to a file."""
        # Test empty cache without write_through
        temporary_file.write(b"abc", write_through=False)
        assert temporary_file.cache.read_bytes is None

        # Test empty cache with write_through
        temporary_file.write(b"abc")
        assert temporary_file.cache.read_bytes == b"abc"

        # Test non-empty cache without write_through
        temporary_file.write(b"def", write_through=False)
        assert temporary_file.cache.read_bytes is None

        # Test non-empty cache with write_through
        temporary_file.write(b"def")
        assert temporary_file.cache.read_bytes == b"def"


class TestDelete:
    """Test the delete method."""

    @pytest.fixture()
    def file_to_delete(self) -> Generator[PavedPath, None, None]:
        """Get a file path for testing and delete it if it exists after the test."""
        file = PavedPath("test_data/file")
        yield file
        file.delete()
        assert not file.exists()

    def test_delete_file_that_does_not_exist(self, file_to_delete: PavedPath) -> None:
        """Test that delete does not raise an error when deleting a file that does not exist."""

    def test_delete_file(self, file_to_delete: PavedPath) -> None:
        """Test that delete deletes a file."""
        file_to_delete.write("Text")

    def test_delete_empty_folder(self, file_to_delete: PavedPath) -> None:
        """Test that delete deletes an empty folder."""
        file_to_delete.mkdir()

    def test_delete_non_empty_folder(self, file_to_delete: PavedPath) -> None:
        """Test that delete deletes a non-empty folder."""
        (file_to_delete / "subfile").write("Text")


class TestRead:
    """Test the cached read methods."""

    def make_initial_file(self) -> PavedPath:
        """Create a file with initial content."""
        file = PavedPath("tests/test_cached_read.txt")
        file.write("123")
        return file

    def test_read_text(self, temporary_file: PavedPath) -> None:
        """Test that read_text reads a file."""
        # Test reading text
        temporary_file.write("123")
        new_file = PavedPath(temporary_file)
        assert new_file.read_text_cached(reload=True) == "123"
        assert new_file.cache.read_text == "123"

        # Test reading byte
        temporary_file.write(b"123")
        new_file = PavedPath(temporary_file)
        assert new_file.read_bytes_cached(reload=True) == b"123"
        assert new_file.cache.read_bytes == b"123"

"""Test the PavedPath class."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from src.paved_path import PavedPath

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    TestFileLambda = Callable[[Any], PavedPath]


# There once was an issue where the way a PavedPath was initialized would affect
# how the cache worked. Testing all 3 of these different ways of creating a
# PavedPath object should help prevent that from happening in the future.
TEMP_DIR_NAME = PavedPath(__file__).parent / "data"
TEST_FILES: tuple[TestFileLambda, TestFileLambda, TestFileLambda] = (
    lambda request: PavedPath(f"{TEMP_DIR_NAME}/{request.node.originalname}"),
    lambda request: PavedPath(TEMP_DIR_NAME, request.node.originalname),
    lambda request: PavedPath(TEMP_DIR_NAME) / request.node.originalname,
)


@pytest.fixture(params=TEST_FILES, name="temp_path")
def temp_path_fixture(
    request: pytest.FixtureRequest,
) -> Generator[PavedPath, Any, Any]:
    """Create a clean state for a temporary PavedPath, yield it, and clean up."""
    temporary_file: PavedPath = request.param(request)
    if temporary_file.parent == Path(TEMP_DIR_NAME):
        temporary_file.parent.delete_dir()
    yield temporary_file
    temporary_file.delete_file()
    if temporary_file.parent.exists():
        temporary_file.parent.rmdir()


class TestInputs:
    UNAWARE_DATETIME = datetime(2020, 1, 1)  # noqa: DTZ001 - Unaware datetime needed for testing
    AWARE_DATETIME = UNAWARE_DATETIME.astimezone()
    INPUTS = (
        ("", ""),  # Test blank string
        (".", "."),  # Test dot string
        (123, "123"),  # Test integers
        (123.456, "123.456"),  # Test floats
        (UNAWARE_DATETIME, "2020-01-01, 00-00-00.000000"),  # Test unaware datetimes
        (AWARE_DATETIME, "2020-01-01, 00-00-00.000000"),  # Test aware datetimes
        (date(2020, 1, 1), "2020-01-01"),  # Test dates
        ("abc", "abc"),  # Test strings
        ("abc.def", "abc.def"),  # Test file extension
        ("abc/def", "abc/def"),  # Test subfolder
        ("abc/def.ghi", "abc/def.ghi"),  # Test subfolder and file extension
        (Path("abc"), "abc"),  # Test Paths
        (PavedPath("abc"), "abc"),  # Test PavedPaths
    )

    @pytest.mark.parametrize(("test_input", "expected"), INPUTS)
    def test_inputs(self, test_input: str, expected: str) -> None:
        assert PavedPath(test_input) == Path(expected)
        assert PavedPath(test_input, test_input) == Path(expected, expected)
        assert PavedPath(test_input) / test_input == Path(expected) / expected

    def test_blank(self) -> None:
        assert PavedPath() == Path()


class TestUpToDateAndOutdated:
    def test_up_to_date_no_file_or_timestamp(self, temp_path: PavedPath) -> None:
        assert not temp_path.is_up_to_date()
        assert temp_path.is_outdated()

    def test_up_to_date_no_timestamp(self, temp_path: PavedPath) -> None:
        temp_path.write_text("Text")
        assert temp_path.is_up_to_date()
        assert not temp_path.is_outdated()

    def test_up_to_date_no_file(self, temp_path: PavedPath) -> None:
        timestamp = datetime.now().astimezone()
        assert not temp_path.is_up_to_date(timestamp)
        assert temp_path.is_outdated(timestamp)

    def test_up_to_date_new_file(self, temp_path: PavedPath) -> None:
        timestamp = datetime.now().astimezone()
        temp_path.write_text("Text")
        assert temp_path.is_up_to_date(timestamp)
        assert not temp_path.is_outdated(timestamp)

    def test_up_to_date_old_file(self, temp_path: PavedPath) -> None:
        temp_path.write_text("Text")
        timestamp = datetime.now().astimezone()
        assert temp_path.is_outdated(timestamp)
        assert not temp_path.is_up_to_date(timestamp)


class TestReadText:
    def test_read_text(self, temp_path: PavedPath) -> None:
        # Test reading a file
        temp_path.write_text("1")
        write_timestamp = temp_path.cache_timestamp
        read_path = PavedPath(temp_path)
        assert read_path.read_text() == "1"
        assert read_path.is_outdated(write_timestamp)

    def test_read_text_cache(self, temp_path: PavedPath) -> None:
        temp_path.write_text("1")
        read_path = PavedPath(temp_path)
        read_path.read_text()
        starting_timestamp = read_path.cache_timestamp
        temp_path.write_text("2")
        assert read_path.read_text() == "1"
        assert starting_timestamp == read_path.cache_timestamp

    def test_read_text_reload(self, temp_path: PavedPath) -> None:
        temp_path.write_text("1")
        read_path = PavedPath(temp_path)
        read_path.read_text()
        temp_path.write_text("2")
        assert read_path.read_text(reload=True) == "2"
        assert read_path.is_outdated(read_path.cache_timestamp)

    def test_read_text_check_file(self, temp_path: PavedPath) -> None:
        temp_path.write_text("1")
        read_path = PavedPath(temp_path)
        temp_path.write_text("2")
        assert read_path.read_text(check_file=True) == "2"
        assert read_path.is_outdated(read_path.cache_timestamp)

    def test_read_text_missing_file(self, temp_path: PavedPath) -> None:
        missing_file = PavedPath(temp_path / "missing")
        with pytest.raises(FileNotFoundError):
            missing_file.read_text()


class TestReadByte:
    def test_read_bytes(self, temp_path: PavedPath) -> None:
        # Test reading a file
        temp_path.write_bytes(b"1")
        write_timestamp = temp_path.cache_timestamp
        read_path = PavedPath(temp_path)
        assert read_path.read_bytes() == b"1"
        assert read_path.is_outdated(write_timestamp)

    def test_read_bytes_cache(self, temp_path: PavedPath) -> None:
        temp_path.write_bytes(b"1")
        read_path = PavedPath(temp_path)
        read_path.read_bytes()
        starting_timestamp = read_path.cache_timestamp
        temp_path.write_bytes(b"2")
        assert read_path.read_bytes() == b"1"
        assert starting_timestamp == read_path.cache_timestamp

    def test_read_bytes_reload(self, temp_path: PavedPath) -> None:
        temp_path.write_bytes(b"1")
        read_path = PavedPath(temp_path)
        read_path.read_bytes()
        temp_path.write_bytes(b"2")
        assert read_path.read_bytes(reload=True) == b"2"
        assert read_path.is_outdated(read_path.cache_timestamp)

    def test_read_bytes_check_file(self, temp_path: PavedPath) -> None:
        temp_path.write_bytes(b"1")
        read_path = PavedPath(temp_path)
        temp_path.write_bytes(b"2")
        assert read_path.read_bytes(check_file=True) == b"2"
        assert read_path.is_outdated(read_path.cache_timestamp)

    def test_read_bytes_missing_file(self, temp_path: PavedPath) -> None:
        missing_file = PavedPath(temp_path / "missing")
        with pytest.raises(FileNotFoundError):
            missing_file.read_bytes()


class TestClearCache:
    def test_clear_cache_text(self, temp_path: PavedPath) -> None:
        temp_path.write_text("1")
        temp_path.clear_cache()
        assert temp_path.cached_read_text is None

    def test_clear_cache_bytes(self, temp_path: PavedPath) -> None:
        temp_path.write_bytes(b"1")
        temp_path.clear_cache()
        assert temp_path.cached_read_bytes is None


class TestWriteText:
    def test_write_text(self, temp_path: PavedPath) -> None:
        temp_path.write_text("1")
        assert temp_path.cached_read_text == "1"

    def test_write_text_filled_cache(self, temp_path: PavedPath) -> None:
        temp_path.write_text("1")
        temp_path.write_text("2", write_through=False)
        assert temp_path.cached_read_text is None

    def test_write_text_empty_cache_no_write_through(
        self, temp_path: PavedPath,
    ) -> None:
        temp_path.write_text("1", write_through=False)
        assert temp_path.cached_read_text is None

    def test_write_text_filled_cache_no_write_through(
        self, temp_path: PavedPath,
    ) -> None:
        temp_path.write_text("1")
        temp_path.write_text("2")
        assert temp_path.cached_read_text == "2"


class TestWriteBytes:
    def test_write_bytes(self, temp_path: PavedPath) -> None:
        temp_path.write_bytes(b"1")
        assert temp_path.cached_read_bytes == b"1"

    def test_write_bytes_filled_cache(self, temp_path: PavedPath) -> None:
        temp_path.write_bytes(b"1")
        temp_path.write_bytes(b"2", write_through=False)
        assert temp_path.cached_read_bytes is None

    def test_write_bytes_empty_cache_no_write_through(
        self, temp_path: PavedPath,
    ) -> None:
        temp_path.write_bytes(b"1", write_through=False)
        assert temp_path.cached_read_bytes is None

    def test_write_bytes_filled_cache_no_write_through(
        self, temp_path: PavedPath,
    ) -> None:
        temp_path.write_bytes(b"1")
        temp_path.write_bytes(b"2")
        assert temp_path.cached_read_bytes == b"2"


class TestDelete:
    def test_delete_file_that_does_not_exist(self, temp_path: PavedPath) -> None:
        temp_path.delete_file()
        assert not temp_path.exists()

    def test_delete_folder_that_does_not_exist(self, temp_path: PavedPath) -> None:
        temp_path.delete_dir()
        assert not temp_path.exists()

    def test_delete_file(self, temp_path: PavedPath) -> None:
        temp_path.write_text("Text")
        temp_path.delete_file()
        assert not temp_path.exists()

    def test_delete_empty_folder(self, temp_path: PavedPath) -> None:
        temp_path.mkdir(parents=True)
        temp_path.delete_dir()
        assert not temp_path.exists()

    def test_delete_non_empty_folder(self, temp_path: PavedPath) -> None:
        (temp_path / "file").write_text("Text")
        temp_path.delete_dir()
        assert not temp_path.exists()

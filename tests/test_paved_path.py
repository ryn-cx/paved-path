from __future__ import annotations

import tempfile
from datetime import date, datetime
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING, Any

import pytest

from paved_path import PavedPath

if TYPE_CHECKING:
    from collections.abc import Generator


def cache_is_empty(temp_path: PavedPath) -> bool:
    """Check if the cache is empty."""
    return (
        temp_path.cached_text is None
        and temp_path.cached_bytes is None
        and temp_path.cache_timestamp is None
    )


@pytest.fixture(name="temp_path")
def temp_path_fixture() -> Generator[PavedPath, Any, Any]:
    """Create a clean state for a temporary PavedPath, yield it, and clean up."""
    temp = tempfile.TemporaryDirectory()
    yield PavedPath(temp.name)
    temp.cleanup()


@pytest.fixture(name="temp_file")
def temp_file_fixture(temp_path: PavedPath) -> PavedPath:
    """Create a clean state for a temporary PavedPath file, yield it, and clean up."""
    return temp_path / temp_path.name


class TestInputs:
    UNAWARE_DATETIME = datetime(2020, 1, 1)  # noqa: DTZ001 - Unaware datetime needed for testing
    AWARE_DATETIME = UNAWARE_DATETIME.astimezone()
    INPUTS = (
        ("", ""),  # Test blank string
        (".", "."),  # Test dot string
        ("..", ".."),  # Test double dot string
        (123, "123"),  # Test integers
        (123.456, "123.456"),  # Test floats
        (datetime(2020, 1, 1), "2020-01-01, 00-00-00.000000"),  # noqa: DTZ001
        (datetime(2020, 1, 1).astimezone(), "2020-01-01, 00-00-00.000000"),
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
    def test_up_to_date_no_file_or_timestamp(self, temp_file: PavedPath) -> None:
        assert not temp_file.is_up_to_date()
        assert temp_file.is_outdated()

    def test_up_to_date_no_timestamp(self, temp_file: PavedPath) -> None:
        temp_file.write_text("Text")
        assert temp_file.is_up_to_date()
        assert not temp_file.is_outdated()

    def test_up_to_date_no_file(self, temp_file: PavedPath) -> None:
        timestamp = datetime.now().astimezone()
        assert not temp_file.is_up_to_date(timestamp)
        assert temp_file.is_outdated(timestamp)

    def test_up_to_date_new_file(self, temp_file: PavedPath) -> None:
        timestamp = datetime.now().astimezone()
        sleep(0.001)
        temp_file.write_text("Text")
        assert temp_file.is_up_to_date(timestamp)
        assert not temp_file.is_outdated(timestamp)

    def test_up_to_date_old_file(self, temp_file: PavedPath) -> None:
        temp_file.write_text("Text")
        sleep(0.001)
        timestamp = datetime.now().astimezone()
        assert temp_file.is_outdated(timestamp)
        assert not temp_file.is_up_to_date(timestamp)


class TestRead:
    def test_read_text(self, temp_file: PavedPath) -> None:
        temp_file.write_text("1")
        alt_file = PavedPath(temp_file)
        assert alt_file.read_text() == "1"
        assert alt_file.cached_bytes is None

    def test_read_bytes(self, temp_file: PavedPath) -> None:
        temp_file.write_bytes(b"1")
        alt_file = PavedPath(temp_file)
        assert alt_file.read_bytes() == b"1"
        assert alt_file.cached_text is None

    def test_read_text_bypass_cache(self, temp_file: PavedPath) -> None:
        temp_file.write_text("1")
        alt_file = PavedPath(temp_file)
        assert alt_file.read_text(bypass_cache=True) == "1"
        assert cache_is_empty(alt_file)

    def test_read_bytes_bypass_cache(self, temp_file: PavedPath) -> None:
        temp_file.write_bytes(b"1")
        alt_file = PavedPath(temp_file)
        assert alt_file.read_bytes(bypass_cache=True) == b"1"
        assert cache_is_empty(alt_file)

    def test_read_text_cache(self, temp_file: PavedPath) -> None:
        """Make sure the file cache is used when reading a file a second time."""
        temp_file.write_text("1")
        alt_file = PavedPath(temp_file)
        sleep(0.001)
        alt_file.write_text("2")
        assert temp_file.read_text() == "1"
        assert alt_file.cache_timestamp
        assert temp_file.cache_timestamp
        assert temp_file.cache_timestamp < alt_file.cache_timestamp

    def test_read_bytes_from_cache(self, temp_file: PavedPath) -> None:
        """Make sure the file cache is used when reading a file a second time."""
        temp_file.write_bytes(b"1")
        alt_file = PavedPath(temp_file)
        sleep(0.001)
        alt_file.write_bytes(b"2")
        assert temp_file.read_bytes() == b"1"
        assert alt_file.cache_timestamp
        assert temp_file.cache_timestamp
        assert temp_file.cache_timestamp < alt_file.cache_timestamp

    def test_read_text_reload(self, temp_file: PavedPath) -> None:
        """Make sure the file cache reloads correctly."""
        temp_file.write_text("1")
        alt_file = PavedPath(temp_file)
        sleep(0.001)
        alt_file.write_text("2")
        assert temp_file.read_text(reload=True) == "2"
        assert alt_file.cache_timestamp
        assert temp_file.cache_timestamp
        assert alt_file.cache_timestamp == temp_file.cache_timestamp

    def test_read_bytes_reload(self, temp_file: PavedPath) -> None:
        """Make sure the file cache reloads correctly."""
        temp_file.write_bytes(b"1")
        alt_file = PavedPath(temp_file)
        sleep(0.001)
        alt_file.write_bytes(b"2")
        assert temp_file.read_bytes(reload=True) == b"2"
        assert alt_file.cache_timestamp
        assert temp_file.cache_timestamp
        assert alt_file.cache_timestamp == temp_file.cache_timestamp

    def test_read_text_check_file(self, temp_file: PavedPath) -> None:
        temp_file.write_text("1")
        alt_file = PavedPath(temp_file)
        sleep(0.001)
        alt_file.write_text("2")
        assert temp_file.read_text(check_file=True) == "2"
        assert alt_file.cache_timestamp
        assert temp_file.cache_timestamp
        assert temp_file.cache_timestamp == alt_file.cache_timestamp

    def test_read_bytes_check_file(self, temp_file: PavedPath) -> None:
        temp_file.write_bytes(b"1")
        alt_file = PavedPath(temp_file)
        sleep(0.001)
        alt_file.write_bytes(b"2")
        assert temp_file.read_bytes(check_file=True) == b"2"
        assert alt_file.cache_timestamp
        assert temp_file.cache_timestamp
        assert temp_file.cache_timestamp == alt_file.cache_timestamp

    def test_read_text_missing_file(self, temp_file: PavedPath) -> None:
        with pytest.raises(FileNotFoundError):
            temp_file.read_text()

    def test_read_bytes_missing_file(self, temp_file: PavedPath) -> None:
        with pytest.raises(FileNotFoundError):
            temp_file.read_bytes()


class TestClearCache:
    def test_clear_cache_text(self, temp_file: PavedPath) -> None:
        temp_file.write_text("1")
        temp_file.clear_cache()
        assert cache_is_empty(temp_file)

    def test_clear_cache_bytes(self, temp_file: PavedPath) -> None:
        temp_file.write_bytes(b"1")
        temp_file.clear_cache()
        assert cache_is_empty(temp_file)


class TestWrite:
    def test_write_text(self, temp_file: PavedPath) -> None:
        temp_file.write_text("1")
        assert temp_file.cached_text == "1"
        assert temp_file.cached_bytes is None
        assert temp_file.cache_timestamp

    def test_write_bytes(self, temp_file: PavedPath) -> None:
        temp_file.write_bytes(b"1")
        assert temp_file.cached_bytes == b"1"
        assert temp_file.cached_text is None
        assert temp_file.cache_timestamp

    def test_write_text_filled_cache(self, temp_file: PavedPath) -> None:
        temp_file.write_text("1")
        original_timestamp = temp_file.cache_timestamp
        sleep(0.001)
        temp_file.write_text("2")
        assert temp_file.cached_text == "2"
        assert temp_file.cached_bytes is None
        assert temp_file.cache_timestamp
        assert original_timestamp
        assert temp_file.cache_timestamp > original_timestamp

    def test_write_bytes_filled_cache(self, temp_file: PavedPath) -> None:
        temp_file.write_bytes(b"1")
        original_timestamp = temp_file.cache_timestamp
        sleep(0.001)
        temp_file.write_bytes(b"2")
        assert temp_file.cached_bytes == b"2"
        assert temp_file.cached_text is None
        assert temp_file.cache_timestamp
        assert original_timestamp
        assert temp_file.cache_timestamp > original_timestamp

    def test_write_text_empty_cache_bypass(
        self,
        temp_file: PavedPath,
    ) -> None:
        temp_file.write_text("1", bypass_cache=True)
        assert cache_is_empty(temp_file)

    def test_write_bytes_empty_cache_bypass(
        self,
        temp_file: PavedPath,
    ) -> None:
        temp_file.write_bytes(b"1", bypass_cache=True)
        assert cache_is_empty(temp_file)

    def test_write_text_full_cache_bypass(
        self,
        temp_file: PavedPath,
    ) -> None:
        temp_file.write_text("1")
        temp_file.write_text("2", bypass_cache=True)
        assert cache_is_empty(temp_file)

    def test_write_bytes_full_cache_bypass(
        self,
        temp_file: PavedPath,
    ) -> None:
        temp_file.write_bytes(b"1")
        temp_file.write_bytes(b"2", bypass_cache=True)
        assert cache_is_empty(temp_file)


class TestDelete:
    def test_unlink_path_that_does_not_exist(self, temp_file: PavedPath) -> None:
        with pytest.raises(FileNotFoundError):
            temp_file.unlink()

    def test_rmdir_path_that_does_not_exist(self, temp_file: PavedPath) -> None:
        with pytest.raises(FileNotFoundError):
            temp_file.rmdir()

    def test_rmdtree_path_that_does_not_exist(self, temp_file: PavedPath) -> None:
        with pytest.raises(FileNotFoundError):
            temp_file.rmtree()

    def test_delete_file(self, temp_file: PavedPath) -> None:
        temp_file.write_text("1")
        temp_file.unlink()
        assert not temp_file.exists()
        assert cache_is_empty(temp_file)

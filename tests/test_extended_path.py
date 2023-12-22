from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from paved_path import PavedPath

if TYPE_CHECKING:
    from paved_path import PathableType


class TestConversions:
    @pytest.mark.parametrize(
        "input_value,expected_output",
        [
            (datetime(2020, 1, 1).timestamp(), "1577865600.0"),
            (date(2020, 1, 1), "2020-01-01"),
            (123.456, "123.456"),
            (123, "123"),
            (Path("abc"), "abc"),
            (PavedPath("abc"), "abc"),
        ],
    )
    def test_conversion(self, input_value: PathableType, expected_output: str):
        """Test that various types of input are correctly converted to a PavedPath."""
        assert PavedPath(input_value) == PavedPath(expected_output)


class TestUpToDate:
    def test_up_to_date_no_file(self):
        timestamp = datetime.now()
        file = PavedPath("Temp Test Files/test_up_to_date_no_file.ext")
        file.parent.delete()
        assert not file.up_to_date(timestamp)

    def test_up_to_date_no_file_or_timestamp(self):
        file = PavedPath("Temp Test Files/test_up_to_date_no_file.ext")
        file.parent.delete()
        assert not file.up_to_date()

    def test_up_to_date_new_file(self):
        timestamp = datetime.now()
        file = PavedPath("Temp Test Files/test_up_to_date_new_file.ext")
        file.write("Text")
        assert file.up_to_date(timestamp)
        file.parent.delete()

    def test_up_to_date_old_file(self):
        file = PavedPath("Temp Test Files/test_up_to_date_old_file.ext")
        file.write("Text")
        timestamp = datetime.now()
        assert not file.up_to_date(timestamp)
        file.parent.delete()


class TestWrite:
    def test_write_binary(self):
        file = PavedPath("Temp Test Files/test_write_binary.ext")
        file.write(b"Text")
        assert file.read_bytes() == b"Text"
        file.parent.delete()

    def test_write_text(self):
        file = PavedPath("Temp Test Files/test_write_text.ext")
        file.write("Text")
        assert file.read_text(encoding="utf-8") == "Text"
        file.parent.delete()


class TestDelete:
    def delete_file(self):
        file = PavedPath("Temp Test Files/test_delete_file.ext")
        file.write("Text")
        file.delete()
        assert file.exists()

    def delete_empty_folder(self):
        folder = PavedPath("Temp Test Files/test_delete_empty_folder")
        folder.mkdir()
        folder.delete()
        assert folder.exists()

    def delete_non_empty_folder(self):
        folder = PavedPath("Temp Test Files/test_delete_non_empty_folder")
        folder.mkdir()
        file = folder / "test_delete_non_empty_folder.ext"
        file.write("Text")
        folder.delete()
        assert folder.exists()


class TestCachedRead:
    def make_initial_file(self):
        file = PavedPath("tests/test_cached_read.txt")
        file.write("123")
        return file

    def test_read_text(self):
        file = self.make_initial_file()
        assert file.read_text_cached() == "123"
        file.delete()

    def test_read_text_changed_file(self):
        file = self.make_initial_file()
        file.read_text_cached()
        file.write("456")
        assert file.read_text_cached() == "123"
        file.delete()

    def test_read_text_updating_cache(self):
        file = self.make_initial_file()
        file.read_text_cached()
        file.write("456")
        assert file.read_text_cached(True) == "456"
        file.delete()

    def test_read_bytes(self):
        file = self.make_initial_file()
        assert file.read_bytes_cached() == b"123"
        file.delete()

    def test_read_bytes_changed_file(self):
        file = self.make_initial_file()
        file.read_bytes_cached()
        file.write("456")
        assert file.read_bytes_cached() == b"123"
        file.delete()

    def test_read_bytes_updating_cache(self):
        file = self.make_initial_file()
        file.read_bytes_cached()
        file.write("456")
        assert file.read_bytes_cached(True) == b"456"
        file.delete()

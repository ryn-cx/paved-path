from __future__ import annotations

import json
import tempfile
from time import sleep
from typing import TYPE_CHECKING, Any

import pytest

from paved_path import JSONFile

if TYPE_CHECKING:
    from collections.abc import Generator


def json_cache_is_empty(temp_path: JSONFile) -> bool:
    """Check if the JSONFile cache is empty."""
    return (
        temp_path.cached_text is None
        and temp_path.cached_bytes is None
        and temp_path.cached_json is None
        and temp_path.cache_timestamp is None
    )


@pytest.fixture(name="json_temp_path")
def json_temp_path_fixture() -> Generator[JSONFile, Any, Any]:
    """Create a clean state for a temporary JSONFile path, yield it, and clean up."""
    temp = tempfile.TemporaryDirectory()
    yield JSONFile(temp.name)
    temp.cleanup()


@pytest.fixture(name="temp_json_file")
def temp_json_file_fixture(json_temp_path: JSONFile) -> JSONFile:
    """Create a clean state for a temporary JSONFile file, yield it, and clean up."""
    return (json_temp_path / json_temp_path.name).with_suffix(".json")


class TestJSONFileRead:
    def test_read(self, temp_json_file: JSONFile) -> None:
        test_input = {"key": "value"}
        temp_json_file.write_json(test_input)
        alt_file = JSONFile(temp_json_file)
        assert alt_file.read_json() == test_input
        assert alt_file.cached_text == json.dumps(test_input)
        assert alt_file.cached_bytes is None

    def test_read_bypass_cache(self, temp_json_file: JSONFile) -> None:
        test_input = {"key": "value"}
        temp_json_file.write_json(test_input)
        alt_file = JSONFile(temp_json_file)
        assert alt_file.read_text(bypass_cache=True) == json.dumps(test_input)
        assert json_cache_is_empty(alt_file)

    def test_read_json_from_cache(self, temp_json_file: JSONFile) -> None:
        """Make sure the file cache is used when reading a file a second time."""
        test_data1 = {"key": "value1"}
        test_data2 = {"key": "value2"}
        temp_json_file.write_json(test_data1)
        alt_file = JSONFile(temp_json_file)
        sleep(0.001)
        alt_file.write_json(test_data2)
        assert temp_json_file.read_json() == test_data1
        assert alt_file.cache_timestamp
        assert temp_json_file.cache_timestamp
        assert temp_json_file.cache_timestamp < alt_file.cache_timestamp

    def test_read_json_reload(self, temp_json_file: JSONFile) -> None:
        """Make sure the file cache reloads correctly."""
        test_data1 = {"key": "value1"}
        test_data2 = {"key": "value2"}
        temp_json_file.write_json(test_data1)
        alt_file = JSONFile(temp_json_file)
        sleep(0.001)
        alt_file.write_json(test_data2)
        assert temp_json_file.read_json(reload=True) == test_data2
        assert alt_file.cache_timestamp
        assert temp_json_file.cache_timestamp
        assert alt_file.cache_timestamp == temp_json_file.cache_timestamp

    def test_read_json_check_file(self, temp_json_file: JSONFile) -> None:
        test_data1 = {"key": "value1"}
        test_data2 = {"key": "value2"}
        temp_json_file.write_json(test_data1)
        alt_file = JSONFile(temp_json_file)
        sleep(0.001)
        alt_file.write_json(test_data2)
        assert temp_json_file.read_json(check_file=True) == test_data2
        assert alt_file.cache_timestamp
        assert temp_json_file.cache_timestamp
        assert temp_json_file.cache_timestamp == alt_file.cache_timestamp

    def test_read_json_missing_file(self, temp_json_file: JSONFile) -> None:
        with pytest.raises(FileNotFoundError):
            temp_json_file.read_json()


class TestJSONFileClearCache:  # pylint: disable=R0903
    def test_clear_cache_json(self, temp_json_file: JSONFile) -> None:
        test_data = {"key": "value"}
        temp_json_file.write_json(test_data)
        temp_json_file.clear_cache()
        assert json_cache_is_empty(temp_json_file)


class TestJSONFileWrite:
    @pytest.mark.parametrize(("test_input"), [{"key": "value"}, ["value1", "value2"]])
    def test_write_json(
        self,
        test_input: dict[str, str] | list[str],
        temp_json_file: JSONFile,
    ) -> None:
        temp_json_file.write_json(test_input)
        assert temp_json_file.cached_json == test_input
        assert temp_json_file.cached_text == json.dumps(test_input)
        assert temp_json_file.cached_bytes is None
        assert temp_json_file.cache_timestamp

    @pytest.mark.parametrize(("test_input"), [{"key": "value"}, ["value1", "value2"]])
    def test_write_json_string(
        self,
        test_input: dict[str, str] | list[str],
        temp_json_file: JSONFile,
    ) -> None:
        """Test writing JSON as a string."""
        string_test_data = json.dumps(test_input)
        temp_json_file.write_json(string_test_data)
        assert temp_json_file.cached_json == test_input
        assert temp_json_file.cached_text == string_test_data
        assert temp_json_file.cached_bytes is None
        assert temp_json_file.cache_timestamp

    def test_write_json_filled_cache(self, temp_json_file: JSONFile) -> None:
        test_data1 = {"key": "value"}
        test_data2 = ["value1", "value2"]
        temp_json_file.write_json(test_data1)
        original_timestamp = temp_json_file.cache_timestamp
        sleep(0.001)
        temp_json_file.write_json(test_data2)
        assert temp_json_file.cached_json == test_data2
        assert temp_json_file.cached_text == json.dumps(test_data2)
        assert temp_json_file.cached_bytes is None
        assert temp_json_file.cache_timestamp
        assert original_timestamp
        assert temp_json_file.cache_timestamp > original_timestamp

    def test_write_json_empty_cache_bypass(
        self,
        temp_json_file: JSONFile,
    ) -> None:
        test_data = {"key": "value"}
        temp_json_file.write_json(test_data, bypass_cache=True)
        assert json_cache_is_empty(temp_json_file)

    def test_write_json_full_cache_bypass(
        self,
        temp_json_file: JSONFile,
    ) -> None:
        test_data1 = {"key": "value1"}
        test_data2 = ["value1", "value2"]
        temp_json_file.write_json(test_data1)
        temp_json_file.write_json(test_data2, bypass_cache=True)
        assert json_cache_is_empty(temp_json_file)

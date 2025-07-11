from __future__ import annotations

import json
import tempfile
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING, Any

import pytest

from paved_path import JSONFile

if TYPE_CHECKING:
    from collections.abc import Generator


def cache_is_empty(temp_path: JSONFile) -> bool:
    """Check if the cache is empty."""
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
        """Test reading a file and filling the cache."""
        test_data = {"key": "value"}
        Path(temp_json_file).write_text(json.dumps(test_data))

        assert temp_json_file.read_json() == test_data
        assert temp_json_file.cached_text == json.dumps(test_data)
        assert temp_json_file.cached_bytes is None

    def test_read_json_from_cache(self, temp_json_file: JSONFile) -> None:
        """Test that the cache is used when reading a file a second time."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        Path(temp_json_file).write_text(json.dumps(test_data_1))
        temp_json_file.read_json()
        sleep(0.001)
        Path(temp_json_file).write_text(json.dumps(test_data_2))

        assert temp_json_file.read_json() == test_data_1
        assert temp_json_file.cache_timestamp
        assert temp_json_file.cache_timestamp < temp_json_file.aware_mtime()

    def test_read_json_reload(self, temp_json_file: JSONFile) -> None:
        """Test that the cache is reloaded when reload=True."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        Path(temp_json_file).write_text(json.dumps(test_data_1))
        temp_json_file.read_json()
        sleep(0.001)
        Path(temp_json_file).write_text(json.dumps(test_data_2))

        assert temp_json_file.read_json(reload=True) == test_data_2
        assert temp_json_file.cache_timestamp
        assert temp_json_file.cache_timestamp == temp_json_file.aware_mtime()

    def test_read_json_check_file(self, temp_json_file: JSONFile) -> None:
        """Test that the cache is reloaded when check_file=True and the file is new."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        Path(temp_json_file).write_text(json.dumps(test_data_1))
        temp_json_file.read_json()
        sleep(0.001)
        Path(temp_json_file).write_text(json.dumps(test_data_2))

        assert temp_json_file.read_json(check_file=True) == test_data_2
        assert temp_json_file.cache_timestamp
        assert temp_json_file.cache_timestamp == temp_json_file.aware_mtime()

    def test_read_json_missing_file(self, temp_json_file: JSONFile) -> None:
        """Test that reading a missing file raises an error."""
        with pytest.raises(FileNotFoundError):
            temp_json_file.read_json()


class TestJSONFileClearCache:  # pylint: disable=R0903
    def test_clear_cache_json(self, temp_json_file: JSONFile) -> None:
        """Test that clearing the cache works."""
        test_data = {"key": "value"}
        temp_json_file.write_json(test_data)
        temp_json_file.clear_cache()

        assert cache_is_empty(temp_json_file)


class TestJSONFileWrite:
    def test_write_json(self, temp_json_file: JSONFile) -> None:
        """Test that writing to a file works."""
        test_data = {"key": "value"}
        temp_json_file.write_json(test_data)

        assert Path(temp_json_file).read_text() == json.dumps(test_data)
        assert temp_json_file.cached_text == json.dumps(test_data)
        assert temp_json_file.cached_bytes is None
        assert temp_json_file.cached_json is None
        assert temp_json_file.cache_timestamp == temp_json_file.aware_mtime()

    def test_write_json_filled_cache(self, temp_json_file: JSONFile) -> None:
        """Test that writing to a file works when the cache is full."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        temp_json_file.write_json(test_data_1)
        sleep(0.001)
        temp_json_file.write_json(test_data_2)

        assert Path(temp_json_file).read_text() == json.dumps(test_data_2)
        assert temp_json_file.cached_text == json.dumps(test_data_2)
        assert temp_json_file.cached_bytes is None
        assert temp_json_file.cached_json is None
        assert temp_json_file.cache_timestamp == temp_json_file.aware_mtime()

    def test_write_json_extra_parameters(self, temp_json_file: JSONFile) -> None:
        """Test that writing to a file with extra parameters works."""
        test_data = {JSONFile(): "value"}

        parameters_dump = json.dumps(test_data, skipkeys=True)
        with pytest.raises(TypeError):
            json.dumps(test_data)

        expected_data = json.loads(parameters_dump)
        temp_json_file.write_json(test_data, skipkeys=True)

        assert temp_json_file.read_json() == expected_data

from __future__ import annotations

import tempfile
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING, Any

import pytest
import yaml

from paved_path import YAMLFile

if TYPE_CHECKING:
    from collections.abc import Generator


def yaml_cache_is_empty(temp_path: YAMLFile) -> bool:
    """Check if the YAMLFile cache is empty."""
    return (
        temp_path.cached_text is None
        and temp_path.cached_bytes is None
        and temp_path.cached_yaml is None
        and temp_path.cache_timestamp is None
    )


@pytest.fixture(name="yaml_temp_path")
def yaml_temp_path_fixture() -> Generator[YAMLFile, Any, Any]:
    """Create a clean state for a temporary YAMLFile path, yield it, and clean up."""
    temp = tempfile.TemporaryDirectory()
    yield YAMLFile(temp.name)
    temp.cleanup()


@pytest.fixture(name="temp_yaml_file")
def temp_yaml_file_fixture(yaml_temp_path: YAMLFile) -> YAMLFile:
    """Create a clean state for a temporary YAMLFile file, yield it, and clean up."""
    return (yaml_temp_path / yaml_temp_path.name).with_suffix(".yaml")


class TestYAMLFileRead:
    def test_unsafe_read(self, temp_yaml_file: YAMLFile) -> None:
        """Test reading a file and filling the cache."""
        test_input = {"key": "value"}
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_input))

        assert temp_yaml_file.unsafe_read_yaml() == test_input
        assert temp_yaml_file.cached_text == yaml.safe_dump(test_input)
        assert temp_yaml_file.cached_bytes is None

    def test_read(self, temp_yaml_file: YAMLFile) -> None:
        """Test reading a file and filling the cache."""
        test_input = {"key": "value"}
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_input))

        assert temp_yaml_file.read_yaml() == test_input
        assert temp_yaml_file.cached_text == yaml.safe_dump(test_input)
        assert temp_yaml_file.cached_bytes is None

    def test_unsafe_read_yaml_from_cache(self, temp_yaml_file: YAMLFile) -> None:
        """Test that the cache is used when reading a file a second time."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_data_1))
        temp_yaml_file.unsafe_read_yaml()
        sleep(0.001)
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_data_2))

        assert temp_yaml_file.unsafe_read_yaml() == test_data_1
        assert temp_yaml_file.cache_timestamp
        assert temp_yaml_file.cache_timestamp < temp_yaml_file.aware_mtime()

    def test_read_yaml_from_cache(self, temp_yaml_file: YAMLFile) -> None:
        """Test that the cache is used when reading a file a second time."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_data_1))
        temp_yaml_file.read_yaml()
        sleep(0.001)
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_data_2))

        assert temp_yaml_file.read_yaml(reload=True) == test_data_2
        assert temp_yaml_file.cache_timestamp
        assert temp_yaml_file.cache_timestamp == temp_yaml_file.aware_mtime()

    def test_unsafe_read_yaml_reload(self, temp_yaml_file: YAMLFile) -> None:
        """Test that the cache is reloaded when reload=True."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_data_1))
        temp_yaml_file.unsafe_read_yaml()
        sleep(0.001)
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_data_2))

        assert temp_yaml_file.unsafe_read_yaml(reload=True) == test_data_2
        assert temp_yaml_file.cache_timestamp
        assert temp_yaml_file.cache_timestamp == temp_yaml_file.aware_mtime()

    def test_read_yaml_reload(self, temp_yaml_file: YAMLFile) -> None:
        """Test that the cache is reloaded when reload=True."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_data_1))
        temp_yaml_file.unsafe_read_yaml()
        sleep(0.001)
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_data_2))

        assert temp_yaml_file.unsafe_read_yaml(check_file=True) == test_data_2
        assert temp_yaml_file.cache_timestamp
        assert temp_yaml_file.cache_timestamp == temp_yaml_file.aware_mtime()

    def test_unsafe_read_yaml_check_file(self, temp_yaml_file: YAMLFile) -> None:
        """Test that the cache is reloaded when check_file=True and the file is new."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        temp_yaml_file.write_yaml(test_data_1)
        sleep(0.001)
        YAMLFile(temp_yaml_file).write_yaml(test_data_2)

        assert temp_yaml_file.read_yaml(check_file=True) == test_data_2
        assert temp_yaml_file.cache_timestamp
        assert temp_yaml_file.cache_timestamp == temp_yaml_file.aware_mtime()

    def test_read_yaml_check_file(self, temp_yaml_file: YAMLFile) -> None:
        """Test that the cache is reloaded when check_file=True and the file is new."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_data_1))
        temp_yaml_file.read_yaml()
        sleep(0.001)
        Path(temp_yaml_file).write_text(yaml.safe_dump(test_data_2))

        assert temp_yaml_file.read_yaml(check_file=True) == test_data_2
        assert temp_yaml_file.cache_timestamp
        assert temp_yaml_file.cache_timestamp == temp_yaml_file.aware_mtime()

    def test_read_yaml_missing_file(self, temp_yaml_file: YAMLFile) -> None:
        """Test that reading a missing file raises an error."""
        with pytest.raises(FileNotFoundError):
            temp_yaml_file.read_yaml()

    def test_unsafe_read_yaml_missing_file(self, temp_yaml_file: YAMLFile) -> None:
        """Test that reading a missing file raises an error."""
        with pytest.raises(FileNotFoundError):
            temp_yaml_file.unsafe_read_yaml()


class TestYAMLFileClearCache:  # pylint: disable=R0903
    def test_clear_cache_yaml(self, temp_yaml_file: YAMLFile) -> None:
        """Test that clearing the cache works."""
        test_data = {"key": "value"}
        temp_yaml_file.write_yaml(test_data)
        temp_yaml_file.clear_cache()

        assert yaml_cache_is_empty(temp_yaml_file)


class TestYAMLFileWrite:
    def test_write_json(self, temp_yaml_file: YAMLFile) -> None:
        """Test that writing to a file works."""
        test_data = {"key": "value"}
        temp_yaml_file.write_yaml(test_data)

        assert Path(temp_yaml_file).read_text() == yaml.safe_dump(test_data)
        assert temp_yaml_file.cached_text == yaml.safe_dump(test_data)
        assert temp_yaml_file.cached_bytes is None
        assert temp_yaml_file.cached_yaml is None
        assert temp_yaml_file.cache_timestamp == temp_yaml_file.aware_mtime()

    def test_unsafe_write_yaml(self, temp_yaml_file: YAMLFile) -> None:
        """Test that writing to a file works."""
        test_data = {"key": "value"}
        temp_yaml_file.unsafe_write_yaml(test_data)

        assert Path(temp_yaml_file).read_text() == yaml.safe_dump(test_data)
        assert temp_yaml_file.cached_text == yaml.safe_dump(test_data)
        assert temp_yaml_file.cached_bytes is None
        assert temp_yaml_file.cached_yaml is None
        assert temp_yaml_file.cache_timestamp == temp_yaml_file.aware_mtime()

    def test_write_json_filled_cache(self, temp_yaml_file: YAMLFile) -> None:
        """Test that writing to a file works when the cache is full."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        temp_yaml_file.write_yaml(test_data_1)
        sleep(0.001)
        temp_yaml_file.write_yaml(test_data_2)

        assert Path(temp_yaml_file).read_text() == yaml.safe_dump(test_data_2)
        assert temp_yaml_file.cached_text == yaml.safe_dump(test_data_2)
        assert temp_yaml_file.cached_bytes is None
        assert temp_yaml_file.cached_yaml is None
        assert temp_yaml_file.cache_timestamp == temp_yaml_file.aware_mtime()

    def test_unsafe_write_yaml_filled_cache(self, temp_yaml_file: YAMLFile) -> None:
        """Test that writing to a file works when the cache is full."""
        test_data_1 = {"key_1": "value_1"}
        test_data_2 = {"key_2": "value_2"}
        temp_yaml_file.unsafe_write_yaml(test_data_1)
        sleep(0.001)
        temp_yaml_file.unsafe_write_yaml(test_data_2)

        assert Path(temp_yaml_file).read_text() == yaml.safe_dump(test_data_2)
        assert temp_yaml_file.cached_text == yaml.safe_dump(test_data_2)
        assert temp_yaml_file.cached_bytes is None
        assert temp_yaml_file.cached_yaml is None
        assert temp_yaml_file.cache_timestamp == temp_yaml_file.aware_mtime()

    def test_write_yaml_extra_parameters(self, temp_yaml_file: YAMLFile) -> None:
        """Test that writing to a file with extra parameters works."""
        test_data = [[{"key": "value"}, {"key": "value"}]]
        regular_dump = yaml.safe_dump(test_data)
        parameter_dump = yaml.safe_dump(test_data, indent=4)
        expected_data = yaml.safe_load(parameter_dump)
        temp_yaml_file.write_yaml(test_data, indent=1)

        assert regular_dump != parameter_dump
        assert temp_yaml_file.read_yaml() == expected_data

    def test_unsafe_write_yaml_extra_parameters(self, temp_yaml_file: YAMLFile) -> None:
        """Test that writing to a file with extra parameters works."""
        test_data = [[{"key": "value"}, {"key": "value"}]]
        regular_dump = yaml.safe_dump(test_data)
        parameter_dump = yaml.safe_dump(test_data, indent=4)
        expected_data = yaml.safe_load(parameter_dump)
        temp_yaml_file.unsafe_write_yaml(test_data, indent=1)

        assert regular_dump != parameter_dump
        assert temp_yaml_file.read_yaml() == expected_data

from __future__ import annotations

import tempfile
from time import sleep
from typing import TYPE_CHECKING, Any

import pytest

try:
    import yaml
except ImportError:
    pytest.skip("PyYAML not available", allow_module_level=True)

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
    def test_read(self, temp_yaml_file: YAMLFile) -> None:
        test_input = {"key": "value"}
        temp_yaml_file.safe_write_yaml(test_input)
        alt_file = YAMLFile(temp_yaml_file)
        assert alt_file.read_yaml() == test_input
        assert alt_file.cached_text == yaml.safe_dump(
            test_input,
            default_flow_style=False,
        )
        assert alt_file.cached_bytes is None

    def test_read_bypass_cache(self, temp_yaml_file: YAMLFile) -> None:
        test_input = {"key": "value"}
        temp_yaml_file.safe_write_yaml(test_input)
        alt_file = YAMLFile(temp_yaml_file)
        assert alt_file.read_text(bypass_cache=True) == yaml.safe_dump(
            test_input,
            default_flow_style=False,
        )
        assert yaml_cache_is_empty(alt_file)

    def test_read_yaml_from_cache(self, temp_yaml_file: YAMLFile) -> None:
        """Make sure the file cache is used when reading a file a second time."""
        test_data1 = {"key": "value1"}
        test_data2 = {"key": "value2"}
        temp_yaml_file.safe_write_yaml(test_data1)
        alt_file = YAMLFile(temp_yaml_file)
        sleep(0.001)
        alt_file.safe_write_yaml(test_data2)
        assert temp_yaml_file.read_yaml() == test_data1
        assert alt_file.cache_timestamp
        assert temp_yaml_file.cache_timestamp
        assert temp_yaml_file.cache_timestamp < alt_file.cache_timestamp

    def test_read_yaml_reload(self, temp_yaml_file: YAMLFile) -> None:
        """Make sure the file cache reloads correctly."""
        test_data1 = {"key": "value1"}
        test_data2 = {"key": "value2"}
        temp_yaml_file.safe_write_yaml(test_data1)
        alt_file = YAMLFile(temp_yaml_file)
        sleep(0.001)
        alt_file.safe_write_yaml(test_data2)
        assert temp_yaml_file.read_yaml(reload=True) == test_data2
        assert alt_file.cache_timestamp
        assert temp_yaml_file.cache_timestamp
        assert alt_file.cache_timestamp == temp_yaml_file.cache_timestamp

    def test_read_yaml_check_file(self, temp_yaml_file: YAMLFile) -> None:
        test_data1 = {"key": "value1"}
        test_data2 = {"key": "value2"}
        temp_yaml_file.safe_write_yaml(test_data1)
        alt_file = YAMLFile(temp_yaml_file)
        sleep(0.001)
        alt_file.safe_write_yaml(test_data2)
        assert temp_yaml_file.read_yaml(check_file=True) == test_data2
        assert alt_file.cache_timestamp
        assert temp_yaml_file.cache_timestamp
        assert temp_yaml_file.cache_timestamp == alt_file.cache_timestamp

    def test_read_yaml_missing_file(self, temp_yaml_file: YAMLFile) -> None:
        with pytest.raises(FileNotFoundError):
            temp_yaml_file.read_yaml()


class TestYAMLFileClearCache:  # pylint: disable=R0903
    def test_clear_cache_yaml(self, temp_yaml_file: YAMLFile) -> None:
        test_data = {"key": "value"}
        temp_yaml_file.safe_write_yaml(test_data)
        temp_yaml_file.clear_cache()
        assert yaml_cache_is_empty(temp_yaml_file)


class TestYAMLFileWrite:
    @pytest.mark.parametrize(("test_input"), [{"key": "value"}, ["value1", "value2"]])
    def test_write_yaml(
        self,
        test_input: dict[str, str] | list[str],
        temp_yaml_file: YAMLFile,
    ) -> None:
        temp_yaml_file.safe_write_yaml(test_input)
        assert temp_yaml_file.cached_yaml == test_input
        assert temp_yaml_file.cached_text == yaml.safe_dump(
            test_input,
            default_flow_style=False,
        )
        assert temp_yaml_file.cached_bytes is None
        assert temp_yaml_file.cache_timestamp

    @pytest.mark.parametrize(("test_input"), [{"key": "value"}, ["value1", "value2"]])
    def test_write_yaml_string(
        self,
        test_input: dict[str, str] | list[str],
        temp_yaml_file: YAMLFile,
    ) -> None:
        """Test writing YAML as a string."""
        string_test_data = yaml.safe_dump(test_input, default_flow_style=False)
        temp_yaml_file.safe_write_yaml(string_test_data)
        assert temp_yaml_file.cached_yaml == test_input
        assert temp_yaml_file.cached_text == string_test_data
        assert temp_yaml_file.cached_bytes is None
        assert temp_yaml_file.cache_timestamp

    def test_write_yaml_filled_cache(self, temp_yaml_file: YAMLFile) -> None:
        test_data1 = {"key": "value"}
        test_data2 = ["value1", "value2"]
        temp_yaml_file.safe_write_yaml(test_data1)
        original_timestamp = temp_yaml_file.cache_timestamp
        sleep(0.001)
        temp_yaml_file.safe_write_yaml(test_data2)
        assert temp_yaml_file.cached_yaml == test_data2
        assert temp_yaml_file.cached_text == yaml.safe_dump(
            test_data2,
            default_flow_style=False,
        )
        assert temp_yaml_file.cached_bytes is None
        assert temp_yaml_file.cache_timestamp
        assert original_timestamp
        assert temp_yaml_file.cache_timestamp > original_timestamp

    def test_write_yaml_empty_cache_bypass(
        self,
        temp_yaml_file: YAMLFile,
    ) -> None:
        test_data = {"key": "value"}
        temp_yaml_file.safe_write_yaml(test_data, bypass_cache=True)
        assert yaml_cache_is_empty(temp_yaml_file)

    def test_write_yaml_full_cache_bypass(
        self,
        temp_yaml_file: YAMLFile,
    ) -> None:
        test_data1 = {"key": "value1"}
        test_data2 = ["value1", "value2"]
        temp_yaml_file.safe_write_yaml(test_data1)
        temp_yaml_file.safe_write_yaml(test_data2, bypass_cache=True)
        assert yaml_cache_is_empty(temp_yaml_file)

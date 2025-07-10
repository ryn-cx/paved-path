"""Library for working with YAML files."""

from collections.abc import Mapping
from typing import Any, TypedDict, Unpack, override

import yaml

from .paved_path import PavedPath


class YAMLWriteOptions(TypedDict, total=False):
    default_style: str | None
    default_flow_style: bool | None
    canonical: bool | None
    indent: int | None
    width: float | None  # Not an accurate type hint
    allow_unicode: bool | None
    line_break: str | None
    encoding: str | None
    explicit_start: bool | None
    explicit_end: bool | None
    version: tuple[int, int] | None
    tags: Mapping[str, str] | None
    sort_keys: bool


class YAMLFile(PavedPath):
    """YAML file interface."""

    cached_yaml: Any = None

    @override
    def clear_cache(self) -> None:
        self.cached_yaml = None
        super().clear_cache()

    def safe_write_yaml(
        self,
        data: dict[Any, Any] | list[Any] | str,
        **options: Unpack[YAMLWriteOptions],
    ) -> int:
        """Manage cache, open the yaml file in text mode, read it, and close the file.

        Args:
            data: The data to write to the file.

            **options: Additional options to pass to `yaml.safe_dump`.

        Returns:
            Passed from self.write_text().
        """
        # No write through caches because the content being written may be different
        # after it is dumped to a string or bytes.
        if encoding := options.pop("encoding", None):
            return self.write_bytes(
                yaml.safe_dump(
                    data,
                    stream=None,
                    encoding=str(encoding),
                    **options,
                ),  # type: ignore[reportUnknownArgumentType]
            )

        return self.write_text(
            yaml.safe_dump(
                data,
                stream=None,
                encoding=None,
                **options,
            ),  # type: ignore[reportUnknownArgumentType]
        )

    def safe_read_yaml(
        self,
        *,
        reload: bool = False,
        check_file: bool = False,
    ) -> dict[str, Any] | list[Any]:
        """Read the file in text mode, parse it, and cache the result.

        Args:
            reload: If True read the bytes from the file and update the cache.

            check_file: If True check if the file is newer than the cache and if
                it is reload it.

        Returns:
            The parsed YAML of the file.
        """
        if (
            self.cached_yaml is None
            or reload
            # If the file is up to date that means the file's content is newer than the
            # cache and it needs to be reloaded.
            or (check_file and self.is_up_to_date(self.cache_timestamp))
        ):
            self.cached_yaml = yaml.safe_load(
                self.read_text(
                    reload=reload,
                    check_file=check_file,
                ),
            )

        return self.cached_yaml

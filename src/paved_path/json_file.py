"""Library for working with JSON files."""

import json
from collections.abc import Callable
from typing import Any, TypedDict, Unpack, override

from .paved_path import PavedPath


class JSONDumpOptions(TypedDict, total=False):
    skipkeys: bool
    ensure_ascii: bool
    check_circular: bool
    allow_nan: bool
    cls: type[json.JSONEncoder] | None
    indent: int | None
    separators: tuple[str, str] | None
    default: Callable[[Any], Any] | None
    sort_keys: bool


class JSONLoadOptions(TypedDict, total=False):
    cls: type[json.JSONDecoder] | None
    object_hook: Callable[[dict[Any, Any]], Any] | None
    parse_float: Callable[[str], float] | None
    parse_int: Callable[[str], int] | None
    parse_constant: Callable[[str], Any] | None
    object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] | None


class JSONFile(PavedPath):
    """JSON file interface."""

    cached_json: Any = None

    @override
    def clear_cache(self) -> None:
        self.cached_json = None
        super().clear_cache()

    def write_json(
        self,
        data: Any,  # noqa: ANN401
        **options: Unpack[JSONDumpOptions],
    ) -> int:
        """Manage cache, open the json file in text mode, read it, and close the file.

        Args:
            data: The data to write to the file.

            write_through: If True write the text to the file and the cache. If
                False write the text to the file and clear out the cache so it
                stays in sync.

            **options: Additional options to pass to `json.dumps`.


        Returns:
            Passed from self.write_text().
        """
        # No write through caches because the content being written may be different
        # after it is dumped to a string.
        return self.write_text(json.dumps(data, **options))

    def read_json(
        self,
        *,
        reload: bool = False,
        check_file: bool = False,
        **options: Unpack[JSONLoadOptions],
    ) -> dict[str, Any] | list[Any]:
        """Read the file in text mode, parse it, and cache the result.

        Args:
            reload: If True read the bytes from the file and update the cache.

            check_file: If True check if the file is newer than the cache and if
                it is reload it.

            **options: Additional options to pass to `json.loads`.

        Returns:
            The parsed JSON of the file.
        """
        if (
            self.cached_json is None
            or reload
            # If the file is up to date that means the file's content is newer than the
            # cache and it needs to be reloaded.
            or (check_file and self.is_up_to_date(self.cache_timestamp))
        ):
            self.cached_json = json.loads(
                self.read_text(
                    reload=reload,
                    check_file=check_file,
                ),
                **options,
            )

        return self.cached_json

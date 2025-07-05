"""Library for working with JSON files."""

import json
from typing import Any, override

from .paved_path import PavedPath


class JSONFile(PavedPath):
    """JSON file manager."""

    cached_json: Any = None

    @override
    def clear_cache(self) -> None:
        self.cached_json = None
        super().clear_cache()

    def write_json(
        self,
        data: dict[Any, Any] | list[Any] | str,
        *,
        bypass_cache: bool = False,
    ) -> int:
        """Manage cache, open the json file in text mode, read it, and close the file.

        Args:
            data: The data to write to the file.

            write_through: If True write the text to the file and the cache. If
                False write the text to the file and clear out the cache so it
                stays in sync.

            bypass_cache: If True the cache will be cleared out and not used.


        Returns:
            Passed from self.write_text().
        """
        # If given a string make sure it is valid JSON before writing it.
        if isinstance(data, str):
            data = json.loads(data)

        # Dump and load JSON to make sure Serialization does not cause the
        # loaded file to be different than the file that is being written.
        dumped_json = json.dumps(data)
        read_json = json.loads(dumped_json)
        if read_json != data:
            msg = "Serialization will create an output that is different from the input"
            raise ValueError(msg)

        output = self.write_text(
            dumped_json,
            bypass_cache=bypass_cache,
        )

        if not bypass_cache:
            self.cached_json = data

        return output

    def read_json(
        self,
        *,
        reload: bool = False,
        check_file: bool = False,
        bypass_cache: bool = False,
    ) -> dict[str, Any] | list[Any]:
        """Read the file in text mode, parse it, and cache the result.

        Args:
            reload: If True read the bytes from the file and update the cache.

            check_file: If True check if the file is newer than the cache and if
                it is reload it.

            bypass_cache: If True the cache will be cleared out and not used.

        Returns:
            The cached parsed JSON of the file.
        """
        if bypass_cache:
            return json.loads(self.read_text(bypass_cache=bypass_cache))

        if (
            self.cached_json is None
            or reload
            # If the file is up to date that means the file's content is newer than the
            # cache and it needs to be reloaded.
            or (check_file and self.is_up_to_date(self.cache_timestamp))
        ):
            self.cached_json = json.loads(self.read_text(reload=True))

        return self.cached_json

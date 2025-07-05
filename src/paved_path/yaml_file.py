"""Library for working with YAML files."""

from typing import Any, override

import yaml

from .paved_path import PavedPath


class YAMLFile(PavedPath):
    """YAML file manager."""

    cached_yaml: Any = None

    @override
    def clear_cache(self) -> None:
        self.cached_yaml = None
        super().clear_cache()

    def safe_write_yaml(
        self,
        data: dict[Any, Any] | list[Any] | str,
        *,
        bypass_cache: bool = False,
    ) -> int:
        """Manage cache, open the yaml file in text mode, read it, and close the file.

        Args:
            data: The data to write to the file.

            bypass_cache: If True the cache will be cleared out and not used.

        Returns:
            Passed from self.write_text().
        """
        # If given a string make sure it is valid YAML before writing it.
        if isinstance(data, str):
            data = yaml.safe_load(data)

        # Dump and load YAML to make sure Serialization does not cause the
        # loaded file to be different than the file that is being written.
        dumped_yaml = yaml.safe_dump(data, default_flow_style=False)
        read_yaml = yaml.safe_load(dumped_yaml)
        if read_yaml != data:
            serialization_error_msg = (
                "Serialization will create an output that is different from the input"
            )
            raise ValueError(serialization_error_msg)

        output = self.write_text(
            dumped_yaml,
            bypass_cache=bypass_cache,
        )

        if not bypass_cache:
            self.cached_yaml = data

        return output

    def read_yaml(
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
            The cached parsed YAML of the file.
        """
        if bypass_cache:
            return yaml.safe_load(self.read_text(bypass_cache=bypass_cache))

        if (
            self.cached_yaml is None
            or reload
            # If the file is up to date that means the file's content is newer than the
            # cache and it needs to be reloaded.
            or (check_file and self.is_up_to_date(self.cache_timestamp))
        ):
            self.cached_yaml = yaml.safe_load(self.read_text(reload=True))

        return self.cached_yaml

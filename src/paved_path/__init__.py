"""Library that extends pathlib's Path."""

from __future__ import annotations

from .json_file import JSONFile
from .paved_path import PavedPath

try:
    from .yaml_file import YAMLFile  # type: ignore[reportAssignmentType]
except ImportError:

    class YAMLFile:  # pylint: disable=R0903
        """Placeholder for YAMLFile when PyYAML is not installed."""

        def __init__(self) -> None:
            err = (
                "PyYAML is required for YAML file operations. "
                "Install it with: `paved-path[yaml]`."
            )
            raise ImportError(err)


__all__ = ["JSONFile", "PavedPath", "YAMLFile"]

"""A modified of pathlib.Path that adds extra functionality."""
from __future__ import annotations

import shutil
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os
    from typing import Self, TypeVar

    PathableType = TypeVar("PathableType", str, bytes, os.PathLike[str], int, datetime, date, float)


# Python's Path implementation  is a little bit unsuaul
# Using type(Path()) is required to subclass Path but it may break in the future
class PavedPath(type(Path())):
    """A modified of pathlib.Path that adds extra functionality."""

    def __new__(cls, *args: PathableType) -> Self:
        """Convert all arguments to Path objects and passes them to the Path constructor."""
        # TypeErrors occur in __new__ so values need to be cast here before __init__
        path_fragments = [cls._convert_to_path(partial_path) for partial_path in args]
        return super().__new__(cls, *path_fragments)

    # Add extra instance variables used for caching
    def __init__(self, *_args: PathableType) -> None:
        """Initialize the path object and set the cached values to None."""
        self.read_bytes_cached_value = None
        self.read_text_cached_value = None

    # When values are appended to a path the new path should be validated
    def __truediv__(self, key: PathableType) -> Self:
        """Append a value to the path and return a new path object."""
        return super().__truediv__(self._convert_to_path(key))

    @classmethod
    def _convert_to_path(cls, value: PathableType) -> os.PathLike[str]:
        """Convert a string, bytes, os.PathLike, int, datetime, date or float to a Path object."""
        if isinstance(value, datetime):
            # datetime - 123.456
            return cls._convert_to_path(value.timestamp())
        if isinstance(value, (datetime, date, float, int, str, bytes)):
            # date - "2000-01-01"
            # float - "123.456"
            # int - "123"
            # str - "abc"
            # bytes - "abc"
            return Path(str(value))

        return value

    def aware_mtime(self) -> datetime:
        """Get the mtime of a file as a timezone aware datetime object."""
        return datetime.fromtimestamp(self.stat().st_mtime).astimezone()

    def up_to_date(self, timestamp: datetime | None = None) -> bool:
        """Check if the file is up to date with respect to a given timestamp."""
        # If file does not exist it can't be up to date
        if not self.exists():
            return False

        # If no timestamp is given and the file exists it is up to date
        if timestamp is None:
            return True

        # When there is a file and a timestamp make the timestamp timezone aware and compare it to the file's mtime
        return self.aware_mtime() > timestamp.astimezone()

    def outdated(self, timestamp: datetime | None = None) -> bool:
        """Check if the file is outdated with respect to a given timestamp."""
        return not self.up_to_date(timestamp)

    def write(self, content: bytes | str) -> None:
        """Write a bytes or a str object to a file, and will automatically create the directory if needed."""
        self.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            self.write_bytes(content)
        else:
            self.write_text(content, encoding="utf-8")

    def delete(self) -> None:
        """Delete a folder or a file without having to worry about which it is."""
        if self.exists():
            if self.is_file():
                self.unlink()
            else:
                shutil.rmtree(self)

    def read_text_cached(self, encoding: None | str = None, *, reload: bool = False) -> str:
        """Read the file text and cache the result."""
        if not self.read_text_cached_value or reload:
            self.read_text_cached_value = self.read_text(encoding=encoding)

        return self.read_text_cached_value

    def read_bytes_cached(self, *, reload: bool = False) -> bytes:
        """Read the file bytes and cache the result."""
        if not self.read_bytes_cached_value or reload:
            self.read_bytes_cached_value = self.read_bytes()

        return self.read_bytes_cached_value

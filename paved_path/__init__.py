"""Library for working with files and file paths."""
from __future__ import annotations

import logging
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import os
    from typing import Self, TypeAlias

    from typing_extensions import Buffer

    PathableType: TypeAlias = str | bytes | os.PathLike[str] | int | datetime | date | float

logger = logging.getLogger(__name__)


# This is set up as a seperate class to make it easier to clear the cache.
class CobblestoneCache:
    """Cache for PavedPath."""

    def __init__(self) -> None:
        """Initialize the cache with None values."""
        self.read_text: str | None = None
        self.read_bytes: bytes | None = None


# Python's Path implementation  is a little bit unsuaul
# Using type(Path()) is required to subclass Path but it may break in the future
class PavedPath(type(Path())):
    """Library for working with files and file paths."""

    cache_class = CobblestoneCache

    def __new__(cls, *args: PathableType, title: str | None = None) -> Self:
        """Convert all arguments to Path objects and passes them to the Path constructor."""
        # TypeErrors occur in __new__ so values need to be cast here before __init__
        path_fragments = [cls._convert_to_path(partial_path) for partial_path in args]
        # This check allows subclasses to initialize a cache of a different object before or after super().__new__ is
        # called making it less likely to accidently have the wrong type of cache object.

        return super().__new__(cls, *path_fragments, title=title)

    # This function exists just for type hinting purposes
    def __init__(self, *_args: PathableType, title: str | None = None) -> None:
        """Initialize the object and set up the cache."""
        super().__init__()
        self.cache = self.cache_class()
        self._title = title

    @property
    def title(self) -> str:
        """The title of the file that has no relationship to it's actual path. Useful for logging."""
        return self._title or self.name

    @title.setter
    def title(self, title: str) -> None:
        self._title = title

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

    def is_up_to_date(self, timestamp: datetime | None = None) -> bool:
        """Check if the file is up to date with respect to a given timestamp.

        Args:
        ----
            timestamp: The timestamp to compare the file's modified timestamp to, if no timestamp is given just check if
            the file exists.
        """
        # If file does not exist it can't be up to date
        if not self.exists():
            logger.getChild("missing_file").info(self.title)
            return False

        # If no timestamp is given and the file exists it is up to date
        if timestamp is None:
            logger.getChild("up_to_date_file").info(self.title)
            return True

        # When there is a file and a timestamp compare them
        if self.aware_mtime() < timestamp.astimezone():
            logger.getChild("outdated_file").info(self.title)
            return False

        # All checks passed, file is up to date
        logger.getChild("up_to_date_file").info(self.title)
        return True

    def is_outdated(self, timestamp: datetime | None = None) -> bool:
        """Check if the file is outdated with respect to a given timestamp.

        Args:
        ----
            timestamp: The timestamp to compare the file's modified timestamp to, if no timestamp is given just check if
            the file exists.
        """
        return not self.is_up_to_date(timestamp)

    def write(self, content: bytes | str, *, write_through: bool = True) -> None:
        """Open the file in bytes or text mode, write to it, close the file, and clear the cache.

        Args:
        ----
            content: The object to be written to the file.
            write_through: If True the cache will be updated to match what is written to the file. If False the cache
            will be cleared. Either way the cache is not allowed to be out of sync with the file, either it matches the
            file or it is None.
        """
        self.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            self.write_bytes(content)
            if write_through:
                self.cache.read_bytes = content
        else:
            self.write_text(content, encoding="utf-8")
            if write_through:
                self.cache.read_text = content

    def write_text(
        self,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        """Open the file in text mode, write to it, close the file, and clear the cache."""
        self.clear_cache()
        return super().write_text(data, encoding=encoding, errors=errors, newline=newline)

    def write_bytes(self, data: Buffer) -> int:
        """Open the file in bytes mode, write to it, close the file, and clear the cache."""
        self.clear_cache()
        return super().write_bytes(data)

    def clear_cache(self) -> None:
        """Clear the cached values."""
        # Replace self.cache with a new instance of the same object dynamically
        self.cache = self.cache_class()

    def delete(self) -> None:
        """Delete a folder or a file without having to worry about which it is."""
        if self.exists():
            if self.is_file():
                self.unlink()
            else:
                shutil.rmtree(self)

    def read_text_cached(self, encoding: None | str = None, *, reload: bool = False) -> str:
        """Read the file text and cache the result.

        Args:
        ----
            encoding: The encoding to use when reading the file.
            reload: If true read the text from the file, and cache the string even if a value is already cached. If
            False use the cached string if it exists otherwise read the text from the file and cache the result.


        Returns:
        -------
            A cached string object.
        """
        if not self.cache.read_text or reload:
            self.cache.read_text = self.read_text(encoding=encoding)

        return self.cache.read_text

    def read_bytes_cached(self, *, reload: bool = False) -> bytes:
        """Read the file bytes and cache the result.

        Args:
        ----
            encoding: The encoding to use when reading the file.
            reload: If true read the bytes from the file, and cache the bytes even if a value is already cached. If
            False use the cached bytes if it exists otherwise read the bytes from the file and cache the result.


        Returns:
        -------
            A cached bytes object.
        """
        if not self.cache.read_bytes or reload:
            self.cache.read_bytes = self.read_bytes()

        return self.cache.read_bytes

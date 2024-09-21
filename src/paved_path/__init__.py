"""Library that extends pathlib's Path."""

from __future__ import annotations

import shutil
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from collections.abc import Buffer
    from os import PathLike
    from typing import Self

    # This is the type signature used by Path
    type StrPath = str | PathLike[str]

    # This is the extended type signature used by PavedPath
    type PavedPathTypes = StrPath | int | datetime | date | float


class PavedPath(Path):
    """Class that extends pathlib's Path."""

    cache_timestamp: datetime | None = None
    cached_read_text: str | None = None
    cached_read_bytes: bytes | None = None

    # __new__ is defined here so the type between __new__ and __init__ match and
    # so that super is called without having type errors
    def __new__(cls, *args: PavedPathTypes) -> Self:
        """Create a new PavedPath object.

        Args:
            args: The objects used to create the PavedPath object.

        Returns:
            A PavedPath object.
        """
        path_fragments = [cls._convert_to_path(arg) for arg in args]
        return super().__new__(cls, *path_fragments)

    def __init__(self, *args: PavedPathTypes) -> None:
        """Create a new PavedPath object.

        Args:
            args: The objects used to create the PavedPath object.

        Returns:
            A PavedPath object.
        """
        path_fragments = [self._convert_to_path(arg) for arg in args]
        super().__init__(*path_fragments)

    def __truediv__(self, key: PavedPathTypes) -> Self:
        """Appends the given value to the path and returns a new path object.

        Args:
            key: The value to append to the path.

        Returns:
            A new PavedPath object with the value appended to it.
        """
        return super().__truediv__(self._convert_to_path(key))

    @classmethod
    def _convert_to_path(cls, arg: PavedPathTypes) -> PathLike[str]:
        """Convert various types into a Path object.

        Conversion format examples:
        - datetime(2020, 1, 1): "01-01-2020, 00-00-00.000000"
        - date(2020, 1, 1): 2000-01-01
        - float(123.456) - 123.456
        - int(123) - 123
        - str("abc") - abc
        - bytes("abc") - abc
        - Path("abc") - abc
        - PavedPath("abc") - abc

        Args:
            arg: The arguments to convert.

        Returns:
            A Path object.
        """
        if isinstance(arg, datetime):
            return cls._convert_to_path(arg.strftime("%Y-%m-%d, %H-%M-%S.%f"))
        if isinstance(arg, date | float | int | str | bytes):
            return Path(str(arg))

        return arg

    def clear_cache(self) -> None:
        """Clear the cache."""
        self.cached_read_text = None
        self.cached_read_bytes = None
        self.cache_timestamp = None

    def aware_mtime(self) -> datetime:
        """Get the timezone aware mtime of a file.

        Returns:
            A timezone aware datetime object.
        """
        return datetime.fromtimestamp(self.stat().st_mtime).astimezone()

    def is_up_to_date(self, timestamp: datetime | None = None) -> bool:
        """Check if the file is up to date with respect to a given timestamp.

        Args:
            timestamp: The timestamp to compare the file's modified timestamp
                to, if no timestamp is given just check if the file exists.

        Returns:
            True if the file exists and is up to date. False if the file is
                outdated or does not exist.
        """
        # If file does not exist it can't be up to date
        if not self.exists():
            return False

        # If no timestamp is given and the file exists it is up to date
        if timestamp is None:
            return True

        # IF the file exists and a timestamp is given compare the information
        return self.aware_mtime() > timestamp.astimezone()

    def is_outdated(self, timestamp: datetime | None = None) -> bool:
        """Check if the file is outdated with respect to a given timestamp.

        Args:
            timestamp: The timestamp to compare the file's modified timestamp
                to, if no timestamp is given just check if the file exists.

        Returns:
            True if the file is outdated or does not exist. False if the file
                exists and is up to date.
        """
        return not self.is_up_to_date(timestamp)

    @override
    def write_text(
        self,
        data: str,
        encoding: str | None = "utf-8",
        errors: str | None = None,
        newline: str | None = None,
        *,
        write_through: bool = True,
        clear_cache: bool = True,
    ) -> int:
        """Manage cache, open the file in text mode, read it, and close the file.

        Args:
            data: The data to write to the file.

            encoding: Passed to super().write_text.

            errors: Passed to super().write_text.

            newline: Passed to super().write_text.

            write_through: If True write the text to the file and the cache. If
                False write the text to the file and clear out the cache so it
                stays in sync.

            clear_cache: If True clear the cache. If False do not clear the
                cache.

        Returns:
            Passed from super().write_text.
        """
        # The original function needs to be overridden so there is no way to
        # write content to the file without clearing the cache. This will keep
        # the cache in sync with whatever is written to the file.
        if clear_cache:
            self.clear_cache()
        if write_through:
            self.cached_read_text = data

        # Make dir if needed
        self.parent.mkdir(parents=True, exist_ok=True)

        output = super().write_text(
            data,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )

        self.cache_timestamp = self.aware_mtime()
        return output

    @override
    def write_bytes(
        self,
        data: Buffer,
        *,
        write_through: bool = True,
        clear_cache: bool = True,
    ) -> int:
        """Manage cache, open the file in bytes mode, read it, and close the file.

        Args:
            data: The data to write to the file.

            write_through: If True write the bytes to the file and the cache. If
                False write the bytes to the file and clear out the cache so it
                stays in sync.

            clear_cache: If True clear the cache. If False do not clear the
                cache.

        Returns:
            Passed from super().write_bytes.
        """
        # The original function needs to be overridden so there is no way to
        # write content to the file without clearing the cache. This will keep
        # the cache in sync with whatever is written to the file.
        if clear_cache:
            self.clear_cache()
        if write_through:
            self.cached_read_bytes = bytes(data)

        self.parent.mkdir(parents=True, exist_ok=True)

        output = super().write_bytes(data)
        self.cache_timestamp = datetime.now().astimezone()

        return output

    def delete_file(self) -> None:
        """Delete the file if it exists.

        This is the same as calling os.remove(self) if the file exists.
        """
        if self.exists():
            self.unlink()

    def delete_dir(self) -> None:
        """Delete the folder if it exists.

        This is the same as calling shutil.rmtree(self) if the folder exists.
        """
        if self.exists():
            shutil.rmtree(self)

    def read_text_cached(
        self,
        encoding: None | str = None,
        errors: None | str = None,
        *,
        reload: bool = False,
        check_file: bool = False,
    ) -> str:
        """Open the file in text mode, read it, cache the result, and close the file.

        Args:
            encoding: Passed to super().read_text.

            errors: Passed to super().read_text.

            reload: * If True read the text from the file, and cache the text.
                * If False use the cached text if it exists otherwise read the
                text from the file and cache it.

            check_file: * If True check if the file is newer than the cache, and
                it is reload it.

        Returns:
            The cached text of the file.
        """
        if (
            self.cached_read_text is None
            or reload
            or (check_file and self.is_up_to_date(self.cache_timestamp))
        ):
            self.cached_read_text = self.read_text(encoding=encoding, errors=errors)
            self.cache_timestamp = datetime.now().astimezone()

        return self.cached_read_text

    def read_bytes_cached(
        self,
        *,
        reload: bool = False,
        check_file: bool = False,
    ) -> bytes:
        """Open the file in bytes mode, read it, cache the result, and close the file.

        If the file is not found in the cache the file will be read and the
        bytes will be cached. If the file is found in the cache the cached bytes
        will be returned.

        Args:
            reload: If True read the bytes from the file and update the cache.

            check_file: If True check if the file is newer than the cache and if
            the file is newer than the cache read the bytes from the file and
            update the cache.

        Returns:
            The cached bytes of the file.
        """
        if (
            self.cached_read_bytes is None
            or reload
            or (check_file and self.is_up_to_date(self.cache_timestamp))
        ):
            self.cached_read_bytes = self.read_bytes()
            self.cache_timestamp = datetime.now().astimezone()

        return self.cached_read_bytes

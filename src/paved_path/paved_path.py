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
    """File manager."""

    cache_timestamp: datetime | None = None
    cached_text: str | None = None
    cached_bytes: bytes | None = None

    @override
    def __new__(cls, *args: PavedPathTypes) -> Self:
        path_fragments = [cls._convert_to_path(arg) for arg in args]
        return super().__new__(cls, *path_fragments)

    @override
    def __init__(self, *args: PavedPathTypes) -> None:
        path_fragments = [self._convert_to_path(arg) for arg in args]
        super().__init__(*path_fragments)

    @override
    def __truediv__(self, key: PavedPathTypes) -> Self:
        return super().__truediv__(self._convert_to_path(key))

    @classmethod
    def _convert_to_path(cls, arg: PavedPathTypes) -> PathLike[str]:
        """Convert various types into a Path object.

        Conversion format examples:
        - datetime(2020, 1, 1): "2020-01-01, 00-00-00.000000"
        - date(2020, 1, 1): 2020-01-01
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
        self.cached_text = None
        self.cached_bytes = None
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
        bypass_cache: bool = False,
    ) -> int:
        """Manage cache, open the file in text mode, read it, and close the file.

        Args:
            data: The data to write to the file.

            encoding: Passed to super().write_text.

            errors: Passed to super().write_text.

            newline: Passed to super().write_text.

            bypass_cache: If True the cache will be cleared out and not used.

        Returns:
            Passed from super().write_text.
        """
        self.clear_cache()

        # Automatically make parent directories if needed for convenience
        self.parent.mkdir(parents=True, exist_ok=True)
        output = super().write_text(
            data,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )

        if not bypass_cache:
            self.cached_text = data
            self.cache_timestamp = self.aware_mtime()

        return output

    @override
    def write_bytes(
        self,
        data: Buffer,
        *,
        bypass_cache: bool = False,
    ) -> int:
        """Manage cache, open the file in bytes mode, read it, and close the file.

        Args:
            data: The data to write to the file.

            bypass_cache: If True the cache will be cleared out and not used.

        Returns:
            Passed from super().write_bytes().
        """
        self.clear_cache()

        # Automatically make parent directories if needed for convenience
        self.parent.mkdir(parents=True, exist_ok=True)
        output = super().write_bytes(data)

        if not bypass_cache:
            self.cached_bytes = bytes(data)
            self.cache_timestamp = self.aware_mtime()

        return output

    def rmtree(self) -> None:
        """Remove this directory and all its contents.

        This is a convenience method that wraps shutil.rmtree
        """
        shutil.rmtree(self)

    @override
    def rmdir(self) -> None:
        super().rmdir()

    @override
    def unlink(self, missing_ok: bool = False) -> None:
        super().unlink(missing_ok=missing_ok)
        self.clear_cache()

    @override
    def read_text(
        self,
        encoding: None | str = None,
        errors: None | str = None,
        *,
        reload: bool = False,
        check_file: bool = False,
        bypass_cache: bool = False,
    ) -> str:
        """Read the file in text mode and cache the result.

        Args:
            encoding: Passed to super().read_text.

            errors: Passed to super().read_text.

            reload: * If True read the text from the file, and cache the text.
                * If False use the cached text if it exists otherwise read the
                text from the file and cache it.

            check_file: If True check if the file is newer than the cache and if
                it is reload it.

            bypass_cache: If True the cache will be cleared out and not used.

        Returns:
            The cached text of the file.
        """
        if bypass_cache:
            return super().read_text(encoding=encoding, errors=errors)

        if (
            self.cached_text is None
            or reload
            # If the file is up to date that means the file's content is newer than the
            # cache and it needs to be reloaded.
            or (check_file and self.is_up_to_date(self.cache_timestamp))
        ):
            self.cached_text = super().read_text(encoding=encoding, errors=errors)
            self.cache_timestamp = self.aware_mtime()

        return self.cached_text

    @override
    def read_bytes(
        self,
        *,
        reload: bool = False,
        check_file: bool = False,
        bypass_cache: bool = False,
    ) -> bytes:
        """Read the file in bytes mode and cache the result.

        If the file is not found in the cache the file will be read and the
        bytes will be cached. If the file is found in the cache the cached bytes
        will be returned.

        Args:
            reload: If True read the bytes from the file and update the cache.

            check_file: If True check if the file is newer than the cache and if
                it is reload it.

            bypass_cache: If True the cache will be cleared out and not used.

        Returns:
            The cached bytes of the file.
        """
        if bypass_cache:
            return super().read_bytes()

        if (
            self.cached_bytes is None
            or reload
            # If the file is up to date that means the file's content is newer than the
            # cache and it needs to be reloaded.
            or (check_file and self.is_up_to_date(self.cache_timestamp))
        ):
            self.cached_bytes = super().read_bytes()
            self.cache_timestamp = self.aware_mtime()

        return self.cached_bytes

"""
media/dummy.py
Dummy media conversion plugin.
Serves as a base class & template for other media plugins,
as well as a fallback for unknown media types.
"""

import os
from pathlib import Path
from typing import Callable
from zipfile import ZipFile

from ..utils import Logger

logger = Logger()


class GkmasDummyMedia:
    """
    Unrecognized media handler, also the fallback for conversion plugins.

    Attributes:
        name (str): Name of the media file (for logging purposes).
        downloader (Callable): Function to lazily download raw bytes.
        mtime (float): Last modified time of the media file as a timestamp.
        mimetype (str): Media type (e.g., "image", "audio", "video").
        raw (bytes): Raw binary data of the media file.
        raw_format (str): Format of the raw media data.
        converted (bytes): Converted binary data of the media file, if applicable.
        converted_format (str): Format of the converted media data.

    Methods:
        get_data(**kwargs) -> dict:
            Requests data of the desired format.
        export(path: Path, **kwargs):
            Exports the media to the specified path.
    """

    ENABLE_CACHE = False

    def __init__(self, name: str, downloader: Callable[[], dict]):
        self.name = name  # only for logging
        self.downloader = downloader  # lazy downloader

        self.mtime = None
        self.raw = None  # raw binary data (we don't want to reencode known formats)
        self.converted = None  # converted binary data (if applicable)

        # Children should override raw_format if raw bytes is "ready"
        #   or converted_format as the default target, but **not both.**
        # This mutual exclusivity forces the following two 'None' fallbacks
        #   to appear here, otherwise we get AttributeError's.
        # This isn't a problem for self.mimetype since it's mandatory.
        self.raw_format = None
        self.converted_format = None
        self._init_mimetype(name)

    def _init_mimetype(self, name: str):
        self.mimetype = None  # TO BE OVERRIDDEN (e.g., "image", "audio", "video")
        self.raw_format = None  # TO BE OVERRIDDEN, or
        self.converted_format = None  # TO BE OVERRIDDEN (choose one)
        # yeah these two lines appear twice... this time just as a hint

    def _convert(self, raw: bytes, **kwargs) -> bytes:
        raise NotImplementedError  # TO BE OVERRIDDEN

    def get_data(self, **kwargs) -> dict:
        """
        Requests data of the desired format.

        Args:
            {mimetype}_format (str): Desired format for the media type.

        Returns:
            dict: A dictionary of keys "bytes", "mimetype", and "mtime".
        """

        fmt = kwargs.get(
            f"{self.mimetype}_format",
            self.raw_format or self.converted_format,  # fallback if raw_format is None
        )

        if self.raw_format == fmt:  # rawdump
            _bytes = self._get_raw()  # must be called before accessing self.mtime
            return {
                "bytes": _bytes,
                "mimetype": (
                    f"{self.mimetype}/{self.raw_format}"
                    if self.mimetype and self.raw_format
                    else "application/octet-stream"
                ),
                "mtime": self.mtime,
            }

        if self.converted_format != fmt:  # record and convert
            self.converted_format = fmt
            self.converted = None  # invalidate cache

        _bytes = self._get_converted(**kwargs)
        return {
            "bytes": _bytes,
            "mimetype": (
                "application/zip"
                if _bytes.startswith(b"PK\x03\x04")
                # a bit of a hack, but we don't want to override bookkeeping vars
                else (
                    f"{self.mimetype}/{self.converted_format}"
                    if self.mimetype and self.converted_format
                    else "application/octet-stream"
                    # in case some malicious user escaped the 'if self.raw_format == fmt' branch
                    # by explicitly specifying 'None_format' as some random value
                )
            ),
            "mtime": self.mtime,
        }

    def _get_raw(self) -> bytes:
        if self.raw is not None:
            return self.raw  # read from cache
        data = self.downloader()
        self.mtime = data["mtime"]  # unconditionally cache, as a metadata field
        if self.ENABLE_CACHE:
            self.raw = data["bytes"]
        return data["bytes"]  # cached or not, this is "valid"

    def _get_converted(self, **kwargs) -> bytes:
        if self.converted is not None:
            return self.converted  # assumes proper invalidation beforehand
        converted = self._convert(self._get_raw(), **kwargs)  # e.g., image_resize
        if self.ENABLE_CACHE:
            self.converted = converted
        return converted

    def export(self, path: Path, **kwargs):
        """
        Exports the media to the specified path.

        Args:
            path (Path): The path to export the media to.
            convert_{mimetype} (bool): Whether to enable media conversion.
            {mimetype}_format (str): Desired format for the media type.
        """

        # not overriding self.mimetype indicates unhandled media type
        if self.mimetype and kwargs.get(f"convert_{self.mimetype}", True):
            try:
                self._export_converted(path, **kwargs)
            except Exception as e:
                logger.warning(
                    f"{self.name} failed to convert, fallback to rawdump; exception to follow"
                )
                self._export_raw(path)
                raise e
        else:
            self._export_raw(path)

    def _export_raw(self, path: Path):
        path.write_bytes(self.raw)
        if self.mtime:
            os.utime(path, (self.mtime, self.mtime))
        logger.success(f"{self.name} downloaded")

    def _export_converted(self, path: Path, **kwargs):
        data = self.get_data(**kwargs)
        mimesubtype = data["mimetype"].split("/")[1]
        path.with_suffix(f".{mimesubtype}").write_bytes(data["bytes"])
        if self.mtime:
            os.utime(path.with_suffix(f".{mimesubtype}"), (self.mtime, self.mtime))
        logger.success(f"{self.name} downloaded and converted to {mimesubtype.upper()}")

        if mimesubtype == "zip" and kwargs.get("unpack_subsongs", False):
            with ZipFile(path.with_suffix(f".{mimesubtype}")) as z:
                z.extractall(path.parent)  # surprisingly, doesn't keep mtime's
                for file in z.namelist():
                    os.utime(path.parent / file, (self.mtime, self.mtime))
            path.with_suffix(f".{mimesubtype}").unlink()
            logger.success(f"{self.name} unpacked to {path.parent}")

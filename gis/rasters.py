"""
Raster utilities for the LULC validation application.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import rasterio
from rasterio.errors import RasterioIOError
from rasterio.transform import rowcol


class RasterError(Exception):
    """Base exception for raster-related errors."""


class RasterFileNotFoundError(RasterError):
    """Raised when the requested raster file does not exist."""


class InvalidRasterError(RasterError):
    """Raised when a raster cannot be opened or is invalid."""


class RasterCRSError(RasterError):
    """Raised when a raster does not contain a CRS."""


class CoordinateOutsideRasterError(RasterError):
    """Raised when a coordinate falls outside the raster bounds."""


class NoDataValueError(RasterError):
    """Raised when a requested raster pixel contains NoData."""


@dataclass(frozen=True)
class RasterMetadata:
    """Basic metadata describing a raster dataset."""

    width: int
    height: int
    count: int
    dtype: str
    crs: Any
    transform: Any
    bounds: Any
    nodata: Any


class Raster:
    """Interface for reading and querying a raster dataset."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._dataset: rasterio.io.DatasetReader | None = None

    def open(self) -> "Raster":
        """Open the raster dataset."""

        if not self.path.exists():
            raise RasterFileNotFoundError(
                f"Raster file does not exist: {self.path}"
            )

        if not self.path.is_file():
            raise RasterFileNotFoundError(
                f"Raster path is not a file: {self.path}"
            )

        try:
            self._dataset = rasterio.open(self.path)

        except RasterioIOError as exc:
            raise InvalidRasterError(
                f"Unable to open raster: {self.path}"
            ) from exc

        return self

    def close(self) -> None:
        """Close the raster."""

        if self._dataset is not None:
            self._dataset.close()
            self._dataset = None

    def __enter__(self) -> "Raster":
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        self.close()

    def _require_open(self):
        """Return the open raster dataset."""

        if self._dataset is None:
            raise InvalidRasterError(
                "Raster is not open. Call open() first."
            )

        return self._dataset

    @property
    def crs(self) -> Any:
        """Return raster CRS."""

        dataset = self._require_open()

        if dataset.crs is None:
            raise RasterCRSError(
                f"Raster does not contain a CRS: {self.path}"
            )

        return dataset.crs

    @property
    def transform(self) -> Any:
        return self._require_open().transform

    @property
    def width(self) -> int:
        return self._require_open().width

    @property
    def height(self) -> int:
        return self._require_open().height

    @property
    def count(self) -> int:
        return self._require_open().count

    @property
    def bounds(self) -> Any:
        return self._require_open().bounds

    @property
    def nodata(self) -> Any:
        return self._require_open().nodata

    @property
    def dtypes(self) -> tuple[str, ...]:
        return self._require_open().dtypes

    def metadata(self) -> RasterMetadata:
        """Return raster metadata."""

        dataset = self._require_open()

        return RasterMetadata(
            width=dataset.width,
            height=dataset.height,
            count=dataset.count,
            dtype=dataset.dtypes[0],
            crs=self.crs,
            transform=dataset.transform,
            bounds=dataset.bounds,
            nodata=dataset.nodata,
        )

    def read_band(self, band: int = 1) -> Any:
        """Read a complete raster band."""

        dataset = self._require_open()

        if band < 1 or band > dataset.count:
            raise ValueError(
                f"Invalid band {band}. "
                f"Raster contains {dataset.count} band(s)."
            )

        return dataset.read(band)

    def coordinate_to_pixel(
        self,
        x: float,
        y: float,
    ) -> tuple[int, int]:
        """Convert spatial coordinates to raster row and column."""

        dataset = self._require_open()

        try:
            row, column = rowcol(
                dataset.transform,
                x,
                y,
            )

        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid coordinate: ({x}, {y})"
            ) from exc

        if (
            row < 0
            or row >= dataset.height
            or column < 0
            or column >= dataset.width
        ):
            raise CoordinateOutsideRasterError(
                f"Coordinate ({x}, {y}) falls outside raster bounds."
            )

        return int(row), int(column)

    def value_at(
        self,
        x: float,
        y: float,
        band: int = 1,
    ) -> Any:
        """Extract a raster value at a coordinate."""

        dataset = self._require_open()

        if band < 1 or band > dataset.count:
            raise ValueError(
                f"Invalid band {band}. "
                f"Raster contains {dataset.count} band(s)."
            )

        row, column = self.coordinate_to_pixel(x, y)

        value = dataset.read(
            band,
            window=(
                (row, row + 1),
                (column, column + 1),
            ),
            masked=True,
        )[0, 0]

        if getattr(value, "mask", False):
            raise NoDataValueError(
                f"Raster value at ({x}, {y}) is NoData."
            )

        return value.item() if hasattr(value, "item") else value

    def contains_coordinate(
        self,
        x: float,
        y: float,
    ) -> bool:
        """Return True if coordinate is inside raster extent."""

        bounds = self._require_open().bounds

        return (
            bounds.left <= x <= bounds.right
            and bounds.bottom <= y <= bounds.top
        )


def open_raster(
    path: str | Path,
) -> Raster:
    """Open and return a Raster object."""

    return Raster(path).open()
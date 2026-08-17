"""
Raster utilities for the LULC validation application.

This module provides functionality for:

- Opening raster datasets
- Reading raster metadata
- Reading CRS and georeferencing information
- Reading raster dimensions
- Reading raster bounds
- Reading NoData information
- Extracting raster values at geographic coordinates

This module does not contain validation metrics, confusion-matrix
logic, GUI logic, or Dynamic World class mappings.
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
    """
    Basic metadata describing a raster dataset.

    Attributes
    ----------
    width:
        Number of columns in the raster.
    height:
        Number of rows in the raster.
    count:
        Number of raster bands.
    dtype:
        Data type of the raster bands.
    crs:
        Coordinate Reference System of the raster.
    transform:
        Affine transform describing raster georeferencing.
    bounds:
        Spatial bounds of the raster.
    nodata:
        Raster NoData value, if defined.
    """

    width: int
    height: int
    count: int
    dtype: str
    crs: Any
    transform: Any
    bounds: Any
    nodata: Any


class Raster:
    """
    Interface for reading and querying a raster dataset.

    Parameters
    ----------
    path:
        Path to the raster dataset.

    Notes
    -----
    The raster is opened when ``open()`` is called. It can then be
    closed explicitly using ``close()`` or automatically by using
    the object as a context manager.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._dataset: rasterio.io.DatasetReader | None = None

    def open(self) -> "Raster":
        """
        Open the raster dataset.

        Returns
        -------
        Raster
            The current Raster object.

        Raises
        ------
        RasterFileNotFoundError
            If the raster file does not exist.

        InvalidRasterError
            If rasterio cannot open the file.
        """
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
        """Close the raster dataset if it is currently open."""
        if self._dataset is not None:
            self._dataset.close()
            self._dataset = None

    def __enter__(self) -> "Raster":
        """Open the raster when entering a context manager."""
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        """Close the raster when leaving a context manager."""
        self.close()

    def _require_open(self) -> rasterio.io.DatasetReader:
        """
        Return the open raster dataset.

        Raises
        ------
        InvalidRasterError
            If the raster has not been opened.
        """
        if self._dataset is None:
            raise InvalidRasterError(
                "Raster is not open. Call open() before accessing it."
            )

        return self._dataset

    @property
    def crs(self) -> Any:
        """
        Return the raster CRS.

        Raises
        ------
        RasterCRSError
            If the raster does not define a CRS.
        """
        dataset = self._require_open()

        if dataset.crs is None:
            raise RasterCRSError(
                f"Raster does not contain a CRS: {self.path}"
            )

        return dataset.crs

    @property
    def transform(self) -> Any:
        """Return the raster's affine georeferencing transform."""
        return self._require_open().transform

    @property
    def width(self) -> int:
        """Return the raster width in pixels."""
        return self._require_open().width

    @property
    def height(self) -> int:
        """Return the raster height in pixels."""
        return self._require_open().height

    @property
    def count(self) -> int:
        """Return the number of raster bands."""
        return self._require_open().count

    @property
    def bounds(self) -> Any:
        """Return the spatial bounds of the raster."""
        return self._require_open().bounds

    @property
    def nodata(self) -> Any:
        """Return the raster's NoData value, if defined."""
        return self._require_open().nodata

    @property
    def dtypes(self) -> tuple[str, ...]:
        """Return the data types of all raster bands."""
        return self._require_open().dtypes

    def metadata(self) -> RasterMetadata:
        """
        Return important raster metadata.

        Returns
        -------
        RasterMetadata
            Structured raster metadata.
        """
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
        """
        Read a complete raster band.

        Parameters
        ----------
        band:
            One-based raster band number.

        Returns
        -------
        numpy.ndarray
            Raster band values.

        Raises
        ------
        ValueError
            If the requested band number is invalid.
        """
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
        """
        Convert spatial coordinates to raster row and column.

        Parameters
        ----------
        x:
            X coordinate in the raster's CRS.
        y:
            Y coordinate in the raster's CRS.

        Returns
        -------
        tuple[int, int]
            Raster row and column.
        """
        dataset = self._require_open()

        try:
            row, column = rowcol(dataset.transform, x, y)
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
        """
        Extract a raster value at a spatial coordinate.

        Parameters
        ----------
        x:
            X coordinate in the raster's CRS.
        y:
            Y coordinate in the raster's CRS.
        band:
            One-based raster band number.

        Returns
        -------
        Any
            Raw raster value at the requested location.

        Raises
        ------
        ValueError
            If the requested band or coordinate is invalid.

        CoordinateOutsideRasterError
            If the coordinate falls outside the raster.

        NoDataValueError
            If the selected pixel contains NoData.
        """
        dataset = self._require_open()

        if band < 1 or band > dataset.count:
            raise ValueError(
                f"Invalid band {band}. "
                f"Raster contains {dataset.count} band(s)."
            )

        row, column = self.coordinate_to_pixel(x, y)

        value = dataset.read(
            band,
            window=((row, row + 1), (column, column + 1)),
            masked=True,
        )[0, 0]

        if getattr(value, "mask", False):
            raise NoDataValueError(
                f"Raster value at ({x}, {y}) is NoData."
            )

        return value.item() if hasattr(value, "item") else value

    def contains_coordinate(self, x: float, y: float) -> bool:
        """
        Check whether a coordinate falls inside the raster bounds.

        Parameters
        ----------
        x:
            X coordinate in the raster's CRS.
        y:
            Y coordinate in the raster's CRS.

        Returns
        -------
        bool
            True if the coordinate is inside the raster extent.
        """
        bounds = self._require_open().bounds

        return (
            bounds.left <= x <= bounds.right
            and bounds.bottom <= y <= bounds.top
        )


def open_raster(path: str | Path) -> Raster:
    """
    Open a raster and return a Raster object.

    Parameters
    ----------
    path:
        Path to the raster dataset.

    Returns
    -------
    Raster
        Open raster interface.
    """
    return Raster(path).open()
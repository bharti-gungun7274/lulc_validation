"""
Validation-point utilities for the LULC validation application.

This module provides functionality for:

- Loading validation-point datasets
- Reading point geometries
- Reading point attributes
- Preserving the original attributes
- Extracting point coordinates
- Validating point geometries
- Preserving the dataset CRS

The module does not calculate validation accuracy, confusion matrices,
or perform GUI/application workflow logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
from shapely.geometry import Point


class PointDataError(Exception):
    """Base exception for validation-point errors."""


class PointFileNotFoundError(PointDataError):
    """Raised when the validation-point file does not exist."""


class InvalidPointDatasetError(PointDataError):
    """Raised when the point dataset cannot be loaded."""


class MissingPointCRSError(PointDataError):
    """Raised when the point dataset has no CRS."""


class InvalidPointGeometryError(PointDataError):
    """Raised when a feature does not contain valid point geometry."""


@dataclass(frozen=True)
class ValidationPoint:
    """
    Clean representation of one validation point.

    Attributes
    ----------
    index:
        Original row index from the source dataset.
    x:
        X coordinate in the source dataset CRS.
    y:
        Y coordinate in the source dataset CRS.
    attributes:
        Original non-geometry attributes.
    """

    index: Any
    x: float
    y: float
    attributes: dict[str, Any]


class ValidationPoints:
    """
    Interface for loading and accessing validation points.

    Parameters
    ----------
    path:
        Path to a supported vector dataset containing point geometry.

    Notes
    -----
    The actual attribute schema is intentionally not assumed.
    All source attributes are preserved.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._data: gpd.GeoDataFrame | None = None

    def load(self) -> "ValidationPoints":
        """
        Load the validation-point dataset.

        Returns
        -------
        ValidationPoints
            The current object.

        Raises
        ------
        PointFileNotFoundError
            If the file does not exist.

        InvalidPointDatasetError
            If GeoPandas cannot read the dataset.
        """
        if not self.path.exists():
            raise PointFileNotFoundError(
                f"Validation-point file does not exist: {self.path}"
            )

        if not self.path.is_file():
            raise PointFileNotFoundError(
                f"Validation-point path is not a file: {self.path}"
            )

        try:
            data = gpd.read_file(self.path)
        except Exception as exc:
            raise InvalidPointDatasetError(
                f"Unable to read validation-point dataset: {self.path}"
            ) from exc

        if data.empty:
            raise InvalidPointDatasetError(
                f"Validation-point dataset contains no records: {self.path}"
            )

        self._validate_geometries(data)

        self._data = data

        return self

    def _require_loaded(self) -> gpd.GeoDataFrame:
        """
        Return the loaded GeoDataFrame.

        Raises
        ------
        InvalidPointDatasetError
            If the dataset has not been loaded.
        """
        if self._data is None:
            raise InvalidPointDatasetError(
                "Validation points are not loaded. "
                "Call load() before accessing the data."
            )

        return self._data

    @staticmethod
    def _validate_geometries(
        data: gpd.GeoDataFrame,
    ) -> None:
        """
        Validate that all records contain valid Point geometries.

        Parameters
        ----------
        data:
            GeoDataFrame containing validation points.

        Raises
        ------
        InvalidPointGeometryError
            If a geometry is missing, invalid, or not a Point.
        """
        for index, geometry in data.geometry.items():
            if geometry is None or geometry.is_empty:
                raise InvalidPointGeometryError(
                    f"Point at row {index} has missing or empty geometry."
                )

            if not geometry.is_valid:
                raise InvalidPointGeometryError(
                    f"Point at row {index} has invalid geometry."
                )

            if not isinstance(geometry, Point):
                raise InvalidPointGeometryError(
                    f"Feature at row {index} is "
                    f"{geometry.geom_type}, not a Point."
                )

    @property
    def data(self) -> gpd.GeoDataFrame:
        """
        Return the complete loaded GeoDataFrame.

        The original attributes and geometry are preserved.
        """
        return self._require_loaded()

    @property
    def crs(self) -> Any:
        """
        Return the CRS of the validation-point dataset.

        Raises
        ------
        MissingPointCRSError
            If the dataset has no CRS.
        """
        data = self._require_loaded()

        if data.crs is None:
            raise MissingPointCRSError(
                f"Validation-point dataset has no CRS: {self.path}"
            )

        return data.crs

    @property
    def count(self) -> int:
        """Return the number of validation points."""
        return len(self._require_loaded())

    def records(self) -> list[ValidationPoint]:
        """
        Return clean validation-point records.

        Returns
        -------
        list[ValidationPoint]
            Point coordinates together with all original attributes.

        Notes
        -----
        The geometry column itself is excluded from the attributes
        dictionary because coordinates are already provided separately.
        """
        data = self._require_loaded()

        attribute_columns = [
            column
            for column in data.columns
            if column != data.geometry.name
        ]

        records: list[ValidationPoint] = []

        for index, row in data.iterrows():
            geometry = row.geometry

            if not isinstance(geometry, Point):
                raise InvalidPointGeometryError(
                    f"Feature at row {index} is not a Point."
                )

            attributes = {
                column: row[column]
                for column in attribute_columns
            }

            records.append(
                ValidationPoint(
                    index=index,
                    x=float(geometry.x),
                    y=float(geometry.y),
                    attributes=attributes,
                )
            )

        return records

    def coordinates(self) -> list[tuple[float, float]]:
        """
        Return all point coordinates.

        Returns
        -------
        list[tuple[float, float]]
            Coordinates as ``(x, y)`` pairs in the source CRS.
        """
        return [
            (point.x, point.y)
            for point in self.records()
        ]

    def attribute_names(self) -> list[str]:
        """
        Return the names of all non-geometry attributes.

        Returns
        -------
        list[str]
            Source attribute names.
        """
        data = self._require_loaded()

        return [
            column
            for column in data.columns
            if column != data.geometry.name
        ]


def load_validation_points(
    path: str | Path,
) -> ValidationPoints:
    """
    Load and return a validation-point dataset.

    Parameters
    ----------
    path:
        Path to the validation-point dataset.

    Returns
    -------
    ValidationPoints
        Loaded validation-point interface.
    """
    return ValidationPoints(path).load()
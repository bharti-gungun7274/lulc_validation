"""
Validation-point utilities for the LULC validation application.

Supports:

- GeoPandas point datasets
- CSV validation-point datasets
- Coordinate extraction
- Attribute preservation
- CRS handling
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
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
    """Clean representation of one validation point."""

    index: Any
    x: float
    y: float
    attributes: dict[str, Any]


class ValidationPoints:
    """Interface for loading and accessing validation points."""

    def __init__(
        self,
        path: str | Path,
        csv_crs: str = "EPSG:4326",
    ) -> None:

        self.path = Path(path)
        self.csv_crs = csv_crs
        self._data: gpd.GeoDataFrame | None = None

    def load(self) -> "ValidationPoints":
        """Load validation points."""

        if not self.path.exists():
            raise PointFileNotFoundError(
                f"Validation-point file does not exist: {self.path}"
            )

        if not self.path.is_file():
            raise PointFileNotFoundError(
                f"Validation-point path is not a file: {self.path}"
            )

        try:

            if self.path.suffix.lower() == ".csv":
                data = self._load_csv()

            else:
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

    def _load_csv(self) -> gpd.GeoDataFrame:
        """Load a CSV containing Latitude and Longitude."""

        df = pd.read_csv(self.path)

        latitude_column = self._find_column(
            df,
            [
                "Latitude",
                "latitude",
                "LATITUDE",
                "lat",
                "Lat",
            ],
        )

        longitude_column = self._find_column(
            df,
            [
                "Longitude",
                "longitude",
                "LONGITUDE",
                "lon",
                "Lon",
            ],
        )

        if latitude_column is None:
            raise InvalidPointDatasetError(
                "CSV does not contain a Latitude column."
            )

        if longitude_column is None:
            raise InvalidPointDatasetError(
                "CSV does not contain a Longitude column."
            )

        df[latitude_column] = pd.to_numeric(
            df[latitude_column],
            errors="coerce",
        )

        df[longitude_column] = pd.to_numeric(
            df[longitude_column],
            errors="coerce",
        )

        if df[latitude_column].isna().any():
            raise InvalidPointDatasetError(
                "CSV contains invalid latitude values."
            )

        if df[longitude_column].isna().any():
            raise InvalidPointDatasetError(
                "CSV contains invalid longitude values."
            )

        geometry = [
            Point(
                float(longitude),
                float(latitude),
            )
            for longitude, latitude in zip(
                df[longitude_column],
                df[latitude_column],
            )
        ]

        return gpd.GeoDataFrame(
            df,
            geometry=geometry,
            crs=self.csv_crs,
        )

    @staticmethod
    def _find_column(
        df: pd.DataFrame,
        candidates: list[str],
    ) -> str | None:

        for candidate in candidates:
            if candidate in df.columns:
                return candidate

        return None

    @staticmethod
    def _validate_geometries(
        data: gpd.GeoDataFrame,
    ) -> None:

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

    def _require_loaded(self) -> gpd.GeoDataFrame:

        if self._data is None:
            raise InvalidPointDatasetError(
                "Validation points are not loaded. "
                "Call load() first."
            )

        return self._data

    @property
    def data(self) -> gpd.GeoDataFrame:
        return self._require_loaded()

    @property
    def crs(self) -> Any:

        data = self._require_loaded()

        if data.crs is None:
            raise MissingPointCRSError(
                f"Validation-point dataset has no CRS: {self.path}"
            )

        return data.crs

    @property
    def count(self) -> int:
        return len(self._require_loaded())

    def records(self) -> list[ValidationPoint]:

        data = self._require_loaded()

        attribute_columns = [
            column
            for column in data.columns
            if column != data.geometry.name
        ]

        records = []

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

        return [
            (point.x, point.y)
            for point in self.records()
        ]

    def attribute_names(self) -> list[str]:

        data = self._require_loaded()

        return [
            column
            for column in data.columns
            if column != data.geometry.name
        ]


def load_validation_points(
    path: str | Path,
) -> ValidationPoints:
    """Load and return validation points."""

    return ValidationPoints(path).load()
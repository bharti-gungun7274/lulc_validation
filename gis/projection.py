"""
Coordinate Reference System (CRS) and projection utilities.

This module provides functionality for:

- Creating and inspecting CRS objects
- Comparing coordinate reference systems
- Transforming coordinates between CRS definitions
- Validating CRS compatibility between spatial datasets

This module does not contain raster processing, validation metrics,
confusion-matrix logic, or GUI/application workflow logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyproj import CRS, Transformer


class ProjectionError(Exception):
    """Base exception for projection-related errors."""


class InvalidCRSError(ProjectionError):
    """Raised when a CRS cannot be interpreted."""


class CRSNotAvailableError(ProjectionError):
    """Raised when a required CRS is missing."""


class CoordinateTransformationError(ProjectionError):
    """Raised when coordinate transformation fails."""


@dataclass(frozen=True)
class Coordinate:
    """Represents a coordinate together with its CRS."""

    x: float
    y: float
    crs: CRS


def get_crs(value: Any) -> CRS:
    """Convert a CRS definition into a pyproj CRS object."""

    if value is None:
        raise CRSNotAvailableError(
            "A CRS is required but none was provided."
        )

    try:
        return CRS.from_user_input(value)
    except Exception as exc:
        raise InvalidCRSError(
            f"Unable to interpret CRS: {value!r}"
        ) from exc


def crs_equal(
    first: Any,
    second: Any,
) -> bool:
    """Return True when two CRS definitions are equivalent."""

    first_crs = get_crs(first)
    second_crs = get_crs(second)

    return first_crs == second_crs


def require_matching_crs(
    first: Any,
    second: Any,
) -> None:
    """Raise an error when two CRS definitions do not match."""

    first_crs = get_crs(first)
    second_crs = get_crs(second)

    if first_crs != second_crs:
        raise ProjectionError(
            "CRS mismatch detected. "
            f"First CRS: {first_crs.to_string()} | "
            f"Second CRS: {second_crs.to_string()}"
        )


def transform_coordinate(
    x: float,
    y: float,
    source_crs: Any,
    target_crs: Any,
) -> tuple[float, float]:
    """Transform one coordinate between CRS definitions."""

    source = get_crs(source_crs)
    target = get_crs(target_crs)

    try:
        transformer = Transformer.from_crs(
            source,
            target,
            always_xy=True,
        )

        transformed_x, transformed_y = transformer.transform(
            x,
            y,
        )

    except Exception as exc:
        raise CoordinateTransformationError(
            "Unable to transform coordinate "
            f"({x}, {y}) from {source.to_string()} "
            f"to {target.to_string()}."
        ) from exc

    return float(transformed_x), float(transformed_y)


def transform_coordinates(
    coordinates: list[tuple[float, float]],
    source_crs: Any,
    target_crs: Any,
) -> list[tuple[float, float]]:
    """Transform multiple coordinates between CRS definitions."""

    source = get_crs(source_crs)
    target = get_crs(target_crs)

    try:
        transformer = Transformer.from_crs(
            source,
            target,
            always_xy=True,
        )

        transformed = [
            transformer.transform(x, y)
            for x, y in coordinates
        ]

    except Exception as exc:
        raise CoordinateTransformationError(
            "Unable to transform the supplied coordinates from "
            f"{source.to_string()} to {target.to_string()}."
        ) from exc

    return [
        (float(x), float(y))
        for x, y in transformed
    ]


def make_coordinate(
    x: float,
    y: float,
    crs: Any,
) -> Coordinate:
    """Create a CRS-aware Coordinate object."""

    parsed_crs = get_crs(crs)

    return Coordinate(
        x=float(x),
        y=float(y),
        crs=parsed_crs,
    )


def transform_coordinate_object(
    coordinate: Coordinate,
    target_crs: Any,
) -> Coordinate:
    """Transform a Coordinate object into another CRS."""

    target = get_crs(target_crs)

    x, y = transform_coordinate(
        coordinate.x,
        coordinate.y,
        coordinate.crs,
        target,
    )

    return Coordinate(
        x=x,
        y=y,
        crs=target,
    )
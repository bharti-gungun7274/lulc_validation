import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow

# GIS modules
from gis.points import (
    ValidationPoints,
    ValidationPoint,
    load_validation_points,
)

from gis.raster import (
    Raster,
    RasterMetadata,
    open_raster,
)

from gis.projection import (
    Coordinate,
    get_crs,
    crs_equal,
    require_matching_crs,
    transform_coordinate,
    transform_coordinates,
    make_coordinate,
    transform_coordinate_object,
)

# Validation modules
from validation.confusion_matrix import (
    create_confusion_matrix,
)

from validation.metrics import (
    calculate_metrics,
)

from validation.validator import (
    load_validation_points as load_csv_validation_points,
    prepare_validation_data,
    validate_dataframe,
    validate_csv,
)


def main():
    """
    Start the LULC Validation GUI application.
    """

    # --------------------------------------------------------
    # Create Qt application
    # --------------------------------------------------------

    app = QApplication(sys.argv)

    # --------------------------------------------------------
    # Create main GUI window
    # --------------------------------------------------------

    window = MainWindow()

    # --------------------------------------------------------
    # Give the GUI access to the GIS functionality
    # --------------------------------------------------------

    window.ValidationPoints = ValidationPoints
    window.ValidationPoint = ValidationPoint
    window.load_validation_points = load_validation_points

    window.Raster = Raster
    window.RasterMetadata = RasterMetadata
    window.open_raster = open_raster

    window.Coordinate = Coordinate
    window.get_crs = get_crs
    window.crs_equal = crs_equal
    window.require_matching_crs = require_matching_crs
    window.transform_coordinate = transform_coordinate
    window.transform_coordinates = transform_coordinates
    window.make_coordinate = make_coordinate
    window.transform_coordinate_object = (
        transform_coordinate_object
    )

    # --------------------------------------------------------
    # Give the GUI access to the validation functionality
    # --------------------------------------------------------

    window.create_confusion_matrix = (
        create_confusion_matrix
    )

    window.calculate_metrics = (
        calculate_metrics
    )

    window.validate_dataframe = (
        validate_dataframe
    )

    window.validate_csv = (
        validate_csv
    )

    # --------------------------------------------------------
    # Show GUI
    # --------------------------------------------------------

    window.show()

    # --------------------------------------------------------
    # Start Qt event loop
    # --------------------------------------------------------

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
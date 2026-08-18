from pathlib import Path

import pandas as pd

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import FileSelector

from gis.points import load_validation_points

from gis.rasters import (
    CoordinateOutsideRasterError,
    NoDataValueError,
    open_raster,
)

from gis.projection import (
    transform_coordinate,
)

from validation.confusion_matrix import (
    CLASS_NAMES,
    create_confusion_matrix,
)

from validation.metrics import (
    calculate_metrics,
)


class MainWindow(QMainWindow):
    """Main window for the LULC validation application."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "LULC Validation Tool"
        )

        self.resize(
            1500,
            900,
        )

        # --------------------------------------------------
        # Application state
        # --------------------------------------------------

        self.points = None

        self.dw_raster = None

        self.reference_raster = None

        self.point_records = []

        self.results = []

        self.current_index = 0

        self.validation_dataframe = None

        self.confusion_matrix = None

        self.metrics = None

        # --------------------------------------------------
        # Build GUI
        # --------------------------------------------------

        self._build_ui()

    # ======================================================
    # UI
    # ======================================================

    def _build_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        main_layout = QVBoxLayout(
            central
        )

        # --------------------------------------------------
        # Title
        # --------------------------------------------------

        title = QLabel(
            "LULC VALIDATION TOOL"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 30px;
                font-weight: bold;
                padding: 20px;
            }
            """
        )

        main_layout.addWidget(
            title
        )

        subtitle = QLabel(
            "Dynamic World / LULC Classification Validation"
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addWidget(
            subtitle
        )

        # --------------------------------------------------
        # Input section
        # --------------------------------------------------

        input_group = QGroupBox(
            "Input Data"
        )

        input_layout = QVBoxLayout(
            input_group
        )

        self.dw_selector = FileSelector(
            "DW LULC Raster:"
        )

        self.reference_selector = FileSelector(
            "Reference Map:"
        )

        self.points_selector = FileSelector(
            "Validation Points:"
        )

        self.dw_selector.browse_button.clicked.connect(
            self._browse_raster
        )

        self.reference_selector.browse_button.clicked.connect(
            self._browse_raster
        )

        self.points_selector.browse_button.clicked.connect(
            self._browse_points
        )

        input_layout.addWidget(
            self.dw_selector
        )

        input_layout.addWidget(
            self.reference_selector
        )

        input_layout.addWidget(
            self.points_selector
        )

        main_layout.addWidget(
            input_group
        )

        # --------------------------------------------------
        # Validate button
        # --------------------------------------------------

        self.validate_button = QPushButton(
            "Run Validation"
        )

        self.validate_button.setMinimumHeight(
            40
        )

        self.validate_button.clicked.connect(
            self.run_validation
        )

        main_layout.addWidget(
            self.validate_button
        )

        # --------------------------------------------------
        # Progress
        # --------------------------------------------------

        progress_group = QGroupBox(
            "Validation Progress"
        )

        progress_layout = QVBoxLayout(
            progress_group
        )

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100
        )

        self.progress_bar.setValue(
            0
        )

        progress_layout.addWidget(
            self.progress_bar
        )

        main_layout.addWidget(
            progress_group
        )

        # --------------------------------------------------
        # Current point
        # --------------------------------------------------

        point_group = QGroupBox(
            "Current Validation Point"
        )

        point_layout = QVBoxLayout(
            point_group
        )

        self.point_label = QLabel(
            "Point: 0 / 0"
        )

        self.coordinate_label = QLabel(
            "Coordinates: -"
        )

        self.dw_class_label = QLabel(
            "DW Class: -"
        )

        self.reference_class_label = QLabel(
            "Reference Class: -"
        )

        self.result_label = QLabel(
            "Result: -"
        )

        point_layout.addWidget(
            self.point_label
        )

        point_layout.addWidget(
            self.coordinate_label
        )

        point_layout.addWidget(
            self.dw_class_label
        )

        point_layout.addWidget(
            self.reference_class_label
        )

        point_layout.addWidget(
            self.result_label
        )

        navigation_layout = QHBoxLayout()

        self.previous_button = QPushButton(
            "< Previous"
        )

        self.next_button = QPushButton(
            "Next >"
        )

        self.previous_button.clicked.connect(
            self.previous_point
        )

        self.next_button.clicked.connect(
            self.next_point
        )

        self.previous_button.setEnabled(
            False
        )

        self.next_button.setEnabled(
            False
        )

        navigation_layout.addWidget(
            self.previous_button
        )

        navigation_layout.addStretch()

        navigation_layout.addWidget(
            self.next_button
        )

        point_layout.addLayout(
            navigation_layout
        )

        main_layout.addWidget(
            point_group
        )

        # --------------------------------------------------
        # Results
        # --------------------------------------------------

        result_group = QGroupBox(
            "Validation Results"
        )

        result_layout = QVBoxLayout(
            result_group
        )

        metrics_layout = QHBoxLayout()

        metrics_labels = QVBoxLayout()

        metrics_values = QVBoxLayout()

        metrics_labels.addWidget(
            QLabel("Overall Accuracy:")
        )

        metrics_labels.addWidget(
            QLabel("Kappa:")
        )

        self.accuracy_value = QLabel(
            "-"
        )

        self.kappa_value = QLabel(
            "-"
        )

        metrics_values.addWidget(
            self.accuracy_value
        )

        metrics_values.addWidget(
            self.kappa_value
        )

        metrics_layout.addLayout(
            metrics_labels
        )

        metrics_layout.addLayout(
            metrics_values
        )

        metrics_layout.addStretch()

        result_layout.addLayout(
            metrics_layout
        )

        self.confusion_button = QPushButton(
            "Confusion Matrix"
        )

        self.export_button = QPushButton(
            "Export Results"
        )

        self.confusion_button.clicked.connect(
            self.show_confusion_matrix
        )

        self.export_button.clicked.connect(
            self.export_results
        )

        self.confusion_button.setEnabled(
            False
        )

        self.export_button.setEnabled(
            False
        )

        result_layout.addWidget(
            self.confusion_button
        )

        result_layout.addWidget(
            self.export_button
        )

        main_layout.addWidget(
            result_group
        )

    # ======================================================
    # Browse
    # ======================================================

    def _browse_raster(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Raster",
            "",
            "Raster files (*.tif *.tiff *.img);;All files (*)",
        )

        if not path:
            return

        sender = self.sender()

        if sender is self.dw_selector.browse_button:
            self.dw_selector.set_path(path)

        elif sender is self.reference_selector.browse_button:
            self.reference_selector.set_path(path)

    def _browse_points(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Validation Points",
            "",
            "CSV files (*.csv);;Vector files (*.shp *.gpkg);;All files (*)",
        )

        if path:
            self.points_selector.set_path(
                path
            )

    # ======================================================
    # Main validation
    # ======================================================

    def run_validation(self):

        dw_path = self.dw_selector.path()

        reference_path = (
            self.reference_selector.path()
        )

        points_path = (
            self.points_selector.path()
        )

        # --------------------------------------------------
        # Check input paths
        # --------------------------------------------------

        if not dw_path:
            self._show_error(
                "Please select the Dynamic World raster."
            )
            return

        if not reference_path:
            self._show_error(
                "Please select the reference map."
            )
            return

        if not points_path:
            self._show_error(
                "Please select the validation points."
            )
            return

        try:

            self.validate_button.setEnabled(
                False
            )

            self.progress_bar.setValue(
                0
            )

            # --------------------------------------------------
            # Load validation points
            # --------------------------------------------------

            self.points = (
                load_validation_points(
                    points_path
                )
            )

            self.point_records = (
                self.points.records()
            )

            if not self.point_records:
                raise ValueError(
                    "No validation points were found."
                )

            # --------------------------------------------------
            # Open rasters
            # --------------------------------------------------

            self.dw_raster = open_raster(
                dw_path
            )

            self.reference_raster = open_raster(
                reference_path
            )

            # --------------------------------------------------
            # Process points
            # --------------------------------------------------

            self.results = []

            total = len(
                self.point_records
            )

            for index, point in enumerate(
                self.point_records
            ):

                result = self._process_point(
                    point
                )

                self.results.append(
                    result
                )

                progress = int(
                    ((index + 1) / total)
                    * 100
                )

                self.progress_bar.setValue(
                    progress
                )

            # --------------------------------------------------
            # Create validation dataframe
            # --------------------------------------------------

            valid_results = [
                result
                for result in self.results
                if result["status"] == "VALID"
            ]

            if not valid_results:
                raise ValueError(
                    "None of the validation points "
                    "produced valid class values."
                )

            self.validation_dataframe = (
                pd.DataFrame(
                    valid_results
                )
            )

            # --------------------------------------------------
            # Calculate metrics
            # --------------------------------------------------

            reference = (
                self.validation_dataframe[
                    "Reference_Class"
                ].to_numpy()
            )

            predicted = (
                self.validation_dataframe[
                    "DW_Class"
                ].to_numpy()
            )

            self.confusion_matrix = (
                create_confusion_matrix(
                    reference,
                    predicted,
                )
            )

            self.metrics = (
                calculate_metrics(
                    reference,
                    predicted,
                )
            )

            # --------------------------------------------------
            # Update results
            # --------------------------------------------------

            accuracy = (
                self.metrics[
                    "overall_accuracy"
                ]
                * 100
            )

            kappa = self.metrics[
                "kappa"
            ]

            self.accuracy_value.setText(
                f"{accuracy:.2f}%"
            )

            self.kappa_value.setText(
                f"{kappa:.4f}"
            )

            # --------------------------------------------------
            # Display first point
            # --------------------------------------------------

            self.current_index = 0

            self.update_current_point()

            self.previous_button.setEnabled(
                False
            )

            self.next_button.setEnabled(
                len(self.results) > 1
            )

            self.confusion_button.setEnabled(
                True
            )

            self.export_button.setEnabled(
                True
            )

            QMessageBox.information(
                self,
                "Validation Complete",
                (
                    "Validation completed successfully.\n\n"
                    f"Total points: {total}\n"
                    f"Valid points: {len(valid_results)}\n"
                    f"Overall Accuracy: {accuracy:.2f}%\n"
                    f"Kappa: {kappa:.4f}"
                ),
            )

        except Exception as exc:

            self.progress_bar.setValue(
                0
            )

            QMessageBox.critical(
                self,
                "Validation Error",
                str(exc),
            )

        finally:

            self.validate_button.setEnabled(
                True
            )

    # ======================================================
    # Process one point
    # ======================================================

    def _process_point(
        self,
        point,
    ):

        x = point.x
        y = point.y

        attributes = point.attributes

        point_id = attributes.get(
            "Point_ID",
            point.index,
        )

        year = attributes.get(
            "Year",
            "",
        )

        # --------------------------------------------------
        # Transform point into DW CRS
        # --------------------------------------------------

        dw_x, dw_y = transform_coordinate(
            x,
            y,
            self.points.crs,
            self.dw_raster.crs,
        )

        # --------------------------------------------------
        # Dynamic World class
        # --------------------------------------------------

        dw_class = self.dw_raster.value_at(
            dw_x,
            dw_y,
            band=1,
        )

        dw_class = int(
            dw_class
        )

        # --------------------------------------------------
        # Reference class
        # --------------------------------------------------

        reference_class = (
            self._get_reference_class(
                point,
                x,
                y,
            )
        )

        # --------------------------------------------------
        # Validate class values
        # --------------------------------------------------

        if dw_class not in range(9):
            return {
                "Point_ID": point_id,
                "Latitude": y,
                "Longitude": x,
                "Year": year,
                "Reference_Class": reference_class,
                "DW_Class": dw_class,
                "status": "INVALID",
                "Result": "Invalid DW class",
            }

        if reference_class not in range(9):
            return {
                "Point_ID": point_id,
                "Latitude": y,
                "Longitude": x,
                "Year": year,
                "Reference_Class": reference_class,
                "DW_Class": dw_class,
                "status": "INVALID",
                "Result": "Invalid reference class",
            }

        result = (
            "MATCH"
            if reference_class == dw_class
            else "MISMATCH"
        )

        return {
            "Point_ID": point_id,
            "Latitude": y,
            "Longitude": x,
            "Year": year,
            "Reference_Class": reference_class,
            "DW_Class": dw_class,
            "status": "VALID",
            "Result": result,
        }

    # ======================================================
    # Reference class
    # ======================================================

    def _get_reference_class(
        self,
        point,
        x,
        y,
    ):

        attributes = point.attributes

        # --------------------------------------------------
        # Option 1:
        # Reference_Class already exists in CSV
        # --------------------------------------------------

        if "Reference_Class" in attributes:

            value = attributes[
                "Reference_Class"
            ]

            if pd.notna(value):

                value = int(
                    float(value)
                )

                if value in range(9):
                    return value

        # --------------------------------------------------
        # Option 2:
        # Reference raster is a single-band
        # class raster
        # --------------------------------------------------

        if self.reference_raster.count == 1:

            ref_x, ref_y = (
                transform_coordinate(
                    x,
                    y,
                    self.points.crs,
                    self.reference_raster.crs,
                )
            )

            value = (
                self.reference_raster.value_at(
                    ref_x,
                    ref_y,
                    band=1,
                )
            )

            return int(
                value
            )

        # --------------------------------------------------
        # RGB reference image
        # --------------------------------------------------

        raise ValueError(
            "The reference raster contains multiple bands "
            "and the CSV does not contain a valid "
            "Reference_Class column.\n\n"
            "An RGB reference image cannot automatically "
            "be converted into LULC class IDs 0-8.\n\n"
            "Please provide a single-band reference-class "
            "raster or add Reference_Class to the "
            "validation CSV."
        )

    # ======================================================
    # Point navigation
    # ======================================================

    def update_current_point(self):

        if not self.results:
            return

        result = self.results[
            self.current_index
        ]

        total = len(
            self.results
        )

        current = (
            self.current_index + 1
        )

        self.point_label.setText(
            f"Point: {current} / {total}"
        )

        self.coordinate_label.setText(
            "Coordinates: "
            f"{result['Latitude']:.6f}, "
            f"{result['Longitude']:.6f}"
        )

        dw_class = result.get(
            "DW_Class",
            "-",
        )

        reference_class = result.get(
            "Reference_Class",
            "-",
        )

        self.dw_class_label.setText(
            "DW Class: "
            f"{self._class_name(dw_class)}"
        )

        self.reference_class_label.setText(
            "Reference Class: "
            f"{self._class_name(reference_class)}"
        )

        self.result_label.setText(
            "Result: "
            f"{result.get('Result', '-')}"
        )

        # --------------------------------------------------
        # Navigation buttons
        # --------------------------------------------------

        self.previous_button.setEnabled(
            self.current_index > 0
        )

        self.next_button.setEnabled(
            self.current_index < total - 1
        )

    def next_point(self):

        if not self.results:
            return

        if self.current_index < (
            len(self.results) - 1
        ):

            self.current_index += 1

            self.update_current_point()

    def previous_point(self):

        if self.current_index > 0:

            self.current_index -= 1

            self.update_current_point()

    # ======================================================
    # Class name
    # ======================================================

    @staticmethod
    def _class_name(
        class_id,
    ):

        try:

            class_id = int(
                class_id
            )

            if class_id in CLASS_NAMES:
                return (
                    f"{class_id} - "
                    f"{CLASS_NAMES[class_id]}"
                )

        except (
            TypeError,
            ValueError,
        ):
            pass

        return str(
            class_id
        )

    # ======================================================
    # Confusion matrix
    # ======================================================

    def show_confusion_matrix(self):

        if self.confusion_matrix is None:
            self._show_error(
                "Run validation first."
            )
            return

        dialog = QMainWindow(
            self
        )

        dialog.setWindowTitle(
            "Confusion Matrix"
        )

        dialog.resize(
            900,
            600,
        )

        table = QTableWidget(
            dialog
        )

        matrix = (
            self.confusion_matrix
        )

        table.setRowCount(
            len(matrix.index)
        )

        table.setColumnCount(
            len(matrix.columns)
        )

        table.setVerticalHeaderLabels(
            list(matrix.index)
        )

        table.setHorizontalHeaderLabels(
            list(matrix.columns)
        )

        for row in range(
            len(matrix.index)
        ):

            for column in range(
                len(matrix.columns)
            ):

                value = matrix.iloc[
                    row,
                    column,
                ]

                table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        str(value)
                    ),
                )

        table.resizeColumnsToContents()

        dialog.setCentralWidget(
            table
        )

        dialog.show()

        self._confusion_dialog = (
            dialog
        )

    # ======================================================
    # Export
    # ======================================================

    def export_results(self):

        if self.validation_dataframe is None:
            self._show_error(
                "Run validation first."
            )
            return

        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
        )

        if not directory:
            return

        output_directory = Path(
            directory
        )

        try:

            # --------------------------------------------------
            # Validation point results
            # --------------------------------------------------

            self.validation_dataframe.to_csv(
                output_directory
                / "validation_results.csv",
                index=False,
            )

            # --------------------------------------------------
            # Confusion matrix
            # --------------------------------------------------

            self.confusion_matrix.to_csv(
                output_directory
                / "confusion_matrix.csv"
            )

            # --------------------------------------------------
            # Summary
            # --------------------------------------------------

            summary = pd.DataFrame(
                [
                    {
                        "Validation_Points": len(
                            self.validation_dataframe
                        ),
                        "Overall_Accuracy": (
                            self.metrics[
                                "overall_accuracy"
                            ]
                        ),
                        "Kappa": (
                            self.metrics[
                                "kappa"
                            ]
                        ),
                    }
                ]
            )

            summary.to_csv(
                output_directory
                / "accuracy_summary.csv",
                index=False,
            )

            QMessageBox.information(
                self,
                "Export Complete",
                (
                    "Validation results exported successfully.\n\n"
                    f"Location:\n{output_directory}"
                ),
            )

        except Exception as exc:

            self._show_error(
                f"Unable to export results:\n\n{exc}"
            )

    # ======================================================
    # Error helper
    # ======================================================

    def _show_error(
        self,
        message: str,
    ):

        QMessageBox.critical(
            self,
            "Validation Error",
            message,
        )

    # ======================================================
    # Close
    # ======================================================

    def closeEvent(self, event):

        if self.dw_raster is not None:
            self.dw_raster.close()

        if self.reference_raster is not None:
            self.reference_raster.close()

        event.accept()
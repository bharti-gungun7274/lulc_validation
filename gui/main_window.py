import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QProgressBar,
    QLabel,
    QMessageBox,
)

from PySide6.QtCore import Qt

from gui.widgets import (
    FileSelector,
    ValidationPointWidget,
    ResultsWidget,
)


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        # ----------------------------------------------------
        # Window Settings
        # ----------------------------------------------------

        self.setWindowTitle(
            "LULC Validation Tool"
        )

        self.setMinimumSize(
            900,
            650
        )

        # ----------------------------------------------------
        # Application Data
        # ----------------------------------------------------

        self.total_points = 240

        self.current_point = 0

        # ----------------------------------------------------
        # Build GUI
        # ----------------------------------------------------

        self.setup_ui()

    # ========================================================
    # SETUP UI
    # ========================================================

    def setup_ui(self):

        # ----------------------------------------------------
        # Central Widget
        # ----------------------------------------------------

        central_widget = QWidget()

        self.setCentralWidget(
            central_widget
        )

        main_layout = QVBoxLayout()

        central_widget.setLayout(
            main_layout
        )

        # ====================================================
        # TITLE
        # ====================================================

        title = QLabel(
            "LULC VALIDATION TOOL"
        )

        title.setAlignment(
            Qt.AlignCenter
        )

        title_font = title.font()

        title_font.setPointSize(
            20
        )

        title_font.setBold(
            True
        )

        title.setFont(
            title_font
        )

        main_layout.addWidget(
            title
        )

        subtitle = QLabel(
            "Dynamic World / LULC Classification Validation"
        )

        subtitle.setAlignment(
            Qt.AlignCenter
        )

        main_layout.addWidget(
            subtitle
        )

        # ====================================================
        # INPUT DATA
        # ====================================================

        input_group = QGroupBox(
            "Input Data"
        )

        input_layout = QVBoxLayout()

        input_group.setLayout(
            input_layout
        )

        # ----------------------------------------------------
        # Dynamic World Raster
        # ----------------------------------------------------

        self.dw_selector = FileSelector(
            label_text="DW LULC Raster:",
            file_filter=(
                "Raster Files (*.tif *.tiff);;"
                "All Files (*)"
            )
        )

        input_layout.addWidget(
            self.dw_selector
        )

        # ----------------------------------------------------
        # Reference Map
        # ----------------------------------------------------

        self.reference_selector = FileSelector(
            label_text="Reference Map:",
            file_filter=(
                "Raster Files (*.tif *.tiff);;"
                "All Files (*)"
            )
        )

        input_layout.addWidget(
            self.reference_selector
        )

        # ----------------------------------------------------
        # Validation Points
        # ----------------------------------------------------

        self.points_selector = FileSelector(
            label_text="Validation Points:",
            file_filter=(
                "GIS Files "
                "(*.shp *.geojson *.gpkg *.csv);;"
                "Shapefile (*.shp);;"
                "GeoJSON (*.geojson);;"
                "GeoPackage (*.gpkg);;"
                "CSV (*.csv);;"
                "All Files (*)"
            )
        )

        input_layout.addWidget(
            self.points_selector
        )

        main_layout.addWidget(
            input_group
        )

        # ====================================================
        # RUN VALIDATION BUTTON
        # ====================================================

        self.run_button = QPushButton(
            "RUN VALIDATION"
        )

        self.run_button.setMinimumHeight(
            45
        )

        self.run_button.clicked.connect(
            self.run_validation
        )

        main_layout.addWidget(
            self.run_button
        )

        # ====================================================
        # PROGRESS
        # ====================================================

        progress_group = QGroupBox(
            "Validation Progress"
        )

        progress_layout = QVBoxLayout()

        progress_group.setLayout(
            progress_layout
        )

        # Progress bar

        self.progress_bar = QProgressBar()

        self.progress_bar.setMinimum(
            0
        )

        self.progress_bar.setMaximum(
            self.total_points
        )

        self.progress_bar.setValue(
            0
        )

        progress_layout.addWidget(
            self.progress_bar
        )

        # Progress text

        self.progress_label = QLabel(
            f"0 / {self.total_points}"
        )

        self.progress_label.setAlignment(
            Qt.AlignCenter
        )

        progress_layout.addWidget(
            self.progress_label
        )

        main_layout.addWidget(
            progress_group
        )

        # ====================================================
        # CURRENT POINT
        # ====================================================

        point_group = QGroupBox(
            "Current Validation Point"
        )

        point_layout = QVBoxLayout()

        point_group.setLayout(
            point_layout
        )

        self.point_widget = ValidationPointWidget(
            total_points=self.total_points
        )

        point_layout.addWidget(
            self.point_widget
        )

        main_layout.addWidget(
            point_group
        )

        # ====================================================
        # NAVIGATION
        # ====================================================

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

        navigation_layout.addWidget(
            self.previous_button
        )

        navigation_layout.addStretch()

        navigation_layout.addWidget(
            self.next_button
        )

        main_layout.addLayout(
            navigation_layout
        )

        # ====================================================
        # RESULTS
        # ====================================================

        results_group = QGroupBox(
            "Validation Results"
        )

        results_layout = QVBoxLayout()

        results_group.setLayout(
            results_layout
        )

        self.results_widget = ResultsWidget()

        # Connect widget signals

        self.results_widget.confusion_matrix_requested.connect(
            self.show_confusion_matrix
        )

        self.results_widget.export_requested.connect(
            self.export_results
        )

        results_layout.addWidget(
            self.results_widget
        )

        main_layout.addWidget(
            results_group
        )

        # ====================================================
        # STATUS BAR
        # ====================================================

        self.statusBar().showMessage(
            "Ready"
        )

    # ========================================================
    # RUN VALIDATION
    # ========================================================

    def run_validation(self):

        # Get file paths from our custom widgets

        dw_file = self.dw_selector.get_path()

        reference_file = (
            self.reference_selector.get_path()
        )

        points_file = (
            self.points_selector.get_path()
        )

        # ----------------------------------------------------
        # Check Dynamic World raster
        # ----------------------------------------------------

        if not dw_file:

            QMessageBox.warning(
                self,
                "Missing Data",
                "Please select the Dynamic World raster."
            )

            return

        # ----------------------------------------------------
        # Check reference map
        # ----------------------------------------------------

        if not reference_file:

            QMessageBox.warning(
                self,
                "Missing Data",
                "Please select the reference map."
            )

            return

        # ----------------------------------------------------
        # Check validation points
        # ----------------------------------------------------

        if not points_file:

            QMessageBox.warning(
                self,
                "Missing Data",
                "Please select the validation points."
            )

            return

        # ----------------------------------------------------
        # Temporary message
        # ----------------------------------------------------

        self.statusBar().showMessage(
            "Validation started..."
        )

        QMessageBox.information(
            self,
            "Validation",
            "All input files have been selected.\n\n"
            "The GIS validation engine will be connected next."
        )

    # ========================================================
    # NEXT POINT
    # ========================================================

    def next_point(self):

        if self.current_point < self.total_points:

            self.current_point += 1

        self.update_point_display()

    # ========================================================
    # PREVIOUS POINT
    # ========================================================

    def previous_point(self):

        if self.current_point > 1:

            self.current_point -= 1

        self.update_point_display()

    # ========================================================
    # UPDATE POINT DISPLAY
    # ========================================================

    def update_point_display(self):

        # Update progress bar

        self.progress_bar.setValue(
            self.current_point
        )

        # Update progress text

        self.progress_label.setText(
            f"{self.current_point} / {self.total_points}"
        )

        # Update point widget

        self.point_widget.point_value.setText(
            f"{self.current_point} / {self.total_points}"
        )

    # ========================================================
    # CONFUSION MATRIX
    # ========================================================

    def show_confusion_matrix(self):

        QMessageBox.information(
            self,
            "Confusion Matrix",
            "The confusion matrix will be displayed here."
        )

    # ========================================================
    # EXPORT
    # ========================================================

    def export_results(self):

        QMessageBox.information(
            self,
            "Export Results",
            "The validation results will be exported here."
        )


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def run_app():

    app = QApplication(
        sys.argv
    )

    window = MainWindow()

    window.show()

    sys.exit(
        app.exec()
    )


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    run_app()
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
)

from PySide6.QtCore import Signal


# ============================================================
# FILE SELECTOR
# ============================================================

class FileSelector(QWidget):
    """
    A reusable widget containing:

        Label + File path box + Browse button
    """

    file_selected = Signal(str)

    def __init__(
        self,
        label_text="File:",
        file_filter="All Files (*)",
        parent=None
    ):
        super().__init__(parent)

        self.file_filter = file_filter

        # ----------------------------------------------------
        # Layout
        # ----------------------------------------------------

        layout = QHBoxLayout()

        # Remove unnecessary spacing around the widget
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        self.label = QLabel(label_text)

        # Text box
        self.path_edit = QLineEdit()

        self.path_edit.setPlaceholderText(
            "Select a file..."
        )

        # Browse button
        self.browse_button = QPushButton(
            "Browse..."
        )

        self.browse_button.clicked.connect(
            self.browse_file
        )

        # Add widgets to layout
        layout.addWidget(self.label)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_button)

        self.setLayout(layout)

    # --------------------------------------------------------
    # Browse for file
    # --------------------------------------------------------

    def browse_file(self):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File",
            "",
            self.file_filter
        )

        if file_path:

            self.path_edit.setText(
                file_path
            )

            self.file_selected.emit(
                file_path
            )

    # --------------------------------------------------------
    # Get selected file path
    # --------------------------------------------------------

    def get_path(self):

        return self.path_edit.text()

    # --------------------------------------------------------
    # Set file path
    # --------------------------------------------------------

    def set_path(self, path):

        self.path_edit.setText(path)


# ============================================================
# VALIDATION POINT WIDGET
# ============================================================

class ValidationPointWidget(QWidget):
    """
    Displays information about the current validation point.
    """

    def __init__(
        self,
        total_points=240,
        parent=None
    ):
        super().__init__(parent)

        self.total_points = total_points

        layout = QGridLayout()

        # ----------------------------------------------------
        # Point Number
        # ----------------------------------------------------

        layout.addWidget(
            QLabel("Point:"),
            0,
            0
        )

        self.point_value = QLabel(
            f"0 / {self.total_points}"
        )

        layout.addWidget(
            self.point_value,
            0,
            1
        )

        # ----------------------------------------------------
        # Coordinates
        # ----------------------------------------------------

        layout.addWidget(
            QLabel("Coordinates:"),
            1,
            0
        )

        self.coordinates_value = QLabel("-")

        layout.addWidget(
            self.coordinates_value,
            1,
            1
        )

        # ----------------------------------------------------
        # Dynamic World Class
        # ----------------------------------------------------

        layout.addWidget(
            QLabel("DW Class:"),
            2,
            0
        )

        self.dw_class_value = QLabel("-")

        layout.addWidget(
            self.dw_class_value,
            2,
            1
        )

        # ----------------------------------------------------
        # Reference Class
        # ----------------------------------------------------

        layout.addWidget(
            QLabel("Reference Class:"),
            3,
            0
        )

        self.reference_class_value = QLabel("-")

        layout.addWidget(
            self.reference_class_value,
            3,
            1
        )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        layout.addWidget(
            QLabel("Result:"),
            4,
            0
        )

        self.result_value = QLabel("-")

        result_font = self.result_value.font()
        result_font.setBold(True)

        self.result_value.setFont(
            result_font
        )

        layout.addWidget(
            self.result_value,
            4,
            1
        )

        self.setLayout(layout)

    # --------------------------------------------------------
    # Update current point
    # --------------------------------------------------------

    def update_point(
        self,
        point_number,
        coordinates,
        dw_class,
        reference_class
    ):

        self.point_value.setText(
            f"{point_number} / {self.total_points}"
        )

        self.coordinates_value.setText(
            str(coordinates)
        )

        self.dw_class_value.setText(
            str(dw_class)
        )

        self.reference_class_value.setText(
            str(reference_class)
        )

        # Compare classes

        if dw_class == reference_class:

            self.result_value.setText(
                "MATCH"
            )

        else:

            self.result_value.setText(
                "MISMATCH"
            )

    # --------------------------------------------------------
    # Clear current point
    # --------------------------------------------------------

    def clear(self):

        self.point_value.setText(
            f"0 / {self.total_points}"
        )

        self.coordinates_value.setText("-")
        self.dw_class_value.setText("-")
        self.reference_class_value.setText("-")
        self.result_value.setText("-")


# ============================================================
# RESULTS WIDGET
# ============================================================

class ResultsWidget(QWidget):
    """
    Displays overall validation statistics.
    """

    confusion_matrix_requested = Signal()
    export_requested = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        layout = QGridLayout()

        # ----------------------------------------------------
        # Overall Accuracy
        # ----------------------------------------------------

        layout.addWidget(
            QLabel("Overall Accuracy:"),
            0,
            0
        )

        self.accuracy_value = QLabel("-")

        layout.addWidget(
            self.accuracy_value,
            0,
            1
        )

        # ----------------------------------------------------
        # Kappa
        # ----------------------------------------------------

        layout.addWidget(
            QLabel("Kappa:"),
            1,
            0
        )

        self.kappa_value = QLabel("-")

        layout.addWidget(
            self.kappa_value,
            1,
            1
        )

        # ----------------------------------------------------
        # Confusion Matrix
        # ----------------------------------------------------

        self.confusion_button = QPushButton(
            "Confusion Matrix"
        )

        self.confusion_button.clicked.connect(
            self.confusion_matrix_requested.emit
        )

        layout.addWidget(
            self.confusion_button,
            0,
            2
        )

        # ----------------------------------------------------
        # Export
        # ----------------------------------------------------

        self.export_button = QPushButton(
            "Export Results"
        )

        self.export_button.clicked.connect(
            self.export_requested.emit
        )

        layout.addWidget(
            self.export_button,
            1,
            2
        )

        self.setLayout(layout)

    # --------------------------------------------------------
    # Update results
    # --------------------------------------------------------

    def update_results(
        self,
        accuracy,
        kappa
    ):

        self.accuracy_value.setText(
            f"{accuracy:.2f}%"
        )

        self.kappa_value.setText(
            f"{kappa:.4f}"
        )

    # --------------------------------------------------------
    # Clear results
    # --------------------------------------------------------

    def clear(self):

        self.accuracy_value.setText("-")
        self.kappa_value.setText("-")
import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from validation.validator import validate_csv


def main():

    # Create Qt application
    app = QApplication(sys.argv)

    # Create main window
    window = MainWindow()

    # Connect validation engine to GUI
    window.validate_csv = validate_csv

    # Show GUI
    window.show()

    # Start application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
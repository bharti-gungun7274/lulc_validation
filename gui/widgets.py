from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class FileSelector(QWidget):
    """Widget containing a path field and Browse button."""

    def __init__(
        self,
        label: str,
        parent=None,
    ):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.label = QLabel(label)

        self.path_edit = QLineEdit()

        self.browse_button = QPushButton(
            "Browse..."
        )

        layout.addWidget(
            self.label
        )

        layout.addWidget(
            self.path_edit,
            1,
        )

        layout.addWidget(
            self.browse_button
        )

    def path(self) -> str:
        return self.path_edit.text().strip()

    def set_path(self, path: str) -> None:
        self.path_edit.setText(path)
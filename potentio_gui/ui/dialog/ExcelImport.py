import logging

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import (
    QClipboard,
    QIcon,
    QGuiApplication,
    QMovie,
    QShortcut,
    QKeySequence,
)
from PyQt6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QPlainTextEdit,
    QLabel,
    QDialogButtonBox,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)
from black.trans import Callable

from potentio_gui.ui.Line import QVLine
from potentio_gui.ui.PotentiometrieWidgets import OptionalDatapoint
from potentio_gui.ui.assets import COPY_EXCEL_GIF


class ExcelImport(QDialog):
    def __init__(
        self,
        on_accept: Callable[[list[OptionalDatapoint]], None],
        parent: QWidget = None,
    ):
        self.logger = logging.getLogger(__name__)
        self.on_accept = on_accept
        super().__init__(parent=parent)

        self.setWindowTitle("Template Erstellen")
        self.setWindowIcon(parent.windowIcon())

        layout = QVBoxLayout()
        self.label = QLabel("Excel Dateien hier rein pasten (Strg + V)")
        layout.addWidget(self.label)
        paste_button = QPushButton(
            icon=QIcon.fromTheme("edit-paste"),
            parent=self,
            text="Aus Zwischenablage einfügen",
        )
        paste_button.clicked.connect(self.__paste)
        layout.addWidget(paste_button)
        self.text_frame = QPlainTextEdit(parent=self)
        layout.addWidget(self.text_frame)

        # Close button
        self.buttonbox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)
        layout.addWidget(self.buttonbox)

        master_layout = QHBoxLayout(self)
        paste_widget = QWidget(parent=self)
        paste_widget.setLayout(layout)
        master_layout.addWidget(paste_widget)
        master_layout.addWidget(QVLine())
        gif_widget = GifWidget(gif_path=str(COPY_EXCEL_GIF), parent=self)
        master_layout.addWidget(gif_widget)

        self.setLayout(master_layout)

        # Accept the dialog on Ctrl+Enter
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.activated.connect(self.accept)
        shortcut2 = QShortcut(QKeySequence("Ctrl+Enter"), self)
        shortcut2.activated.connect(self.accept)
        self.text_frame.setFocus()

    def __paste(self):
        text = QGuiApplication.clipboard().text(QClipboard.Mode.Clipboard)
        if text != "":
            self.text_frame.setPlainText(text)

    def accept(self):
        self.logger.debug("Accepting with text '%s'" % self.text_frame.toPlainText())
        text = self.text_frame.toPlainText().replace(
            ",", ".", 1000
        )  # Convert german decimal denominator "," to "." for python processing
        try:
            data = [row.split("\t") for row in text.splitlines(False)]
            return_data = [
                OptionalDatapoint(float(row[0]), float(row[1])) for row in data
            ]
            self.logger.debug(return_data)
            self.on_accept(return_data)
            super().accept()
        except IndexError as err:
            self.logger.exception(f"Could not parse copied Data! IndexError! {err}")
            QMessageBox.critical(
                self,
                "Fehler!",
                "Daten konnten nicht importiert werden!\n\nEs müssen pro Zeile genau zwei Zahlen stehen, die durch die 'Tab' Taste getrennt werden!",
                buttons=QMessageBox.StandardButton.Ok,
                defaultButton=QMessageBox.StandardButton.Ok,
            )
        except ValueError as err:
            self.logger.exception(f"Could not parse copied Data! ValueError! {err}")
            error_word = str(err).splitlines(True)[0][
                len("could not convert string to float: '"): -1
            ]
            QMessageBox.critical(
                self,
                "Fehler!",
                f"Daten konnten nicht importiert werden!\n\nEs wurde eine Nicht-Zahl gefunden: {error_word}\nBitte den Fehler beheben und erneut versuchen!",
                buttons=QMessageBox.StandardButton.Ok,
                defaultButton=QMessageBox.StandardButton.Ok,
            )

    def reject(self):
        super().reject()


class GifWidget(QWidget):
    def __init__(self, gif_path: str, parent=None):
        super().__init__(parent)

        # QLabel to show the GIF
        self.label = QLabel(parent=self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setScaledContents(True)

        # Load the animated GIF
        self.movie = QMovie(gif_path)
        self.movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self.movie.setSpeed(100)  # 100% speed
        self.movie.loopCount = -1  # Loop indefinitely
        self.movie.setScaledSize(QSize(343, 913))

        # Attach movie to label
        self.label.setMovie(self.movie)

        # Start animation
        self.movie.start()

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

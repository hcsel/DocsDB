from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.config import get_documents_root, set_documents_root


class SettingsDialog(QDialog):
    """
    Настройки приложения.

    Сейчас здесь находится только корневая папка
    с документами.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Настройки")
        self.setMinimumWidth(650)

        self._build_ui()
        self._load_settings()

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self):

        layout = QVBoxLayout(self)

        title = QLabel(
            "<b>Папка с документами</b>"
        )

        description = QLabel(
            "Укажите корневую папку «БД Документов».\n"
            "Пути к файлам в базе будут храниться "
            "относительно этой папки."
        )

        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)

        # ----------------------------------------------------
        # Поле пути
        # ----------------------------------------------------

        path_layout = QHBoxLayout()

        self.path_edit = QLineEdit()

        self.browse_button = QPushButton(
            "Выбрать..."
        )

        self.browse_button.clicked.connect(
            self._choose_folder
        )

        path_layout.addWidget(
            self.path_edit,
            1,
        )

        path_layout.addWidget(
            self.browse_button
        )

        layout.addLayout(path_layout)

        # ----------------------------------------------------
        # Пример
        # ----------------------------------------------------

        self.example_label = QLabel()

        self.example_label.setWordWrap(True)

        layout.addWidget(
            self.example_label
        )

        # ----------------------------------------------------
        # Кнопки
        # ----------------------------------------------------

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(
            self._save
        )

        buttons.rejected.connect(
            self.reject
        )

        layout.addWidget(buttons)

    # ========================================================
    # Загрузка
    # ========================================================

    def _load_settings(self):

        root = get_documents_root()

        if root:
            self.path_edit.setText(
                str(root)
            )

        self._update_example()

        self.path_edit.textChanged.connect(
            self._update_example
        )

    # ========================================================
    # Выбор папки
    # ========================================================

    def _choose_folder(self):

        current = self.path_edit.text().strip()

        if current and Path(current).exists():
            start_dir = current
        else:
            start_dir = str(Path.home())

        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку «БД Документов»",
            start_dir,
        )

        if folder:
            self.path_edit.setText(folder)

    # ========================================================
    # Пример
    # ========================================================

    def _update_example(self):

        root = self.path_edit.text().strip()

        if not root:
            self.example_label.setText(
                "Корневая папка пока не выбрана."
            )
            return

        self.example_label.setText(
            "Например, если в базе записано:\n"
            "<code>Приказы\\2024\\Приказ №123.pdf</code>\n\n"
            f"полный путь будет:\n"
            f"<code>{root}\\Приказы\\2024\\Приказ №123.pdf</code>"
        )

    # ========================================================
    # Сохранение
    # ========================================================

    def _save(self):

        value = self.path_edit.text().strip()

        if not value:

            QMessageBox.warning(
                self,
                "Не указана папка",
                "Выберите корневую папку "
                "с документами.",
            )

            return

        path = Path(value)

        if not path.exists():

            answer = QMessageBox.question(
                self,
                "Папка не существует",
                (
                    "Указанная папка не существует:\n\n"
                    f"{path}\n\n"
                    "Всё равно сохранить этот путь?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                return

        if not path.is_dir():

            QMessageBox.warning(
                self,
                "Ошибка",
                "Указанный путь не является папкой.",
            )

            return

        set_documents_root(path)

        self.accept()
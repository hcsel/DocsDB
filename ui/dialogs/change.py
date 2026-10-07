from pathlib import Path
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QTextEdit,
)

from app import db, files
from app.models import Document



class DocumentDialog(QDialog):
    """
    Окно добавления / редактирования документа.
    """

    def __init__(
        self,
        parent=None,
        document: Document | None = None,
    ):
        super().__init__(parent)

        self.document = document

        if document:
            self.setWindowTitle("Редактирование документа")
        else:
            self.setWindowTitle("Добавление документа")

        self.resize(650, 520)

        self._build_ui()
        self._load_document(document)

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)

        form = QFormLayout()

        form.setFieldGrowthPolicy(
            QFormLayout.AllNonFixedFieldsGrow
        )

        # Название

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(
            "Название документа"
        )

        form.addRow(
            "Название*:",
            self.title_edit,
        )

        # Дата

        self.date_edit = QDateEdit()

        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat(
            "dd.MM.yyyy"
        )

        self.date_edit.setMinimumDate(
            QDate(1900, 1, 1)
        )

        self.date_edit.setDate(
            QDate(1900, 1, 1)
        )

        form.addRow(
            "Дата:",
            self.date_edit,
        )

        # Номер

        self.number_edit = QLineEdit()

        form.addRow(
            "№ документа:",
            self.number_edit,
        )

        # Раздел

        self.sheet_edit = QLineEdit()

        form.addRow(
            "Раздел:",
            self.sheet_edit,
        )

        # Категория

        self.category_edit = QLineEdit()

        form.addRow(
            "Категория:",
            self.category_edit,
        )

        # Тип

        self.type_edit = QLineEdit()

        form.addRow(
            "Тип:",
            self.type_edit,
        )

        # Изменения

        self.changes_edit = QLineEdit()

        form.addRow(
            "Изменения:",
            self.changes_edit,
        )

        # Примечания

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(100)

        form.addRow(
            "Примечания:",
            self.notes_edit,
        )

        # Файл

        file_row = QHBoxLayout()

        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)
        self.file_edit.setPlaceholderText(
            "Файл не выбран"
        )

        file_row.addWidget(
            self.file_edit,
            1,
        )

        self.browse_button = QPushButton(
            "Выбрать…"
        )

        self.browse_button.clicked.connect(
            self._choose_file
        )

        file_row.addWidget(
            self.browse_button
        )

        form.addRow(
            "Файл:",
            file_row,
        )

        root.addLayout(form)

        # Кнопки

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(
            self._validate_and_accept
        )

        buttons.rejected.connect(
            self.reject
        )

        root.addWidget(buttons)

    # ---------------------------------------------------------
    # Загрузка существующего документа
    # ---------------------------------------------------------

    def _load_document(
        self,
        document: Document | None,
    ):
        if not document:
            return

        self.title_edit.setText(
            document.title
        )

        self.number_edit.setText(
            document.doc_number
        )

        self.sheet_edit.setText(
            document.sheet
        )

        self.category_edit.setText(
            document.category
        )

        self.type_edit.setText(
            document.doc_type
        )

        self.changes_edit.setText(
            document.changes
        )

        self.notes_edit.setPlainText(
            document.notes
        )

        if document.doc_date:

            date = QDate.fromString(
                document.doc_date,
                "yyyy-MM-dd",
            )

            if date.isValid():
                self.date_edit.setDate(date)

        path = files.resolve_file(
            document.file_path,
            document.file_name,
        )

        if path:
            self.file_edit.setText(
                str(path)
            )

        elif document.file_path:
            self.file_edit.setText(
                document.file_path
            )

        elif document.file_name:
            self.file_edit.setText(
                document.file_name
            )

    # ---------------------------------------------------------
    # Выбор файла
    # ---------------------------------------------------------

    def _choose_file(self):

        current = self.file_edit.text().strip()

        if current:

            current_path = Path(current)

            if current_path.parent.exists():
                start_dir = str(
                    current_path.parent
                )
            else:
                start_dir = ""

        else:
            start_dir = ""

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите документ",
            start_dir,
            "Все файлы (*.*)",
        )

        if not path:
            return

        self.file_edit.setText(path)

        # Если название ещё пустое —
        # автоматически берём имя файла без расширения.

        if not self.title_edit.text().strip():

            self.title_edit.setText(
                Path(path).stem
            )

    # ---------------------------------------------------------
    # Проверка
    # ---------------------------------------------------------

    def _validate_and_accept(self):

        title = self.title_edit.text().strip()

        if not title:

            QMessageBox.warning(
                self,
                "Проверка",
                "Введите название документа.",
            )

            self.title_edit.setFocus()

            return

        path_text = self.file_edit.text().strip()

        if not path_text:

            QMessageBox.warning(
                self,
                "Проверка",
                "Выберите файл документа.",
            )

            return

        path = Path(path_text)

        if not path.is_file():

            QMessageBox.warning(
                self,
                "Файл не найден",
                f"Указанный файл не существует:\n{path}",
            )

            return

        exclude_id = (
            self.document.id
            if self.document
            else None
        )

        if db.exists_by_file(
            str(path),
            exclude_id=exclude_id,
        ):

            QMessageBox.warning(
                self,
                "Дубликат",
                "Этот файл уже есть в базе документов.",
            )

            return

        self.accept()

    # ---------------------------------------------------------
    # Получение модели
    # ---------------------------------------------------------

    def get_document(self) -> Document:

        date_value = None

        date = self.date_edit.date()

        if date != QDate(1900, 1, 1):

            date_value = date.toString(
                "yyyy-MM-dd"
            )

        path = Path(
            self.file_edit.text().strip()
        )

        return Document(

            id=(
                self.document.id
                if self.document
                else None
            ),

            sheet=self.sheet_edit.text().strip(),

            category=self.category_edit.text().strip(),

            doc_type=self.type_edit.text().strip(),

            doc_date=date_value,

            doc_number=self.number_edit.text().strip(),

            title=self.title_edit.text().strip(),

            changes=self.changes_edit.text().strip(),

            notes=self.notes_edit.toPlainText().strip(),

            # НОВЫЙ ФОРМАТ:
            # полный путь к физическому файлу
            file_path=str(path),

            file_name=path.name,

            raw_link=(
                self.document.raw_link
                if self.document
                else ""
            ),

            link_kind="filename",

            needs_review=False,

            review_reason="",
        )


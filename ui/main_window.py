from pathlib import Path

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QAction,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QTableView,
    QStatusBar,
    QPushButton,
    QMessageBox,
    QMenu,
    QHeaderView,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QDateEdit,
    QTextEdit,
    QFileDialog,
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


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Справочник документов"
        )
        screen = self.screen().availableGeometry()
        self.resize(
            min(1600, screen.width() - 100),
            min(1000, screen.height() - 100),
        )
        self.setMinimumSize(800, 500)
        self._current_docs: list[Document] = []

        self._build_ui()

        self._reload_filters()

        self._refresh()

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        root = QVBoxLayout(
            central
        )

        # -----------------------------------------------------
        # Поиск / фильтры
        # -----------------------------------------------------

        top = QHBoxLayout()

        self.search_edit = QLineEdit()

        self.search_edit.setPlaceholderText(
            "Поиск..."
        )

        self.search_edit.textChanged.connect(
            self._refresh
        )

        top.addWidget(
            self.search_edit,
            stretch=1,
        )

        self.category_combo = QComboBox()

        self.category_combo.currentIndexChanged.connect(
            self._refresh
        )

        top.addWidget(
            self.category_combo
        )

        self.type_combo = QComboBox()

        self.type_combo.currentIndexChanged.connect(
            self._refresh
        )

        top.addWidget(
            self.type_combo
        )

        self.sheet_combo = QComboBox()

        self.sheet_combo.currentIndexChanged.connect(
            self._refresh
        )

        top.addWidget(
            self.sheet_combo
        )

        btn_reset = QPushButton(
            "Сбросить фильтры"
        )

        btn_reset.clicked.connect(
            self._reset_filters
        )

        top.addWidget(
            btn_reset
        )

        # НОВАЯ КНОПКА

        btn_add = QPushButton(
            "+ Добавить файл"
        )

        btn_add.clicked.connect(
            self._add_document
        )

        top.addWidget(
            btn_add
        )

        root.addLayout(top)

        # -----------------------------------------------------
        # Таблица
        # -----------------------------------------------------

        self.model = QStandardItemModel()

        self.model.setHorizontalHeaderLabels(
            [
                "ID",
                "Раздел",
                "Категория",
                "Тип",
                "Дата",
                "№",
                "Название",
                "Файл",
            ]
        )

        self.table = QTableView()
#настройка по ширине при изменении окна
        self.table.setWordWrap(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.table.setModel(
            self.model
        )

        self.table.setSelectionBehavior(
            QTableView.SelectRows
        )

        self.table.setSelectionMode(
            QTableView.SingleSelection
        )

        self.table.setEditTriggers(
            QTableView.NoEditTriggers
        )

        self.table.setAlternatingRowColors(
            True
        )

        self.table.setSortingEnabled(
            True
        )

        self.table.doubleClicked.connect(
            self._open_selected
        )

        self.table.setContextMenuPolicy(
            Qt.CustomContextMenu
        )

        self.table.customContextMenuRequested.connect(
            self._show_context_menu
        )

        header = self.table.horizontalHeader()

        # Все колонки тянутся пропорционально окну,
        # но с разными весами — название и файл получают больше места.
        for i in range(self.model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Interactive)

        header.setSectionResizeMode(6, QHeaderView.Stretch)

        # ID, Дата, № — узкие
        header.resizeSection(0, 60)  # ID
        header.resizeSection(4, 100)  # Дата
        header.resizeSection(5, 80)  # №

        # Название — самое широкое
        header.resizeSection(6, 400)  # Название

        # Остальные — средние
        header.resizeSection(1, 120)  # Раздел
        header.resizeSection(2, 140)  # Категория
        header.resizeSection(3, 120)  # Тип
        header.resizeSection(7, 100)  # Файл

        root.addWidget(
            self.table,
            stretch=1,
        )

        # -----------------------------------------------------
        # Status bar
        # -----------------------------------------------------

        self.status = QStatusBar()

        self.setStatusBar(
            self.status
        )

    # =========================================================
    # Данные
    # =========================================================

    def _reload_filters(self):

        for combo, values in [

            (
                self.category_combo,
                db.distinct_values(
                    "category"
                ),
            ),

            (
                self.type_combo,
                db.distinct_values(
                    "doc_type"
                ),
            ),

            (
                self.sheet_combo,
                db.distinct_values(
                    "sheet"
                ),
            ),
        ]:

            combo.blockSignals(
                True
            )

            combo.clear()

            combo.addItem(
                "— все —",
                "",
            )

            for value in values:

                combo.addItem(
                    value,
                    value,
                )

            combo.blockSignals(
                False
            )

    def _current_filter(
        self,
        combo,
    ):

        return (
            combo.currentData()
            or ""
        )

    def _refresh(self):

        docs = db.search(

            query=self.search_edit.text().strip(),

            category=self._current_filter(
                self.category_combo
            ),

            doc_type=self._current_filter(
                self.type_combo
            ),

            sheet=self._current_filter(
                self.sheet_combo
            ),
        )

        self._current_docs = docs

        self._fill_table(
            docs
        )

        c = db.counts()

        self.status.showMessage(

            f"Показано: {len(docs)} | "
            f"Всего: {c['total']} | "
            f"Требуют проверки: {c['needs_review']} | "
            f"С файлом: {c['with_file']}"
        )

    def _fill_table(
        self,
        docs: list[Document],
    ):

        self.model.removeRows(
            0,
            self.model.rowCount(),
        )

        for d in docs:

            path = files.resolve_file(
                d.file_path,
                d.file_name,
            )

            if path:
                file_marker = "есть"

            elif d.file_path or d.file_name:
                file_marker = "ссылка"

            else:
                file_marker = ""

            row = [

                QStandardItem(
                    str(d.id)
                ),

                QStandardItem(
                    d.sheet
                ),

                QStandardItem(
                    d.category
                ),

                QStandardItem(
                    d.doc_type
                ),

                QStandardItem(
                    d.doc_date or ""
                ),

                QStandardItem(
                    d.doc_number
                ),

                QStandardItem(
                    d.title
                ),

                QStandardItem(
                    file_marker
                ),
            ]

            # Очень важно:
            # ID хранится непосредственно в строке.

            for item in row:

                item.setData(
                    d.id,
                    Qt.UserRole,
                )

            if d.needs_review:

                for item in row:
                    item.setBackground(
                        Qt.yellow
                    )

            self.model.appendRow(
                row
            )

    def _reset_filters(self):

        self.search_edit.clear()

        self.category_combo.setCurrentIndex(
            0
        )

        self.type_combo.setCurrentIndex(
            0
        )

        self.sheet_combo.setCurrentIndex(
            0
        )

    # =========================================================
    # Получение выбранного документа
    # =========================================================

    def _selected_doc(
        self,
    ) -> Document | None:

        idx = self.table.currentIndex()

        if not idx.isValid():
            return None

        doc_id = idx.data(
            Qt.UserRole
        )

        if doc_id is None:
            return None

        return db.get(
            int(doc_id)
        )

    # =========================================================
    # CREATE
    # =========================================================

    def _add_document(self):

        dialog = DocumentDialog(
            self
        )

        if dialog.exec() != QDialog.Accepted:
            return

        document = dialog.get_document()

        new_id = db.insert(
            document
        )

        self._reload_filters()

        self._refresh()

        self.status.showMessage(
            f"Документ добавлен (ID {new_id})",
            4000,
        )

    # =========================================================
    # UPDATE
    # =========================================================

    def _edit_selected(self):

        document = self._selected_doc()

        if not document:
            return

        dialog = DocumentDialog(
            self,
            document,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        updated = dialog.get_document()

        db.update(
            updated
        )

        self._reload_filters()

        self._refresh()

        self.status.showMessage(
            "Документ сохранён",
            4000,
        )

    # =========================================================
    # DELETE
    # =========================================================

    def _delete_selected(self):

        document = self._selected_doc()

        if not document:
            return

        answer = QMessageBox.question(

            self,

            "Удалить запись?",

            (
                f"Удалить из базы запись:\n\n"
                f"{document.title}\n\n"
                "Физический файл на диске "
                "удалён НЕ будет."
            ),

            QMessageBox.Yes
            | QMessageBox.No,

            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        db.delete(
            document.id
        )

        self._reload_filters()

        self._refresh()

        self.status.showMessage(
            "Запись удалена из базы",
            4000,
        )

    # =========================================================
    # FILE
    # =========================================================

    def _open_selected(self):

        document = self._selected_doc()

        if not document:
            return

        path = files.resolve_file(

            document.file_path,

            document.file_name,
        )

        if not path:

            QMessageBox.warning(

                self,

                "Файл не найден",

                (
                    "Не удалось найти файл:\n"
                    f"{document.file_path or document.file_name or '(нет ссылки)'}"
                ),
            )

            return

        if not files.open_file(path):

            QMessageBox.warning(

                self,

                "Ошибка",

                f"Не удалось открыть:\n{path}",
            )

    def _open_folder(self):

        document = self._selected_doc()

        if not document:
            return

        path = files.resolve_file(

            document.file_path,

            document.file_name,
        )

        if not path:

            QMessageBox.warning(

                self,

                "Файл не найден",

                "Нечего показывать.",
            )

            return

        if not files.open_folder_and_select(
            path
        ):

            QMessageBox.warning(

                self,

                "Ошибка",

                f"Не удалось открыть расположение:\n{path}",
            )

    def _copy_path(self):

        document = self._selected_doc()

        if not document:
            return

        from PySide6.QtWidgets import QApplication

        path = files.resolve_file(

            document.file_path,

            document.file_name,
        )

        value = (
            str(path)
            if path
            else (
                document.file_path
                or document.file_name
                or ""
            )
        )

        QApplication.clipboard().setText(
            value
        )

        self.status.showMessage(
            f"Скопировано: {value}",
            3000,
        )

    # =========================================================
    # CONTEXT MENU
    # =========================================================

    def _show_context_menu(
        self,
        pos,
    ):

        idx = self.table.indexAt(
            pos
        )

        if idx.isValid():

            self.table.selectRow(
                idx.row()
            )

        document = self._selected_doc()

        if not document:
            return

        menu = QMenu(
            self
        )

        a_open = QAction(
            "Открыть документ",
            self,
        )

        a_folder = QAction(
            "Показать в папке",
            self,
        )

        a_edit = QAction(
            "Редактировать",
            self,
        )

        a_copy = QAction(
            "Скопировать путь",
            self,
        )

        a_delete = QAction(
            "Удалить из базы",
            self,
        )

        a_open.triggered.connect(
            self._open_selected
        )

        a_folder.triggered.connect(
            self._open_folder
        )

        a_edit.triggered.connect(
            self._edit_selected
        )

        a_copy.triggered.connect(
            self._copy_path
        )

        a_delete.triggered.connect(
            self._delete_selected
        )

        menu.addAction(
            a_open
        )

        menu.addAction(
            a_folder
        )

        menu.addSeparator()

        menu.addAction(
            a_edit
        )

        menu.addAction(
            a_copy
        )

        menu.addSeparator()

        menu.addAction(
            a_delete
        )

        menu.exec(
            self.table.viewport().mapToGlobal(
                pos
            )
        )
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QAction,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTableView,
    QStatusBar,
    QMessageBox,
    QMenu,
    QHeaderView,
    QDialog,
)

from app import db, files
from app.models import Document
from ui.dialogs.settings import SettingsDialog
from ui.dialogs.change import DocumentDialog
from ui.parts.filter import FilterBar

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
        self.setMinimumSize(800, 600)
        self._current_docs: list[Document] = []
        self._build_ui()
        self.filters.reload_filters()
        self._refresh()

    # ==========UI
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        #верхняя панель filter
        self.filters = FilterBar()
        self.filters.changed.connect(self._refresh)
        self.filters.addRequested.connect(self._add_document)
        self.filters.settingsRequested.connect(self._open_settings)

        root.addWidget(self.filters)

        # Таблица

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
        # настройка по ширине при изменении окна
        self.table.setWordWrap(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setEditTriggers(QTableView.NoEditTriggers)

        self.table.doubleClicked.connect(self._open_selected)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)

        self.table.customContextMenuRequested.connect(self._show_context_menu)

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

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)







    # =========================================================
    # Данные
    # =========================================================

    # обновление
    def _refresh(self):

        docs = db.search(
            query=self.filters.query(),
            category=self.filters.category(),
            doc_type=self.filters.doc_type(),
            sheet=self.filters.sheet(),
        )

        self._current_docs = docs
        self._fill_table(docs)

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

        self.filters.reload_filters()

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

        self.filters.reload_filters()

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

        self.filters.reload_filters()

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

    def _open_settings(self):
        dialog = SettingsDialog(self)

        if dialog.exec():
            # Если корневая папка изменилась,
            # можно обновить интерфейс.
            self._refresh()

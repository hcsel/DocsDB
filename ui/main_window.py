# ui/main_window.py
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QComboBox, QTableView, QLabel, QStatusBar, QPushButton,
    QMessageBox, QMenu, QHeaderView, QSplitter,
)

from app import db, files
from app.models import Document


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Справочник документов УИИ")
        self.resize(1200, 700)

        self._current_docs: list[Document] = []

        self._build_ui()
        self._reload_filters()
        self._refresh()

    # ---------- UI ----------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)

        # --- строка поиска и фильтров ---
        top = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по названию, изменениям, пометкам...")
        self.search_edit.textChanged.connect(self._refresh)
        top.addWidget(self.search_edit, stretch=1)

        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self._refresh)
        top.addWidget(self.category_combo)

        self.type_combo = QComboBox()
        self.type_combo.currentIndexChanged.connect(self._refresh)
        top.addWidget(self.type_combo)

        self.sheet_combo = QComboBox()
        self.sheet_combo.currentIndexChanged.connect(self._refresh)
        top.addWidget(self.sheet_combo)

        btn_reset = QPushButton("Сброс")
        btn_reset.clicked.connect(self._reset_filters)
        top.addWidget(btn_reset)

        root.addLayout(top)

        # --- таблица ---
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(
            ["ID", "Раздел", "Категория", "Тип", "Дата", "№", "Название", "Файл"]
        )

        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setEditTriggers(QTableView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self._open_selected)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # название растягиваем
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)

        root.addWidget(self.table, stretch=1)

        # --- статус-бар ---
        self.status = QStatusBar()
        self.setStatusBar(self.status)

    # ---------- данные ----------

    def _reload_filters(self):
        for combo, values in [
            (self.category_combo, db.distinct_values("category")),
            (self.type_combo, db.distinct_values("doc_type")),
            (self.sheet_combo, db.distinct_values("sheet")),
        ]:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("— все —", "")
            for v in values:
                combo.addItem(v, v)
            combo.blockSignals(False)

    def _current_filter(self, combo):
        return combo.currentData() or ""

    def _refresh(self):
        query = self.search_edit.text().strip()
        docs = db.search(
            query=query,
            category=self._current_filter(self.category_combo),
            doc_type=self._current_filter(self.type_combo),
            sheet=self._current_filter(self.sheet_combo),
        )
        self._current_docs = docs
        self._fill_table(docs)

        c = db.counts()
        self.status.showMessage(
            f"Показано: {len(docs)} | Всего: {c['total']} | "
            f"Требуют проверки: {c['needs_review']} | С файлом: {c['with_file']}"
        )

    def _fill_table(self, docs: list[Document]):
        self.model.removeRows(0, self.model.rowCount())
        for d in docs:
            file_marker = ""
            if d.file_path or d.file_name:
                resolved = files.resolve_file(d.file_path, d.file_name)
                file_marker = "✓" if resolved else "✗ не найден"
            row = [
                QStandardItem(str(d.id)),
                QStandardItem(d.sheet),
                QStandardItem(d.category),
                QStandardItem(d.doc_type),
                QStandardItem(d.doc_date or ""),
                QStandardItem(d.doc_number),
                QStandardItem(d.title),
                QStandardItem(file_marker),
            ]
            if d.needs_review:
                for it in row:
                    it.setBackground(Qt.yellow)
            self.model.appendRow(row)

    def _reset_filters(self):
        self.search_edit.clear()
        self.category_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.sheet_combo.setCurrentIndex(0)

    # ---------- действия ----------

    def _selected_doc(self) -> Document | None:
        idx = self.table.currentIndex()
        if not idx.isValid():
            return None
        row = idx.row()
        if row >= len(self._current_docs):
            return None
        return self._current_docs[row]

    def _open_selected(self):
        d = self._selected_doc()
        if not d:
            return
        path = files.resolve_file(d.file_path, d.file_name)
        if not path:
            QMessageBox.warning(
                self, "Файл не найден",
                f"Не удалось найти файл:\n{d.file_path or d.file_name or '(нет ссылки)'}\n\n"
                f"Проверьте базовую папку и имя файла.",
            )
            return
        if not files.open_file(path):
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть:\n{path}")

    def _open_folder(self):
        d = self._selected_doc()
        if not d:
            return
        path = files.resolve_file(d.file_path, d.file_name)
        if not path:
            QMessageBox.warning(self, "Файл не найден", "Нечего показывать.")
            return
        files.open_folder_and_select(path)

    def _copy_path(self):
        d = self._selected_doc()
        if not d:
            return
        from PySide6.QtWidgets import QApplication
        path = files.resolve_file(d.file_path, d.file_name) or (d.file_path or "")
        QApplication.clipboard().setText(str(path))
        self.status.showMessage(f"Скопировано: {path}", 3000)

    def _show_context_menu(self, pos):
        d = self._selected_doc()
        if not d:
            return
        menu = QMenu(self)
        a_open   = QAction("Открыть документ", self)
        a_folder = QAction("Показать в папке", self)
        a_copy   = QAction("Скопировать путь", self)
        a_open.triggered.connect(self._open_selected)
        a_folder.triggered.connect(self._open_folder)
        a_copy.triggered.connect(self._copy_path)
        menu.addAction(a_open)
        menu.addAction(a_folder)
        menu.addSeparator()
        menu.addAction(a_copy)
        menu.exec(self.table.viewport().mapToGlobal(pos))
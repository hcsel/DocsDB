from pathlib import Path

from PySide6.QtCore import Signal

from PySide6.QtWidgets import (

    QWidget,

    QHBoxLayout,
    QLineEdit,
    QComboBox,

    QPushButton,

)

from app import db


class FilterBar(QWidget):
    changed = Signal()  # сигнал на изменение фильтра
    addRequested = Signal()
    settingsRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ========== UI
    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # строка поиска
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск...")

        self.search_edit.textChanged.connect(self.changed)
        layout.addWidget(self.search_edit, stretch=1)

        # категория
        self.category_combo = QComboBox()
        self.category_combo.currentIndexChanged.connect(self.changed)
        layout.addWidget(self.category_combo)

        # тип
        self.type_combo = QComboBox()
        self.type_combo.currentIndexChanged.connect(self.changed)

        layout.addWidget(self.type_combo)

        # раздел
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentIndexChanged.connect(self.changed)
        layout.addWidget(self.sheet_combo)

        #сброс
        btn_reset = QPushButton("Сбросить фильтры")
        btn_reset.clicked.connect(self.reset)
        layout.addWidget(btn_reset)

        # добавить
        btn_add = QPushButton("+ Добавить файл")
        btn_add.clicked.connect(self.addRequested)
        layout.addWidget(btn_add)

        # Настройки
        self.settings_button = QPushButton("Настройки")
        self.settings_button.clicked.connect(self.settingsRequested)
        layout.addWidget(self.settings_button)


# =============== заполнение выпадающих списков
    def reload_filters(self):
        """
        Перечитывает список значений из БД и обновляет combobox'ы.
        Сигналы блокируются, чтобы не дёргать changed лишний раз.
        """
        for combo, values in (
            (self.category_combo, db.distinct_values("category")),
            (self.type_combo, db.distinct_values("doc_type")),
            (self.sheet_combo, db.distinct_values("sheet")),
        ):
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("— все —", "")
            for value in values:
                combo.addItem(value, value)
            combo.blockSignals(False)

# ============== сброс

    def reset(self):
        """Сбрасывает все фильтры и уведомляет об этом один раз."""
        widgets = (
            self.search_edit,
            self.category_combo,
            self.type_combo,
            self.sheet_combo,
        )

        for w in widgets:
            w.blockSignals(True)

        self.search_edit.clear()
        self.category_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.sheet_combo.setCurrentIndex(0)

        for w in widgets:
            w.blockSignals(False)

        self.changed.emit()

        # Геттеры текущих значений

    def query(self) -> str:
            return self.search_edit.text().strip()

    def category(self) -> str:
            return self.category_combo.currentData() or ""

    def doc_type(self) -> str:
            return self.type_combo.currentData() or ""

    def sheet(self) -> str:
            return self.sheet_combo.currentData() or ""
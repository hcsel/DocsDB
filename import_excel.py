import sqlite3
from pathlib import Path
import openpyxl
from datetime import datetime

# Настройки импорта
PROJECT_DIR = Path(__file__).resolve().parent
EXCEL_FILE = PROJECT_DIR / "на замену Программа документы.xlsx"
DB_FILE = PROJECT_DIR / "docs.db"

# Название листа в Excel
SHEET_NAME = "обзор"
# Очищать ли старые записи этого листа перед импортом?
# True - удалит все старые записи этого листа и запишет новые
# False - будет добавлять только новые, пропуская дубликаты
CLEAR_BEFORE_IMPORT = False

# Если колонка не нужна не указывать её или пустая строка.
COLUMNS = {
    "category": "B",  # Категория, по виду наказания
    "doc_type": "D",  # Тип документа, вид
    "doc_date": "E",  # Дата
    "doc_number": "F",  # Номер
    "title": "G",  # Название
    "file_path": "H",  # Путь к файлу
    "changes": "I",  # Изменения
    "notes": "J",  # Примечания
}


# Все что ниже не трогать
def col_letter_to_index(letter: str) -> int:
    if not letter:
        return -1
    letter = letter.upper()
    result = 0
    for char in letter:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1


def clean(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()

# Дата
def format_date(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")


    val_str = clean(value)
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            dt = datetime.strptime(val_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return val_str


def normalize_path(value) -> str:
    """Чистит путь и отрезает всё до корневой папки 'БД документов'."""
    value = clean(value)
    if not value or value.isdigit():
        return ""

    value = value.strip('"')

    # Приводим все слэши к одному виду для удобства поиска
    val_normalized = value.replace("/", "\\")

    # Ищем нашу корневую папку в пути
    marker = "БД документов\\"
    marker_lower = "бд документов\\"

    # Ищем маркер без учета регистра
    if marker_lower in val_normalized.lower():
        # Разделяем строку по маркеру и берём то, что после него
        # split(..., 1) значит, что делим только один раз
        idx = val_normalized.lower().find(marker_lower)
        if idx != -1:
            relative_path = val_normalized[idx + len(marker_lower):]
            return relative_path

    # Если корневой папки в пути нет (например, файл лежит вне неё),
    # возвращаем как есть (или можно вернуть пустую строку, если хотите такие отсеивать)
    return value


def get_file_name(file_path: str) -> str:
    if not file_path:
        return ""
    normalized = file_path.replace("\\", "/")
    return normalized.rstrip("/").split("/")[-1]


# ==========
def run_import():
    if not EXCEL_FILE.exists():
        raise FileNotFoundError(f"Не найден Excel-файл:\n{EXCEL_FILE}")
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Не найдена база данных:\n{DB_FILE}")

    print(f"Импорт листа: '{SHEET_NAME}'")
    print(f"Очистка старых записей: {'ДА' if CLEAR_BEFORE_IMPORT else 'НЕТ'}")

    workbook = openpyxl.load_workbook(EXCEL_FILE, data_only=True, read_only=True)

    if SHEET_NAME not in workbook.sheetnames:
        raise ValueError(f"Лист '{SHEET_NAME}' не найден!\nДоступные: {workbook.sheetnames}")

    sheet = workbook[SHEET_NAME]
    connection = sqlite3.connect(DB_FILE)

    # Подготавливаем индексы колонок
    idx_map = {key: col_letter_to_index(val) for key, val in COLUMNS.items()}

    try:
        cursor = connection.cursor()

        if CLEAR_BEFORE_IMPORT:
            cursor.execute("DELETE FROM documents WHERE sheet = ?", (SHEET_NAME,))
            print("Старые записи листа удалены.")

        imported = 0
        skipped = 0
        duplicates = 0

        # Идём по строкам начиная со 2-й
        for row_number, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):

            # Функция для безопасного доставания значения по ключу
            def get_val(key):
                idx = idx_map.get(key, -1)
                if idx == -1 or len(row) <= idx:
                    return ""
                return row[idx]

            # Извлекаем данные
            category = clean(get_val("category"))
            doc_type = clean(get_val("doc_type"))
            doc_date = format_date(get_val("doc_date"))
            doc_number = clean(get_val("doc_number"))
            title = clean(get_val("title"))
            file_path = normalize_path(get_val("file_path"))
            changes = clean(get_val("changes"))
            notes = clean(get_val("notes"))

            # Пропускаем пустые строки или строки без названия
            if not any([category, doc_type, doc_date, doc_number, title, file_path, changes, notes]):
                skipped += 1
                continue
            if not title:
                skipped += 1
                continue

            # Проверка на дубликаты (если не включена очистка)
            if not CLEAR_BEFORE_IMPORT:
                cursor.execute("""
                    SELECT id FROM documents 
                    WHERE sheet = ? AND title = ? AND doc_date = ? AND doc_number = ?
                    LIMIT 1
                """, (SHEET_NAME, title, doc_date, doc_number))
                if cursor.fetchone():
                    duplicates += 1
                    continue

            file_name = get_file_name(file_path)
            link_kind = "filename" if file_path else "empty"

            # Вставка
            cursor.execute("""
                INSERT INTO documents (
                    sheet, category, doc_type, doc_date, doc_number, title,
                    changes, notes, file_path, file_name, raw_link, link_kind,
                    needs_review, review_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                SHEET_NAME, category, doc_type, doc_date, doc_number, title,
                changes, notes, file_path, file_name, file_path, link_kind,
                0, ""
            ))

            imported += 1
            print(f"[{imported}] {title[:50]}...")  # Выводим первые 50 символов названия

        connection.commit()

        print("\n" + "=" * 50)
        print("ИМПОРТ ЗАВЕРШЁН")
        print("=" * 50)
        print(f"Добавлено:   {imported}")
        print(f"Дубликатов:  {duplicates}")
        print(f"Пропущено:   {skipped}")

    except Exception as e:
        connection.rollback()
        print(f"\nОШИБКА: {e}")
        raise
    finally:
        connection.close()
        workbook.close()


if __name__ == "__main__":
    run_import()
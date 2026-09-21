from pathlib import Path

# Где лежит БД
APP_DIR = Path(__file__).resolve().parent.parent
DB_PATH = APP_DIR / "docs.db"

# Базовые папки, где лежат документы.
# Программа будет искать файл по имени во всех этих папках по очереди.
BASE_FOLDERS = [
    Path(r"\\10.39.0.14\xxx$\УИИ (не удалять)\БД Документов"),
    # Path(r"\\10.39.0.14\xxx$\УИИ (не удалять)\БД  Документов"),
]

# Что открывать файлы через системный обработчик (Word, PDF и т.п.)
OPEN_VIA_OS = True
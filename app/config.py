from pathlib import Path
import json


# ============================================================
# Папки приложения
# ============================================================

APP_DIR = Path(__file__).resolve().parent.parent

DB_PATH = APP_DIR / "docs.db"

SETTINGS_PATH = APP_DIR / "settings.json"


# ============================================================
# Настройки по умолчанию
# ============================================================

DEFAULT_SETTINGS = {
    "documents_root": ""
}


# ============================================================
# Работа с настройками
# ============================================================

def load_settings() -> dict:
    """
    Загружает настройки из settings.json.

    Если файла ещё нет или он повреждён —
    возвращаются настройки по умолчанию.
    """

    if not SETTINGS_PATH.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        with SETTINGS_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return DEFAULT_SETTINGS.copy()

        settings = DEFAULT_SETTINGS.copy()
        settings.update(data)

        return settings

    except (OSError, json.JSONDecodeError):
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """
    Сохраняет настройки в settings.json.
    """

    with SETTINGS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            settings,
            file,
            ensure_ascii=False,
            indent=4,
        )


def get_documents_root() -> Path | None:
    """
    Возвращает корневую папку документов.

    Если пользователь ещё не указал её,
    возвращается None.
    """

    settings = load_settings()

    value = settings.get("documents_root", "")

    if not value:
        return None

    path = Path(value)

    return path


def set_documents_root(path: str | Path) -> None:
    """
    Устанавливает корневую папку документов.
    """

    path = Path(path)

    settings = load_settings()

    settings["documents_root"] = str(path)

    save_settings(settings)


# ============================================================
# Старый совместимый интерфейс
# ============================================================

# Некоторые части старого проекта могут импортировать
# DOCUMENTS_ROOT напрямую.
#
# Поэтому оставляем эту переменную для совместимости.
#
# В новом коде лучше использовать get_documents_root().

DOCUMENTS_ROOT = get_documents_root()


# ============================================================
# Открытие файлов
# ============================================================

OPEN_VIA_OS = True
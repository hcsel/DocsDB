from pathlib import Path
import json



# Папки приложения

APP_DIR = Path(__file__).resolve().parent.parent
DB_PATH = APP_DIR / "docs.db"
SETTINGS_PATH = APP_DIR / "settings.json"

# Настройки по умолчанию
DEFAULT_SETTINGS = {"documents_root": ""}

# кэш настроек
_settings_cache: dict | None = None


# Работа с настройками

def load_settings() -> dict:
    """
    Загружает настройки из settings.json.
    читает файл один раз за запуск
    """

    global _settings_cache
    if _settings_cache is not None:
        return _settings_cache

    if not SETTINGS_PATH.exists():
        _settings_cache = DEFAULT_SETTINGS.copy()
        return _settings_cache

    try:
        with SETTINGS_PATH.open("r",encoding="utf-8",) as file:
            data = json.load(file)
        if not isinstance(data, dict):
            data = {}

    except (OSError, json.JSONDecodeError):
        data = {}

    settings = DEFAULT_SETTINGS.copy()
    settings.update(data)
    _settings_cache = settings
    return _settings_cache


def save_settings(settings: dict) -> None:
    """
    Сохраняет настройки в settings.json.
    """
    global _settings_cache
    _settings_cache = settings.copy()
    with SETTINGS_PATH.open("w", encoding="utf-8") as file:
        json.dump(settings, file, ensure_ascii=False, indent=4)


def get_documents_root() -> Path | None:
    """
    Возвращает корневую папку документов.

    Если пользователь ещё не указал её,
    возвращается None.
    """

    value = load_settings().get("documents_root", "")

    if not value:
        return None
    return Path(value)


def set_documents_root(path: str | Path) -> None:
    """
    Устанавливает корневую папку документов.
    """

    settings = load_settings()
    settings["documents_root"] = str(Path(path))
    save_settings(settings)

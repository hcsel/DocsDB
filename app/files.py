# app/files.py
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from app.config import BASE_FOLDERS, OPEN_VIA_OS
# app/files.py
import socket
import time
from pathlib import Path
"""
# кэш доступности сервера
_server_ok = None
_server_checked_at = 0.0
_SERVER_HOST = "10.39.0.14"
_CACHE_TTL = 30.0   # секунд
"""

"""
def server_reachable(timeout: float = 1.0) -> bool:
    "Быстрая проверка доступности сервера с таймаутом."
    global _server_ok, _server_checked_at
    now = time.time()
    if _server_ok is not None and (now - _server_checked_at) < _CACHE_TTL:
        return _server_ok
    try:
        with socket.create_connection((_SERVER_HOST, 445), timeout=timeout):
            _server_ok = True
    except (OSError, socket.timeout):
        _server_ok = False
    _server_checked_at = now
    return _server_ok
"""
"""
def resolve_file(doc_file_path, doc_file_name):
    # если сервер недоступен — сразу возвращаем None, не висим
    #if not server_reachable():
       # return None

    if doc_file_path:
        p = Path(doc_file_path)
        if p.exists():
            return p
    if doc_file_name:
        for folder in BASE_FOLDERS:
            candidate = folder / doc_file_name
            if candidate.exists():
                return candidate
    return None
"""
def resolve_file(doc_file_path: Optional[str], doc_file_name: Optional[str]) -> Optional[Path]:
    if doc_file_path:
        p = Path(doc_file_path)

        # Это уже полный путь к файлу
        if p.is_file():
            return p

        # Это путь к папке
        if p.is_dir() and doc_file_name:
            candidate = p / doc_file_name
            if candidate.is_file():
                return candidate

        # Поиск по базовым папкам
    if doc_file_name:
        for folder in BASE_FOLDERS:
            candidate = Path(folder) / doc_file_name

            if candidate.is_file():
                return candidate

    return None

    """
    Пытается найти файл:
      1) если есть полный путь и он существует — вернуть его
      2) если есть только имя — искать в BASE_FOLDERS по очереди
    Возвращает Path или None.

    if doc_file_path:
        p = Path(doc_file_path)

    if p.is_dir() and doc_file_name:
        for folder in BASE_FOLDERS:
            candidate = folder / doc_file_name
            if candidate.exists():
                return candidate
    return None
    """




def open_file(path: Path) -> bool:
    """Открывает файл системным обработчиком.
    if not path.exists():
        return False

    if OPEN_VIA_OS:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
            return True
        except Exception:
            return False
    return False
    """
    if not path.is_file():
        return False

    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))

        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])

        else:
            subprocess.Popen(["xdg-open", str(path)])

        return True

    except Exception as e:
        print(f"Ошибка открытия файла: {e}")
        return False


def open_folder_and_select(path: Path):
    """Открывает проводник и выделяет файл."""
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer", "/select,", str(path)])
    else:
        open_file(path.parent)
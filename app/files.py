# app/files.py
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from app.config import BASE_FOLDERS, OPEN_VIA_OS


def resolve_file(doc_file_path: Optional[str], doc_file_name: Optional[str]) -> Optional[Path]:
    """
    Пытается найти файл:
      1) если есть полный путь и он существует — вернуть его
      2) если есть только имя — искать в BASE_FOLDERS по очереди
    Возвращает Path или None.
    """
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


def open_file(path: Path) -> bool:
    """Открывает файл системным обработчиком."""
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


def open_folder_and_select(path: Path):
    """Открывает проводник и выделяет файл."""
    if sys.platform.startswith("win"):
        subprocess.Popen(["explorer", "/select,", str(path)])
    else:
        open_file(path.parent)
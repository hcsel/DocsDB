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

def normalize_file_path(path: str | Path) -> Path:
    """Приводит путь к Path."""
    return Path(path).expanduser()

def open_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if not OPEN_VIA_OS:
        return False
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))

        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])

        else:
            subprocess.Popen(["xdg-open", str(path)])

        return True

    except (OSError, subprocess.SubprocessError):
        return False


def open_folder_and_select(path: Path) -> bool:
    """Открывает проводник и выделяет файл."""

    if not path.exists():
        return False

    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(
                ["explorer", "/select,", str(path)]
            )

        elif sys.platform == "darwin":
            subprocess.Popen(
                ["open", "-R", str(path)]
            )

        else:
            subprocess.Popen(
                ["xdg-open", str(path.parent)]
            )

        return True

    except (OSError, subprocess.SubprocessError):
        return False
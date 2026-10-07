import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from app.config import get_documents_root


# ============================================================
# Пути
# ============================================================

def is_absolute_path(path: str | Path) -> bool:
    """
    Проверяет, является ли путь абсолютным.

    Поддерживает Windows-пути и UNC:
        C:\\Documents\\file.pdf
        \\\\server\\folder\\file.pdf
    """

    if not path:
        return False

    value = str(path).strip()

    # Windows drive:
    # C:\...
    if len(value) >= 3:
        if value[1] == ":" and value[2] in ("\\", "/"):
            return True

    # UNC:
    # \\server\...
    if value.startswith("\\\\"):
        return True

    return Path(value).is_absolute()


def normalize_relative_path(path: str | Path) -> str:
    """
    Нормализует относительный путь для хранения в БД.

    В базе используем обратные слэши, как в Windows:

        Приказы\\2024\\Приказ.pdf
    """

    value = str(path).strip()

    value = value.replace("/", "\\")

    while value.startswith(".\\"):
        value = value[2:]

    return value


# ============================================================
# Получение полного пути
# ============================================================

def resolve_file(
    doc_file_path: Optional[str],
    doc_file_name: Optional[str] = None,
) -> Optional[Path]:
    """
    Находит физический файл.

    Поддерживаются несколько вариантов.

    Новый формат:

        file_path =
        Приказы\\2024\\Приказ.pdf

    Тогда используется:

        DOCUMENTS_ROOT / file_path


    Старый формат:

        file_path =
        E:\\БД Документов\\Приказы

        file_name =
        Приказ.pdf


    Также поддерживаются абсолютные пути:

        C:\\Documents\\Приказ.pdf

    и UNC:

        \\\\server\\folder\\Приказ.pdf
    """

    path_value = (doc_file_path or "").strip()
    name_value = (doc_file_name or "").strip()

    # --------------------------------------------------------
    # Ничего нет
    # --------------------------------------------------------

    if not path_value and not name_value:
        return None

    # --------------------------------------------------------
    # 1. Абсолютный путь
    # --------------------------------------------------------

    if path_value and is_absolute_path(path_value):

        path = Path(path_value)

        # Если path уже указывает на файл
        if path.is_file():
            return path

        # Старый формат:
        # file_path = папка
        # file_name = файл
        if name_value:
            combined = path / name_value

            if combined.is_file():
                return combined

        # Даже если файла сейчас нет,
        # возвращаем ожидаемый путь.
        if name_value:
            return path / name_value

        return path

    # --------------------------------------------------------
    # 2. Новый относительный путь
    # --------------------------------------------------------

    root = get_documents_root()

    if root is not None and path_value:

        relative_path = Path(
            path_value.replace("\\", os.sep)
        )

        full_path = root / relative_path

        if full_path.is_file():
            return full_path

        # Если указан относительный путь к папке
        # + отдельное имя файла.
        if name_value:
            combined = full_path / name_value

            if combined.is_file():
                return combined

        # Возвращаем ожидаемый путь
        return full_path

    # --------------------------------------------------------
    # 3. Корневая папка не настроена
    # --------------------------------------------------------

    return None


# ============================================================
# Нормализация пути перед сохранением
# ============================================================

def make_relative_path(path: str | Path) -> str:
    """
    Преобразует полный путь к документу
    в относительный путь относительно DOCUMENTS_ROOT.

    Например:

        D:\\БД Документов\\Приказы\\123.pdf

    превращается в:

        Приказы\\123.pdf
    """

    path = Path(path)

    root = get_documents_root()

    if root is None:
        raise ValueError(
            "Не настроена корневая папка документов."
        )

    try:
        relative = path.relative_to(root)

    except ValueError:
        raise ValueError(
            "Файл находится вне корневой папки документов:\n\n"
            f"{path}\n\n"
            f"Корневая папка:\n"
            f"{root}"
        )

    return normalize_relative_path(relative)


# ============================================================
# Открытие файла
# ============================================================

def open_file(path: str | Path) -> bool:
    """
    Открывает файл стандартной программой ОС.

    Возвращает True, если команда запуска была выполнена.
    """

    path = Path(path)

    if not path.exists():
        return False

    if not path.is_file():
        return False

    try:

        if sys.platform.startswith("win"):

            os.startfile(str(path))

        elif sys.platform == "darwin":

            subprocess.Popen(
                ["open", str(path)]
            )

        else:

            subprocess.Popen(
                ["xdg-open", str(path)]
            )

        return True

    except OSError:
        return False


# ============================================================
# Открытие папки
# ============================================================

def open_folder(path: str | Path) -> bool:
    """
    Открывает папку, в которой находится файл.
    """

    path = Path(path)

    if path.is_file():
        folder = path.parent
    else:
        folder = path

    if not folder.exists():
        return False

    try:

        if sys.platform.startswith("win"):

            os.startfile(str(folder))

        elif sys.platform == "darwin":

            subprocess.Popen(
                ["open", str(folder)]
            )

        else:

            subprocess.Popen(
                ["xdg-open", str(folder)]
            )

        return True

    except OSError:
        return False


# ============================================================
# Показать файл в Windows Explorer
# ============================================================

def open_folder_and_select(path: str | Path) -> bool:
    """
    Открывает папку и выделяет конкретный файл.

    Windows:
        explorer /select,...

    macOS:
        open -R

    Linux:
        открывает папку.
    """

    path = Path(path)

    if not path.exists():
        return False

    try:

        if sys.platform.startswith("win"):

            subprocess.Popen(
                [
                    "explorer",
                    "/select,",
                    str(path),
                ]
            )

            return True

        elif sys.platform == "darwin":

            subprocess.Popen(
                [
                    "open",
                    "-R",
                    str(path),
                ]
            )

            return True

        else:

            subprocess.Popen(
                [
                    "xdg-open",
                    str(path.parent),
                ]
            )

            return True

    except OSError:
        return False
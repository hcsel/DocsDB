# app/models.py
from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class Document:
    id: Optional[int] = None
    sheet: str = ""             # исходный раздел (Основные / обзор / Генпрокуратура)
    category: str = ""          # ИР, КоАП, ДА, ОС, АКУС...
    doc_type: str = ""          # Приказ, Письмо, Методические рекомендации...
    doc_date: Optional[str] = None  # ISO 'YYYY-MM-DD'
    doc_number: str = ""        # № документа
    title: str = ""             # название
    changes: str = ""           # что изменено
    notes: str = ""             # прочие пометки
    file_path: Optional[str] = None  # полный путь к файлу
    file_name: Optional[str] = None  # если известен только файл
    raw_link: str = ""          # исходная ссылка из Excel
    link_kind: str = "empty"    # 'unc' | 'filename' | 'note' | 'empty'
    needs_review: bool = False
    review_reason: str = ""
# main.py
import sys
from PySide6.QtWidgets import QApplication
from app import db
from ui.main_window import MainWindow


def main():
    db.init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("Справочник УИИ")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
# main.py
import sys
from PySide6.QtWidgets import QApplication
from app import db
from ui.main_window import MainWindow


def main():
    db.init_db()
    print("1. Запуск приложения")
    app = QApplication(sys.argv)
    print("2. QApplication создан")
    app.setApplicationName("Справочник УИИ")
    w = MainWindow()
    print(f"3. MainWindow создан") #TODO долгий запуск нада ускорить
    w.show()
    print("4. Окно показано")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
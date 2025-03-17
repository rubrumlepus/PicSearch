"""
Модуль содержит графический интерфейс и функции, позволяющие пользователю
взаимодействовать с программой.
"""

from pathlib import Path
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QPushButton, QWidget,
                               QMessageBox, QHBoxLayout, QFileSystemModel, QTreeView)
# from PySide6.QtCore import QSize

from PicSearch import sql


class MainWindow(QMainWindow):
    """Основное окно приложения"""
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PicSearch")
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # model = QFileSystemModel()
        # model.setRootPath(self.get_path())
        # tree = QTreeView()
        # tree.setModel(model)
        # tree.setRootIndex(model.index(self.get_path()))
        # tree.setIconSize(QSize(128, 128))

        self.add_image_bttn = QPushButton("Добавить изображение")
        self.add_image_bttn.clicked.connect(self.add_image)

        self.delete_image_bttn = QPushButton("Удалить изображение")
        self.delete_image_bttn.clicked.connect(self.delete_image)

        layout = QHBoxLayout()
        layout.addWidget(self.add_image_bttn)
        layout.addWidget(self.delete_image_bttn)
        # layout.addWidget(tree)
        central_widget.setLayout(layout)

        self.check_dir()

    def make_dir(self):
        """
        Метод для создания в файловой системе директории с названием 'PicSearch',
        где будут храниться изображения. При создании в файл 'dir_check.txt'
        записывается путь к созданной директории.
        """
        path = QFileDialog.getExistingDirectory(self, "Выберите директорию, где будет "
                                                      "размещена папка с изображениями:", "")
        new_path = Path(path) / "PicSearch"
        if path:
            Path(new_path).mkdir(parents=True, exist_ok=False)
            f = open('dir_check.txt', 'w')
            f.write(str(new_path))
            f.close()
        else:
            QMessageBox.warning(self, "Ошибка!", "Директория не выбрана. "
                                                 "Пожалуйста, выберите директорию.")

    @staticmethod
    def get_path():
        """
        Метод для извлечения из файла 'dir_check.txt' пути к директории, где хранятся изображения.
        :return d: Путь к директории, где хранятся изображения.
        """
        f = open('dir_check.txt', 'r')
        d = f.read()
        f.close()
        return d

    def check_dir(self):
        """
        Метод проверяет, существует ли директория, полученная с помощью метода get_path.
        """
        d = self.get_path()
        if not (d or Path(d).exists()):
            self.make_dir()

    def add_image(self):
        """
        Метод для добавления изображения.
        Метод перемещает выбранное изображение в папку PicSearch и добавляет путь к изображению
        в базу данных, вызывая соответствующий метод из модуля sql.
        """
        filename, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "",
                                                  "Images (*.png *.jpg)")
        name = Path(filename).name
        f = open('dir_check.txt', 'r')
        directory = Path(f.read())
        f.close()
        if filename:
            if not sql.check_path(image_path=filename):
                image_path = Path(filename)
                Path(image_path).rename(directory / name)
                image_path = Path(directory / name)
                sql.add_image_to_db(image_path)
            else:
                QMessageBox.warning(self, "Ошибка!",
                                    "Это изображение уже было добавлено.")
        else:
            QMessageBox.warning(self, "Ошибка!", "Изображение не было выбрано. "
                                                 "Пожалуйста, выберите изображение.")

    def delete_image(self):
        """
        Метод для удаления изображения.
        Метод удаляет выбранное изображение и удаляет путь к нему из базы данных,
        вызывая соответствующий метод из модуля sql.
        """
        try:
            filename, _ = QFileDialog.getOpenFileName(self, "Выберите изображение",
                                                      self.get_path(), "Images (*.png *.jpg)")
            if filename:
                if sql.check_path(image_path=filename):
                    image_path = Path(filename)
                    sql.delete_image_from_db(image_path=image_path)
                    Path.unlink(image_path)
                else:
                    QMessageBox.warning(self, "Ошибка!",
                                        "Выбранное изображение отсутствует в базе данных.")
            else:
                QMessageBox.warning(self, "Ошибка!", "Изображение не было выбрано. "
                                                     "Пожалуйста, выберите изображение.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")


app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
app.exec()

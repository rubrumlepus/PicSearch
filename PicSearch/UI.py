"""
Модуль содержит графический интерфейс и функции, позволяющие пользователю
взаимодействовать с программой.
"""

from pathlib import Path
import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QPushButton, QWidget,
                               QMessageBox, QLabel, QGridLayout, QVBoxLayout, QMenu, QInputDialog,
                               QTextEdit, QDialog, QScrollArea)
from PySide6.QtGui import QPixmap, QAction, QPalette, QContextMenuEvent
from PicSearch import sql
import send2trash


class MainWindow(QMainWindow):
    """Основное окно приложения"""
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PicSearch")

        scroll_area = QScrollArea()
        scroll_area.setBackgroundRole(QPalette.ColorRole.Dark)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)

        self.image_grid = ImageGrid(parent=self)
        scroll_area.setWidget(self.image_grid)

        self.image_grid.load_files(self.get_path())

        self.add_image_bttn = QPushButton("Добавить изображение")
        self.add_image_bttn.clicked.connect(self.add_image)

        layout = QVBoxLayout()
        layout.addWidget(scroll_area)
        layout.addWidget(self.add_image_bttn)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

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
                self.image_grid.load_files(directory)
            else:
                QMessageBox.warning(self, "Ошибка!",
                                    "Это изображение уже было добавлено.")
        else:
            QMessageBox.warning(self, "Ошибка!", "Изображение не было выбрано. "
                                                 "Пожалуйста, выберите изображение.")

    def delete_image(self, file):
        """
        Метод для удаления изображения.
        Метод удаляет выбранное изображение и удаляет путь к нему из базы данных,
        вызывая соответствующий метод из модуля sql.
        :param file: Путь к изображению, которое надо удалить.
        """
        try:
            if file:
                if sql.check_path(image_path=file):
                    image_path = Path(file)
                    sql.delete_image_from_db(image_path=image_path)
                    send2trash.send2trash(image_path)
                    self.image_grid.load_files(self.get_path())
                else:
                    QMessageBox.warning(self, "Ошибка!",
                                        "Выбранное изображение отсутствует в базе данных.")
            else:
                QMessageBox.warning(self, "Ошибка!", "Изображение не было выбрано. "
                                                     "Пожалуйста, выберите изображение.")
        except Exception as e:
            print(f"Произошла ошибка: {e}")

    def add_tag(self, file):
        """
        Метод для добавления тега. Вызывает соответствующий метод из модуля sql.
        :param file: Путь к изображению, к которому добавляется тег.
        """
        tag, ok = QInputDialog.getText(self, "Добавление тега", "Введите тег, "
                                                                "который хотите добавить:")
        if ok and tag:
            try:
                tag_id = sql.get_tag_id(tag)
                image_id = sql.get_image_id(file)
                if tag_id:
                    if not sql.check_tag(tag_id, image_id):
                        sql.connect_tag_to_image(image_id, tag_id)
                    else:
                        QMessageBox.warning(self, "Этот тег уже добавлен!", "Тег, который "
                                            "вы пытаетесь добавить, уже добавлен к этой картинке.")
                else:
                    sql.add_tag_to_db(tag)
                    sql.connect_tag_to_image(image_id, tag_id)
            except Exception as e:
                print(f"Произошла ошибка: {e}")

    def delete_tag(self):
        """
        Метод для удаления тега. Вызывает соответствующий метод из модуля sql.
        """
        tag, ok = QInputDialog.getText(self, "Удаление тега", "Введите тег, "
                                                              "который хотите удалить:")
        if ok and tag:
            try:
                tag_id = sql.get_tag_id(tag)
                if tag_id:
                    sql.delete_tag_from_db(tag)
                else:
                    QMessageBox.warning(self, "Ошибка!", "Вы пытаетесь удалить тег, "
                                                         "который не привязан к этой картинке.")
            except Exception as e:
                print(f"Произошла ошибка: {e}")


class ImageGrid(QWidget):
    """Класс для отображения загруженных изображений."""
    def __init__(self, parent=None):
        super().__init__()
        self.setParent(parent)
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

    def load_files(self, folder):
        file_folder = Path(folder)
        files = list(file_folder.glob('*.png')) + list(file_folder.glob('*.jpg')) + \
            list(file_folder.glob('*.jpeg')) + list(file_folder.glob('*.gif'))

        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        row, col = 0, 0
        for file in files:
            label = ImageLabel(parent=self.parent(), file=file)
            label.mousePressEvent = lambda event, f=file: self.open_image_viewer(event, f)

            self.layout.addWidget(label, row, col)

            col += 1
            if col >= 4:
                col = 0
                row += 1

    @staticmethod
    def open_image_viewer(event, file):
        if event.button() == Qt.MouseButton.LeftButton:
            image_id = sql.get_image_id(file)
            tags = sql.get_tags_for_image(image_id)
            viewer = ImageViewer(file, tags)
            viewer.exec()


class ImageLabel(QLabel):
    """ Класс для отрисовки загруженных изображений и отображения контекстного меню."""
    def __init__(self, parent=None, file=None):
        super().__init__()
        self.setParent(parent)
        self.file = file
        self.pixmap = QPixmap(str(file))
        self.setPixmap(self.pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio))

    def contextMenuEvent(self, ev: QContextMenuEvent) -> None:
        context_menu = QMenu(self)

        adding_tag = QAction("Добавить тег", self)
        adding_tag.triggered.connect(lambda: self.window().add_tag(self.file))
        deleting_image = QAction("Удалить изображение", self)
        deleting_image.triggered.connect(lambda: self.window().delete_image(self.file))
        deleting_tag = QAction("Удалить тег", self)
        deleting_tag.triggered.connect(lambda: self.window().delete_tag())

        context_menu.addAction(adding_tag)
        context_menu.addAction(deleting_image)
        context_menu.addAction(deleting_tag)

        context_menu.exec(self.mapToGlobal(ev.pos()))


class ImageViewer(QDialog):
    """Класс для просмотра изображения и его тегов."""
    def __init__(self, image_path, tags):
        super().__init__()
        self.setWindowTitle("Просмотр изображения")

        layout = QVBoxLayout()

        image_label = QLabel()
        pixmap = QPixmap(str(image_path))
        image_label.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio))
        layout.addWidget(image_label)

        tags_label = QLabel("Теги:")
        layout.addWidget(tags_label)

        tags_text = QTextEdit()
        tags_text.setPlainText(", ".join(tags))
        tags_text.setReadOnly(True)
        layout.addWidget(tags_text)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.setLayout(layout)


app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
app.exec()

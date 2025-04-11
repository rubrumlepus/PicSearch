"""
Модуль содержит графический интерфейс и функции, позволяющие пользователю
взаимодействовать с программой.
"""

from pathlib import Path
from io import BytesIO
import win32clipboard
from PIL import Image
import sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QPushButton, QWidget,
                               QMessageBox, QLabel, QGridLayout, QVBoxLayout, QMenu, QInputDialog,
                               QDialog, QScrollArea, QLineEdit, QCompleter, QTabWidget, QHBoxLayout,
                               QFrame)
from PySide6.QtGui import QPixmap, QAction, QContextMenuEvent, QMovie
from PicSearch import sql
from flow_layout import FlowLayout
import send2trash


class MainWindow(QMainWindow):
    """Основное окно приложения"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PicSearch")
        self.setGeometry(600, 100, 900, 600)

        self.image_scroll_area = QScrollArea()
        self.gif_scroll_area = QScrollArea()

        self.image_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.image_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.image_scroll_area.setWidgetResizable(True)

        self.gif_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.gif_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.gif_scroll_area.setWidgetResizable(True)

        self.image_grid = Grid(parent=self)
        self.image_scroll_area.setWidget(self.image_grid)
        self.gif_grid = Grid(parent=self)
        self.gif_scroll_area.setWidget(self.gif_grid)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.addTab(self.image_scroll_area, "Изображения")
        self.tab_widget.addTab(self.gif_scroll_area, "Анимации")

        self.searchbar = QLineEdit()
        self.searchbar.textEdited.connect(self.show_searched)
        self.completer = QCompleter(sql.get_tags())
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.searchbar.setCompleter(self.completer)

        self.image_grid.load_files(self.get_dir(), self.tab_widget.indexOf(self.image_scroll_area))
        self.gif_grid.load_files(self.get_dir(), self.tab_widget.indexOf(self.gif_scroll_area))

        self.add_image_button = QPushButton("Добавить изображение")
        self.add_image_button.clicked.connect(lambda: self.add_media("image"))
        self.add_gif_button = QPushButton("Добавить анимацию")
        self.add_gif_button.clicked.connect(lambda: self.add_media("gif"))

        layout = QVBoxLayout()
        layout.addWidget(self.searchbar)
        layout.addWidget(self.tab_widget)
        layout.addWidget(self.add_image_button)
        layout.addWidget(self.add_gif_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.check_dir()

    def make_dir(self):
        """
        Метод для создания в файловой системе директории с названием 'PicSearch',
        где будут храниться изображения и анимации. При создании в файл 'dir_check.txt'
        записывается путь к созданной директории.
        """
        path = QFileDialog.getExistingDirectory(self, "Выберите директорию, где будет "
                                                      "размещена папка с изображениями:", "")
        new_path = Path(path) / "PicSearch"
        if path:
            Path(new_path).mkdir(parents=True, exist_ok=False)
            f = open('PicSearch\dir_check.txt', 'w')
            f.write(str(new_path))
            f.close()
        else:
            QMessageBox.warning(self, "Ошибка!", "Директория не выбрана. "
                                                 "Пожалуйста, выберите директорию.")

    @staticmethod
    def get_dir():
        """
        Метод для извлечения из файла 'dir_check.txt' пути к директории, где хранятся изображения
        и анимации.
        :return d: Путь к директории, где хранятся изображения и анимации.
        """
        f = open('PicSearch\dir_check.txt', 'r')
        d = f.read()
        f.close()
        return d

    def check_dir(self):
        """
        Метод проверяет, существует ли директория, полученная с помощью метода get_dir.
        """
        d = self.get_dir()
        if not (d or Path(d).exists()):
            self.make_dir()

    def add_media(self, media_type: str):
        """
        Универсальный метод для добавления изображений или анимаций.
        :param media_type: 'image' или 'gif'
        """
        if media_type == 'image':
            file_filter = "Изображения (*.png *.jpg *.jpeg)"
            tab_index = self.tab_widget.indexOf(self.image_scroll_area)
            grid = self.image_grid
        elif media_type == 'gif':
            file_filter = "Анимации (*.gif)"
            tab_index = self.tab_widget.indexOf(self.gif_scroll_area)
            grid = self.gif_grid
        else:
            QMessageBox.warning(self, "Ошибка!", "Этот тип медиа не поддерживается.")
            return

        filename, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", file_filter)

        if not filename:
            QMessageBox.warning(self, "Ошибка!",
                                f"{'Изображение не выбрано.' if media_type == 'image' else 'Анимация не выбрана.'}")
            return

        name = Path(filename).name
        directory = Path(self.get_dir())

        if sql.check_path(image_path=filename):
            QMessageBox.warning(self, "Ошибка!", "Этот файл уже был добавлен.")
            return

        try:
            new_path = directory / name
            Path(filename).rename(new_path)
            sql.add_image_to_db(new_path)
            grid.load_files(directory, tab_index)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка!", f"Ошибка при добавлении файла: {e}")

    def delete_media(self, file):
        """
        Метод для удаления изображения или анимации.
        Метод удаляет выбранный объект и удаляет путь к нему из базы данных,
        вызывая соответствующий метод из модуля sql.
        :param file: Путь к изображению/анимации.
        """
        try:
            if file:
                if sql.check_path(image_path=file):
                    image_path = Path(file)
                    sql.delete_image_from_db(image_path=image_path)
                    send2trash.send2trash(image_path)
                    self.image_grid.load_files(self.get_dir(), self.tab_widget.currentIndex())
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
                    tag_id = sql.get_tag_id(tag)
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

    def show_searched(self):
        """
        Обновляет отображение в зависимости от текста в строке поиска и текущей вкладки.
        """
        text = self.searchbar.text()
        current_index = self.tab_widget.currentIndex()

        grid = self.image_grid if current_index == 0 else self.gif_grid
        folder = self.get_dir()

        for i in reversed(range(grid.layout.count())):
            widget = grid.layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        if text == "":
            grid.load_files(folder, current_index)
            return

        images = sql.get_images()

        row, col = 0, 0
        for image_path in images:
            image_path = Path(image_path[0])
            if current_index == 0 and image_path.suffix.lower() not in ['.png', '.jpg', '.jpeg']:
                continue
            if current_index == 1 and image_path.suffix.lower() != '.gif':
                continue

            image_id = sql.get_image_id(file=image_path)
            tags = sql.get_tags_for_image(image_id=image_id)

            if any(text.lower().strip() in tag.lower().strip() for tag in tags):
                label = MediaLabel(parent=self, file=image_path)
                grid.layout.addWidget(label, row, col)

                col += 1
                if col >= 4:
                    col = 0
                    row += 1


class Grid(QWidget):
    """Класс для отображения загруженных изображений."""
    def __init__(self, parent=None):
        super().__init__()
        self.setParent(parent)
        self.layout = QGridLayout(self)
        self.setLayout(self.layout)

    def load_files(self, folder, tab_index):
        file_folder = Path(folder)
        if tab_index == 0:
            files = list(file_folder.glob('*.png')) + list(file_folder.glob('*.jpg')) + \
                    list(file_folder.glob('*.jpeg'))
        else:
            files = list(file_folder.glob('*.gif'))

        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        row, col = 0, 0
        for file in files:
            label = MediaLabel(parent=self.parent(), file=file)
            label.mousePressEvent = lambda event, f=file: self.open_viewer(event, f)

            self.layout.addWidget(label, row, col)

            col += 1
            if col >= 4:
                col = 0
                row += 1

    @staticmethod
    def open_viewer(event, file):
        if event.button() == Qt.MouseButton.LeftButton:
            image_id = sql.get_image_id(file)
            tags = sql.get_tags_for_image(image_id)
            viewer = MediaViewer(file, tags)
            viewer.exec()


class MediaLabel(QLabel):
    """Класс для отображения изображений и GIF-файлов с контекстным меню."""

    def __init__(self, parent=None, file=None):
        super().__init__()
        self.setParent(parent)
        self.file = Path(file)
        self.setFixedSize(200, 200)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.file.suffix.lower() == '.gif':
            self.movie = QMovie(str(self.file))
            self.movie.setScaledSize(QSize(180, 180))
            self.setMovie(self.movie)
            self.movie.start()
        else:
            self.pixmap = QPixmap(str(self.file))
            scaled = self.pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled)

    def contextMenuEvent(self, ev: QContextMenuEvent) -> None:
        context_menu = QMenu(self)

        adding_tag = QAction("Добавить тег", self)
        adding_tag.triggered.connect(lambda: self.window().add_tag(self.file))

        deleting_media = QAction("Удалить", self)
        deleting_media.triggered.connect(lambda: self.window().delete_media(self.file))

        deleting_tag = QAction("Удалить тег", self)
        deleting_tag.triggered.connect(lambda: self.window().delete_tag())

        context_menu.addAction(adding_tag)
        context_menu.addAction(deleting_tag)
        context_menu.addAction(deleting_media)

        if self.file.suffix.lower() != '.gif':
            copying_image = QAction("Копировать изображение", self)
            copying_image.triggered.connect(lambda: self.copy_to_clipboard(self.file))
            context_menu.addAction(copying_image)

        context_menu.exec(self.mapToGlobal(ev.pos()))

    @staticmethod
    def copy_to_clipboard(file):
        """
        Метод для копирования изображения в буфер обмена.
        :param file: Путь к изображению, которое нужно скопировать.
        """
        if file:
            image = Image.open(file)
            output = BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()


class MediaViewer(QDialog):
    """Класс для просмотра изображения или анимации и тегов."""

    def __init__(self, file_path, tags):
        super().__init__()
        self.setWindowTitle("Просмотр медиафайла")
        self.file_path = Path(file_path)
        self.tags = tags

        self.layout = QVBoxLayout()

        self.media_label = QLabel()
        self.media_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        max_size = QSize(500, 500)

        if self.file_path.suffix.lower() == '.gif':
            self.movie = QMovie(str(self.file_path))
            self.movie.setScaledSize(self.movie.scaledSize().boundedTo(max_size))
            self.media_label.setMovie(self.movie)
            self.movie.start()
        else:
            pixmap = QPixmap(str(self.file_path))
            scaled_pixmap = pixmap.scaled(max_size, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            self.media_label.setPixmap(scaled_pixmap)

        self.layout.addWidget(self.media_label, alignment=Qt.AlignmentFlag.AlignCenter)

        tags_label = QLabel("Теги:")
        self.layout.addWidget(tags_label)

        self.tags_scroll = QScrollArea()
        self.tags_scroll.setWidgetResizable(True)

        self.tags_container = QWidget()
        self.tags_layout = FlowLayout(self.tags_container)
        self.tags_container.setLayout(self.tags_layout)

        self.tags_scroll.setWidget(self.tags_container)
        self.layout.addWidget(self.tags_scroll)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.close)
        self.layout.addWidget(close_button)

        self.setLayout(self.layout)

        self.render_tags()

    def render_tags(self):
        for i in reversed(range(self.tags_layout.count())):
            item = self.tags_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        for tag in self.tags:
            tag_frame = QFrame()
            tag_frame.setObjectName("TagFrame")
            tag_frame.setLayout(QHBoxLayout())
            tag_frame.layout().setContentsMargins(6, 2, 6, 2)
            tag_frame.layout().setSpacing(4)

            tag_label = QLabel(tag)
            tag_label.setObjectName("TagText")

            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(16, 16)
            remove_btn.setObjectName("RemoveButton")
            remove_btn.clicked.connect(lambda _, t=tag: self.confirm_delete_tag(t))

            tag_frame.layout().addWidget(tag_label)
            tag_frame.layout().addWidget(remove_btn)

            self.tags_layout.addWidget(tag_frame)

    def confirm_delete_tag(self, tag):
        reply = QMessageBox.question(
            self,
            "Удаление тега",
            f"Вы уверены, что хотите удалить тег '{tag}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                tag_id = sql.get_tag_id(tag)
                file_id = sql.get_image_id(self.file_path)
                sql.disconnect_tag_from_image(file_id, tag_id)
                self.tags.remove(tag)
                self.render_tags()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить тег: {e}")


app = QApplication(sys.argv)
with open("PicSearch\style.qss", "r", encoding="utf-8") as f:
    app.setStyleSheet(f.read())
main_window = MainWindow()
main_window.show()
app.exec()

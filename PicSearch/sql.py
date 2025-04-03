"""
Модуль содержит все функции, взаимодействующие с базой данных с помощью SQL-команд.
"""
import json
import psycopg2

with open('config.json') as config_file:
    config = json.load(config_file)
    db_name = config['database']['database_name']
    db_user = config['database']['user']
    db_password = config['database']['password']
    db_host = config['database']['host']
    db_port = config['database']['port']

# Объект класса connection, обрабатывающий подключение к базе данных PostgreSQl.
connection = psycopg2.connect(database=db_name, user=db_user, password=db_password,
                              host=db_host, port=db_port)

# Объект класса cursor, позволяющий выполнять psql команды в базе данных.
cursor = connection.cursor()


def add_image_to_db(image_path):
    """
    Добавляет путь к изображению в базу данных.
    :param image_path: Путь к изображению на диске.
    """
    try:
        insert_query = "INSERT INTO images (image_path) VALUES (%s)"
        cursor.execute(insert_query, (str(image_path), ))

        connection.commit()
        print("Изображение успешно добавлено.")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


def delete_image_from_db(image_path):
    """
    Удаляет путь к изображению из базы данных.
    :param image_path: Путь к изображению на диске.
    """
    try:
        delete_query = "DELETE FROM images WHERE image_path = (%s)"
        cursor.execute(delete_query, (str(image_path).replace('/', '\\'), ))

        connection.commit()
        print("Изображение успешно удалено.")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


def add_tag_to_db(tag):
    """
    Добавляет тег в базу данных.
    :param tag: Тег, который нужно добавить.
    """
    try:
        insert_query = "INSERT INTO tags (tag_name) VALUES (%s)"
        cursor.execute(insert_query, (tag, ))

        connection.commit()
        print("Тег успешно добавлен.")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


def delete_tag_from_db(tag):
    """
    Удаляет тег из базы данных.
    :param tag: Тег, который нужно удалить.
    """
    try:
        delete_query = "DELETE FROM tags WHERE tag_name = (%s)"
        cursor.execute(delete_query, (tag, ))

        connection.commit()
        print("Тег успешно удален.")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


def connect_tag_to_image(image_id, tag_id):
    """
    Связывает тег с изображением в базе данных.
    :param image_id: Id изображения в базе данных.
    :param tag_id:  Id тега в базе данных.
    """
    try:
        insert_query = "INSERT INTO image_tags (image_id, tag_id) VALUES(%s, %s)"
        cursor.execute(insert_query, (image_id, tag_id, ))

        connection.commit()
        print("Тег привязан к изображению.")

    except Exception as e:
        print(f"Произошла ошибка: {e}")


def check_path(image_path):
    """
    Проверяет, существует ли переданный путь к изображению в базе данных.
    :param image_path: Путь к изображению.
    :return: True в случае, когда путь существует, false - если такой путь отсутствует.
    """
    try:
        check_query = "SELECT id FROM images WHERE image_path = (%s)"
        cursor.execute(check_query, (str(image_path).replace('/', '\\'), ))

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Произошла ошибка: {e}")


def check_tag(tag_id, image_id):
    try:
        check_query = "SELECT * FROM image_tags WHERE tag_id = (%s) AND image_id = (%s)"
        cursor.execute(check_query, (tag_id, image_id, ))

        return cursor.rowcount > 0

    except Exception as e:
        print(f"Произошла ошибка: {e}")


def get_tag_id(tag):
    """
    Получает айди тега.
    :param tag: Тег, айди которого нужно получить.
    :return: Айди тега.
    """
    try:
        select_query = "SELECT id FROM tags WHERE tag_name = (%s)"
        cursor.execute(select_query, (tag, ))

        return cursor.fetchone()

    except Exception as e:
        print(f"Произошла ошибка: {e}")


def get_image_id(file):
    """
    Получает айди изображения.
    :param file: Путь к изображению, айди которого нужно получить.
    :return: Айди изображения.
    """
    try:
        select_query = "SELECT id FROM images WHERE image_path = (%s)"
        cursor.execute(select_query, (str(file).replace('/', '\\'), ))

        return cursor.fetchone()

    except Exception as e:
        print(f"Произошла ошибка: {e}")


def get_tags_for_image(image_id):
    """
    Получает список тегов для изображения.
    :param image_id: ID изображения, для которого нужно получить список тегов.
    :return: Список тегов для изображения.
    """
    try:
        image_select_query = "SELECT tag_id FROM image_tags WHERE image_id = (%s)"
        cursor.execute(image_select_query, (image_id, ))
        tag_ids = cursor.fetchall()

        tag_select_query = "SELECT tag_name FROM tags WHERE id = (%s)"
        tags = []
        for tag in tag_ids:
            cursor.execute(tag_select_query, (tag[0], ))
            tag_name = cursor.fetchone()
            if tag_name:
                tags.append(tag_name[0])

        return tags

    except Exception as e:
        print(f"Произошла ошибка: {e}")

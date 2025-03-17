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

import psycopg2 as ps
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("host")
user = os.getenv("user")
password = os.getenv("password")
db_name = os.getenv("db_name")


try:
    conn = ps.connect(
        host=host,
        user=user,
        password=password,
        database=db_name
    )
except Exception:
    print('Не получается соединиться с базой данных')

cursor = conn.cursor()
conn.autocommit = True

cursor.execute("""CREATE TABLE IF NOT EXISTS person (
               id SERIAL PRIMARY KEY,
               name VARCHAR(255),
               age INT,
               gender CHAR
               );
               """)


def get_all_users():
    cursor.execute("""SELECT * FROM person""")
    for user in cursor.fetchall():
        print(user)


def add_user():
    name = input('Введите имя юзера: ')
    while True:
        try:
            age = int(input("Введите возраст юзера: "))
        except ValueError:
            print("Недопустимое значение")
            continue
        else:
            break

    while True:
        gender = input('Введите пол юзера (м или ж): ')
        if gender in ('м', 'ж'):
            break
        else:
            print('Недопустимое значение')
            continue
    cursor.execute(""" INSERT INTO person (id, name, age, gender) VALUES(
               DEFAULT, %s, %s, %s)""", (name, age, gender))
    print('Пользователь добавлен')


def delete_user():
    cursor.execute("""SELECT id FROM person""")
    users_lst = []
    for x in cursor.fetchall():
        users_lst.append(x[0])
    while True:
        try:
            user_id = int(input('Введите id юзера, которого хотите удалить: '))
        except ValueError:
            print('Invalid type')
            continue
        if user_id not in users_lst:
            print('Такого id нет')
            continue
        else:
            break
    cursor.execute(f"SELECT name FROM person WHERE id={user_id}")
    for res in cursor.fetchall():
        print('Пользователь', res[0], 'удален')
    cursor.execute(f"DELETE FROM person WHERE id={user_id}")


while True:
    print('Список команд:\n0:Завершить\n1:Посмотреть список всех юзеров',
          '\n2:Добавить юзера\n3:Удалить юзера')
    command = int(input('Введите номер команды: '))
    if command == 0:
        break
    elif command == 1:
        get_all_users()
        continue
    elif command == 2:
        add_user()
        continue
    elif command == 3:
        delete_user()
        continue
    else:
        print('Такой команды нет\n')
        continue


conn.commit()
cursor.close()
conn.close()

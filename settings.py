import os
from aiogram import Bot, Dispatcher
import hashlib
import sqlite3

# дебаг режим
debug = True


# Абсолютный путь к soffice. На дистрибутивах линукса в большинстве случаев менять путь не нужно 
# Так как это часть libreoffice, то нужно установить его полностью. Команда: apt install libreoffice
soffice_path = '/usr/bin/soffice'

# токен тг бота
TOKEN = "TOKEN"

# bot, dp - необходимые штуки для работы бота
bot = Bot(token=TOKEN)
dp = Dispatcher()


# имя базы данных
db_name = 'students.db'


# ссылка на сайт. обязательна должна иметь вид с id на конце в виде прогрессии n + 1.
# вид ссылки может быть как example.com, так и пример.рф 
url_base = 'https://гимназия5.екатеринбург.рф/file/download?id='

# список id каналов для отправки расписания, а так же id для отправки ошибок
# значения явяются числом. группы и каналы имеют -100 в начале.
channels = [0, 1]
my_id = 2 # замените на свой айдишник
id4log = 3 # айди группы с логами


# классы
# для каждого учебного года/школы нужно ручками добавлять свои
global_classes = ["5а", "5б", "5в", "5г", "5м",
           "6а", "6б", "6в", "6г", 
           "7а", "7б", "7в", "7г", "7д", "7е", 
           "8а", "8б", "8в", "8г", "8д", 
           "9а", "9б", "9в", "9г", "9д",
           "10а", "10б", "10в", "10г", "10д", 
           "11а", "11б", "11в", "11г", "11д"]


# список всех файлов, для их удаления перед скачиванием нового
all_files = ["page_1.png", "page_2.png", "page_4.png", "sched.xlsx", "sched.pdf"]


# список из дней недели для проверки файлов
days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]


# файлы с картинками расписания для отправки
files = ["page_1.png", "page_2.png", "page_4.png"]


################################################
#                  ФУНКЦИИ                     #
################################################


# функция чтения айдишника
def load_last_id():
    if not os.path.exists("last_id.txt"):
        return 13000
    with open("last_id.txt", "r") as f:
        return int(f.read().strip())


# функция сохранения айдишника
def save_last_id(value):
    with open("last_id.txt", "w") as f:
        f.write(str(value))


# функция чтения даты последнего расписания
def load_filename_n():
    if not os.path.exists("filename_n.txt"):
        return 1
    with open("filename_n.txt", "r") as f:
        return int(f.read().strip())


# функция сохранения даты последнего расписания
def save_filename_n(value):
    with open("filename_n.txt", "w") as f:
        f.write(str(value))


# простая проверка искомого файла
def approve(filename, data):

    if not os.path.exists("old_sched.xlsx"):
        return filename.endswith(".xlsx") and any(day in filename for day in days)

    hash_old = hashlib.sha1(open("old_sched.xlsx", "rb").read()).hexdigest()
    hash_new = hashlib.sha1(data).hexdigest()

    return filename.endswith(".xlsx") and any(day in filename for day in days) and hash_old != hash_new


# функция удаления файлов (для предотвращения потенциальных ошибок)
def delete():
    for file in all_files:
        try:
            os.remove(file)
        except:
            print("не получилось удалить, фиг с ним, не критично...")


################################################
#                  SQLite                      #
################################################


# Подключение к базе данных
def connect(db_name=db_name):
    conn = sqlite3.connect(db_name)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# Инициализация бдшки
def init_db(global_classes=global_classes):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        name TEXT PRIMARY KEY
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        class_name TEXT NOT NULL,
        FOREIGN KEY (class_name) REFERENCES classes(name)
    )
    """)

    for c in global_classes:
        cur.execute("INSERT OR IGNORE INTO classes (name) VALUES (?)", (c,))

    conn.commit()
    conn.close()


# Функция добавления ученика по классу
def add_student(student_id, class_name):
    conn = connect()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO students (student_id, class_name) VALUES (?, ?)",
            (student_id, class_name)
        )
        conn.commit()
        return f'Вы были успешно привязаны к классу {class_name}'
    except sqlite3.IntegrityError:
        return 'Класс не найден. Проверьте правильность написания класса'
    finally:
        conn.close()


# Функция удаления ученика из бдшки
def remove_student(student_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM students WHERE student_id = ?",
        (student_id,)
    )

    conn.commit()
    deleted = cur.rowcount
    conn.close()

    return deleted


# Функция получения списка, в котором находятся id всех учеников выбранного класса. Нужно для рассылки
def get_students(class_name, db_name=db_name):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    cur.execute(
        "SELECT student_id FROM students WHERE class_name = ?",
        (class_name,)
    )

    rows = cur.fetchall()
    conn.close()

    return [r[0] for r in rows]


# функция проверки наличия id ученика в базе данных
def student_exists(student_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM students WHERE student_id = ? LIMIT 1",
        (student_id,)
    )

    exists = cur.fetchone() is not None
    conn.close()
    return exists


# функция нахождения класса по id ученика
def get_student_class(student_id):
    conn = connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT class_name FROM students WHERE student_id = ? LIMIT 1",
        (student_id,)
    )

    row = cur.fetchone()
    conn.close()

    return row[0] if row else None

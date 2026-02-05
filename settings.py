import os
from aiogram import Bot, Dispatcher

# дебаг режим
debug = True


# Абсолютный путь к soffice. На дистрибутивах линукса в большинстве случаев менять путь не нужно 
# Так как это часть libreoffice, то нужно установить его полностью. Команда: apt install libreoffice
soffice_path = '/usr/bin/soffice'


# токен тг бота
TOKEN = ""

# bot, dp - необходимые штуки для работы бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ссылка на сайт. обязательна должна иметь вид с id на конце в виде прогрессии n + 1.
# вид ссылки может быть как example.com, так и пример.рф 
url_base = 'https://вашсайт.рф/file/download?id='

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


# список всех файлов, для их удаления перед скачиванием нового
all_files = ["page_1.png", "page_2.png", "page_4.png", "sched.xlsx", "sched.pdf"]

# функция удаления файлов (для предотвращения потенциальных ошибок)
def delete():
    for file in all_files:
        try:
            os.remove(file)
        except:
            print("не получилось удалить, фиг с ним, не критично...")


# список из дней недели для проверки файлов
days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]

# простая проверка искомого файла
def approve(filename, data):
    hash_old = hashlib.sha1(open("old_sched.xlsx", "rb").read()).hexdigest()
    hash_new = hashlib.sha1(data).hexdigest()

    return filename.endswith(".xlsx") and any(day in filename for day in days) and hash_old != hash_new


# файлы с картинками расписания для отправки
files = ["page_1.png", "page_2.png", "page_4.png"]

# список id каналов для отправки расписания, а так же id для отправки ошибок
# значения явяются числом. группы и каналы имеют -100 в начале.
channels = []
my_id = 0
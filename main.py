import aiohttp
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
import subprocess
import shlex
from pdf2image import convert_from_path
from pdf2image.exceptions import PDFPageCountError
import time
import os
import shutil
from fill_s import fill_sched

# дебаг режим
debug = True


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


# channels - айдишники каналов, куда будет кидаться, рассылка расписания, специально для каналов: -100 + chat_id
# days - дни недели (для проверки файла), files - файлы с фотками расписания (для скидывания)
# all_files - название всех файлов, last_id - id последнего найденного файла (любого), TOKEN - токен тгбота. 
# bot, dp - необходимые штуки для работы бота, n - номер попытки найти файл
# filename_n - дата предыдущего файла с расписанием
channels = []
days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота"]
files = ["page_1.png", "page_2.png", "page_4.png"]
all_files = ["page_1.png", "page_2.png", "page_4.png", "sched.xlsx", "sched.pdf"]
last_id = load_last_id()
TOKEN = ""
bot = Bot(token=TOKEN)
dp = Dispatcher()
n = 1
my_id = None
filename_n = '1'

# функция удаления файлов (для предотвращения потенциальных ошибок)
def delete():
    for file in all_files:
        try:
            os.remove(file)
        except:
            print("не получилось удалить, фиг с ним, не критично...")


# функция отправки группы из трёх картинок расписания с подписью к первой
async def send_images(sched_name, chats=channels):

    media = []
    caption = sched_name.replace("_", " ").split(".")[0]

    success = False
    att = 10
    while not success and att:
        for filename in files:
            if os.path.exists(filename):
                media.append(types.InputMediaPhoto(media=types.FSInputFile(filename), caption = caption if filename == "page_1.png" else ""))
            if not media:
                if debug:
                    print("Файлы не существуют.")
        try:
            if debug:
                print("Отправляем фотки в каналы...")
            for chat in chats:
                await bot.send_media_group(chat_id=chat, media=media)
            success = True
            print("Успешно отправлено расписание!")
        except Exception as e:
            if debug:
                print(f"Ошибка отправки {filename}: {e}")
            att -= 1
            await asyncio.sleep(5)


# супер простая проверка искомого файла XD
def approve(file):
    return file.endswith(".xlsx") and any(day in file for day in days)


# функция конвертации xlsx в pdf
def xlsx_to_pdf(input_file, output_dir):
    cmd = rf'/usr/bin/soffice --headless --convert-to pdf --outdir {output_dir} {input_file}'
    success = False
    while not success:
        try:
            if debug:
                print("Преобразуем xlsx в pdf...")
            subprocess.run(shlex.split(cmd), check=True)
            success = True
        except Exception as e:
            if debug:
                print("Ошибка преобразование xlsx в pdf. Пробуем снова")
            time.sleep(5)

# функция конвертации pdf в png
def pdf_to_png(poppler_path):
    success = False
    while not success:
        try:
            n_page = [0, 1, 3]
            pages = convert_from_path('sched.pdf', dpi=150)
            if debug:
                print("Преобразуем pdf в png...")
            for page in n_page:
                img = pages[page]
                img.save(f'page_{page+1}.png')
            success = True
        except PDFPageCountError as e:
            if debug:
                print("Ошибка преобразование pdf в png. Пробуем снова")
            time.sleep(5)

# основная асинхронная функция работы бота
async def check():
    global n, last_id, filename_n

    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession() as session:
        while True:
            url = f'https://гимназия5.екатеринбург.рф/file/download?id={last_id + n}'

            try:
                async with session.get(url) as response:

                    # основной цикл проверки наличия файла. при респонсе отличном от 200 идёт цикл из попыток
                    # найти существующий файл при id от последнего и до +15
                    if response.status != 200:
                        if n < 15:
                            if debug:
                                print(f"Нет файла, id - {last_id + n}, попытка номер {n}")
                            n += 1
                            await asyncio.sleep(3)
                            continue
                        else:
                            if debug:
                                print(f"Нет файла, id - {last_id + n}, попытка номер {n}")
                            n = 1
                            await asyncio.sleep(3)
                            continue

                    # сли мы нашли файл, то для начала получаем его имя, отделяя от него "filename="
                    first_filename = response.headers.get("Content-Disposition")
                    filename = first_filename.split("filename=")[1].strip('"')

                    # если файл не соответствует требованиям (расширение .xlsx и день недели в названии),
                    # то повышаем last_id на 1 и изменяем n (номер попытки) на 1, чтобы при следующей
                    # проверке цикл начинался с первой попыке (last_id + 1)
                    if not approve(filename):
                        if debug:
                            print(f"Не тот файл, id - {last_id + n}, попытка номер {n}")
                        last_id += n
                        save_last_id(last_id)
                        n = 1
                        await asyncio.sleep(3)
                        continue

                    # найден нужный файл, для начала скачиваем его,
                    # потом преобразуем скачанную excel таблицу в pdf файл для дальнейшего
                    # преобразования в картинку png
                    # предварительно удаляем предыдущие файлы
                    delete()
                    data = await response.read()
                    with open("sched.xlsx", "wb") as f:
                        f.write(data)
                    await asyncio.sleep(1)
                    
                    if filename_n == filename.split("_")[0]:
                    	fill_sched("old_sched.xlsx", "sched.xlsx")
                    else:
                    	shutil.copy("sched.xlsx", "old_sched.xlsx")
                    	filename_n = filename.split("_")[0]
                    
                    # xlsx -> pdf -> png
                    xlsx_to_pdf("sched.xlsx", ".")
                    pdf_to_png(poppler_path="/usr/bin")
                    if debug:
                        print(f"Успешно выполнено преобразование! id: {last_id + n}")
                    last_id += n
                    save_last_id(last_id)
                    n = 1
                    
                    # отправляем
                    await send_images(filename)
                    await asyncio.sleep(3)

            # перебор известных мне ошибок
            except aiohttp.ClientConnectorError as e:
                if debug:
                    print(f"Ошибка подключения: {e}")
                    await bot.send_message(chat_id=my_id, text=f"Ошибка подключение: {e}")
                await asyncio.sleep(10)
                continue

            except asyncio.TimeoutError:
                if debug:
                    print("Таймаут")
                    await bot.send_message(chat_id=my_id, text=f"Таймаут бота")
                await asyncio.sleep(10)
                continue

            except Exception as e:
                if debug:
                    print(f"Непредвиденная ошибка: {e}")
                    await bot.send_message(chat_id=my_id, text=f"Непредвиденная ошибка: {e}")
                await asyncio.sleep(10)
                continue

# команда /start
@dp.message(CommandStart())
async def get_start(message: Message):
    await message.answer('Данный бот не имеет никакого отношения к учительскому составу, работникам, администрации и руководству Гимназии №5.\n'
                        'Поддержать автора вы можете подпиской на тгк @horunikko, либо покупкой дешёвого VPN сервиса (по этому в лс: @ahorotoru)\n\n'
                        '<tg-spoiler>Могу предоставить помощь в создании тг ботов, либо полностью написать его за вас, по всем вопросам тоже в лс: @ahorotoru</tg-spoiler>',
                        parse_mode='HTML')


# функция запуска бота
async def main():
    asyncio.create_task(check())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
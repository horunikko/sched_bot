import aiohttp
import asyncio
import time
import os
import shutil
from fill_sched import fill_sched
from tg_cmds import send_images, get_start
from conv import xlsx_to_pdf, pdf_to_png
from settings import *


# last_id - id последнего найденного файла (любого), n - номер попытки найти файл
# filename_n - дата предыдущего файла с расписанием
last_id = load_last_id()
n = 1
filename_n = load_filename_n()


# основная асинхронная функция работы бота
async def check():
    global n, last_id, filename_n

    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession() as session:
        while True:
            url = f'{url_base}{last_id + n}'

            try:
                async with session.get(url) as response:

                    # основной цикл проверки наличия файла. при респонсе отличном от 200 идёт цикл из попыток
                    # найти существующий файл при id от последнего и до +15
                    if response.status != 200:
                        if n < 15:
                            n += 1
                            await asyncio.sleep(3)
                            continue
                        else:
                            n = 1
                            await asyncio.sleep(3)
                            continue

                    # сли мы нашли файл, то для начала получаем его имя, отделяя от него "filename="
                    first_filename = response.headers.get("Content-Disposition")
                    filename = first_filename.split("filename=")[1].strip('"')
                    data = await response.read()

                    # если файл не соответствует требованиям (расширение .xlsx и день недели в названии),
                    # а так же если хэш файла равен хэшу предыдущего расписания,
                    # то повышаем last_id на 1 и изменяем n (номер попытки) на 1, чтобы при следующей
                    # проверке цикл начинался с первой попыке (last_id + 1)
                    if not approve(filename, data):
                        if debug:
                            print(f"Не тот файл, id - {last_id + n}, попытка номер {n}")
                        last_id += n
                        save_last_id(last_id)
                        n = 1
                        await asyncio.sleep(3)
                        continue

                    # найден нужный файл, для начала скачиваем его, потом преобразуем скачанную excel таблицу
                    # в pdf файл для дальнейшего преобразования в картинку png. предварительно удаляем предыдущие файлы
                    delete()
                    with open("sched.xlsx", "wb") as f:
                        f.write(data)
                    await asyncio.sleep(1)
                    
                    # проверяем является ли расписание изменением
                    if filename_n == int(filename.split("_")[0]) and os.path.exists("old_sched.xlsx"):
                    	fill_sched("old_sched.xlsx", "sched.xlsx")
                    else:
                    	shutil.copy("sched.xlsx", "old_sched.xlsx")
                    	save_filename_n(filename.split("_")[0])
                    
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


# функция запуска бота
async def main():
    asyncio.create_task(check())
    await dp.start_polling(bot)
    print("бот успешно запустился")

if __name__ == "__main__":
    asyncio.run(main())
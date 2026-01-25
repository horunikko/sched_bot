import asyncio
from aiogram import types
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
import os
import time
from db import bot, dp, files, channels, debug


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


# команда /start
@dp.message(CommandStart())
async def get_start(message: Message):
    await message.answer('Данный бот не имеет никакого отношения к учительскому составу, работникам, администрации и руководству Гимназии №5.\n'
                        'Поддержать автора вы можете подпиской на тгк @horunikko, либо покупкой дешёвого VPN сервиса (по этому в лс: @ahorotoru)\n\n'
                        '<tg-spoiler>Могу предоставить помощь в создании тг ботов, либо полностью написать его за вас, по всем вопросам тоже в лс: @ahorotoru</tg-spoiler>',
                        parse_mode='HTML')
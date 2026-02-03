import asyncio
from aiogram import types, Router, F
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.enums import ParseMode
import os
import time
from db import bot, dp, files, channels, debug, my_id


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


# функция отправки нужного сообщения пользователем
@dp.message(Command("send"))
async def msg_send(message: Message, command: CommandObject):
    if message.from_user.id != my_id:
        await message.answer("Вы не можете использовать эту команду!")
        return

    if command.args:
        try:
            for chat in channels:
                await bot.send_message(chat_id=chat, text=command.args)
                await message.answer("Сообщение успешно отправлено!")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
    
    else:
        await message.answer(text="Использование: <blockquote>/send сообщение</blockquote>", parse_mode='HTML')


# команда удаления сообщения
@dp.message(Command("delete"))
async def msg_delete(message: Message, command: CommandObject):
    if message.from_user.id != my_id:
        await message.answer("Вы не можете использовать эту команду!")
        return

    if command.args:
        try:
            args = command.args.split()
            chat_id = channels[int(args[0].strip()) - 1]
            msg_id = args[1]
            for i in range(3):
                await bot.delete_message(chat_id=chat_id, message_id=msg_id + i)
            await message.answer("Сообщение было успешно удалено!")
        except Exception as e:
            print(e)
            await message.answer(f"Ошибка удаления: {e}")
    else:
        text = "Использование: <blockquote>/delete номер_чата айди_соо</blockquote>\n\nМои чаты:\n"
        for n, channel in enumerate(channels):
            channel = await bot.get_chat(channel)
            text += f"{n + 1}. {channel.title}\n"
    
        await message.answer(text, parse_mode='HTML')
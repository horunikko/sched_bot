import asyncio
from aiogram import types, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.enums import ParseMode
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import os
import time
from settings import *
from xlsx_defs import find_in_sched, normal, get_day


class Reg(StatesGroup):
    usr_id = State()
    usr_class = State()


# функция отправки группы из трёх картинок расписания с подписью к первой
async def send_images(chats=channels):

    caption = get_day(file="sched.xlsx")

    success = False
    att = 10
    while not success and att:
        media = []

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


# функция отправки изменения сообщений лично
async def send_private(new):
    for class_name in global_classes:
        reply = find_in_sched(new=new, classes=[class_name])

        if not new:
            last_reply = find_in_sched(new=new, classes=[class_name], file='rec_sched.xlsx')

        if reply and normal(last_reply) != normal(reply):

            for student in get_students(class_name=class_name):
                try:
                    await bot.send_message(chat_id=int(student), text=reply, parse_mode='HTML')
                    await asyncio.sleep(0.1)

                except TelegramForbiddenError:
                    await bot.send(message(chat_id=id4log, text='Пользователь заблокировал бота, удаляем его из бд...'))
                    remove_student(int(student))

                except Exception as e:
                    await bot.send_message(chat_id=id4log, text=f"Ошибка отправки: {e}")
                    await asyncio.sleep(0.5)



# команда /start
@dp.message(CommandStart())
async def get_start(message: Message):
    await message.answer(text="Приветствую!\n\n\n"

                              '- Для автоматического получения оповещений об изменении расписания вашего класса, нажмите кнопку <b>"Привязать"</b>\n'
                              '- Для отключения оповещений, нажмите кнопку <b>"Отвязать"</b>\n'
                              '- Для получения текущего расписания вашего класса, нажмите <b>"Получить расписание"</b>\n'
                              '- Команда для получения расписания конкретного класса: <blockquote>/get <i>класс</i></blockquote>\n'
                              '\n\n<tg-spoiler><i>При обнаружении бага просьба сообщить о нём @ahorotoru</i></tg-spoiler>',
                               parse_mode='HTML', reply_markup=inline_start)


# проверка на подписку и привязка к классу
@dp.callback_query(F.data == 'start')
async def start(callback: CallbackQuery, state: FSMContext):
    try:
        if not student_exists(callback.from_user.id):
            await state.set_state(Reg.usr_class)
            await callback.answer('')
            await callback.message.edit_text("Введите класс для автоматического получения оповещений:", reply_markup=kb_back)
        else:
            await callback.answer('')
            await callback.message.edit_text(text=f'Вы уже получаете оповещения об изменении расписании <b>{get_student_class(callback.from_user.id).upper()}</b> класса!', parse_mode='HTML', reply_markup=kb_back)

    except TelegramBadRequest:
        pass


# убираем пользователя из базы данных
@dp.callback_query(F.data == 'stop')
async def stop(callback: CallbackQuery):
    if student_exists(callback.from_user.id):
        remove_student(callback.from_user.id)
        await callback.answer('')
        await callback.message.edit_text(f'Вы успешно отключили оповещения об изменении расписания!', reply_markup=kb_back)
    else:
        await callback.answer('')
        await callback.message.edit_text(f'Вы не включили оповещения об изменении расписания!', reply_markup=kb_back)


# отправляем пользователю расписание его класса по кнопке
@dp.callback_query(F.data == 'get')
async def get_s(callback: CallbackQuery):
    if student_exists(callback.from_user.id):
        reply = find_in_sched(get=True, new=False, classes=[get_student_class(callback.from_user.id)])
        await callback.answer('')
        await callback.message.edit_text(text=reply, parse_mode='HTML', reply_markup=kb_back)
    else:
        await callback.answer('Ошибка!')
        await callback.message.edit_text(text='Вы не привязаны к какому-либо классу.', reply_markup=kb_back)


# о себе
@dp.callback_query(F.data == 'author')
async def author(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.edit_text(text='Привет! Спасибо что заглянули в моего бота, я достаточно много убил времени на него, хехе)\n\n'
                                     '<blockquote>Мой псевдоним - Хору <i>(@ahorotoru)</i></blockquote>\n\n'
                                     'Реального имени и всего остального называть не буду.\n'
                                     'Бота писал на языке python, так же есть свой гитхаб с исходным кодом бота.\n'
                                     'Очень надеюсь, что мой бот облегчит вам жизнь)\n'
                                     'И да, у меня есть свой телеграм-канал, если интересно - кнопка ниже, спасибо)', parse_mode='HTML', reply_markup=tgc)


# кнопка Назад
@dp.callback_query(F.data == 'back')
async def back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.answer('')
        await callback.message.edit_text(text="Приветствую!\n\n\n"
                                '- Для автоматического получения оповещений об изменении расписания вашего класса, нажмите кнопку <b>"Привязать"</b>\n'
                                '- Для отключения оповещений, нажмите кнопку <b>"Отвязать"</b>\n'
                                '- Для получения текущего расписания вашего класса, нажмите <b>"Получить расписание"</b>\n'
                                '- Команда для получения расписания конкретного класса: <blockquote>/get <i>класс</i></blockquote>\n'
                                '\n\n<tg-spoiler><i>При обнаружении бага просьба сообщить о нём @ahorotoru</i></tg-spoiler>',
                                parse_mode='HTML', reply_markup=inline_start)
    except TelegramBadRequest:
        pass
    except Exception as e:
        await callback.answer('Произошла ошибка!')
        await bot.send_message(chat_id=callback.from_user.id, text='Произошла ошибка, перезапустите бота командой <code>/start</code>', parse_mode='HTML')
        await bot.send_message(chat_id=id4log, text=f'Ошибка: {e}')


# добавления пользователя в базу данных
@dp.message(Reg.usr_class)
async def reg_last(message: Message, state: FSMContext):

    if student_exists(message.from_user.id):
        await message.answer(text="Вы и так уже привязаны к классу", reply_markup=kb_back)
        await state.clear()
        return

    await state.update_data(usr_class=message.text.lower().replace("a", "а"))
    class_data = await state.get_data()
    class_name = normal(class_data["usr_class"])

    if class_name in global_classes:
        add_student(student_id=message.from_user.id, class_name=class_name)
        await message.answer(text=f"Вы успешно привязались к классу <b>{class_name.upper()}</b>!", parse_mode='HTML', reply_markup=kb_back)
        await state.clear()
    else:
        await message.answer(f"Введённый класс не найден! Введите коректный класс повторно:", reply_markup=kb_back)
        await state.set_state(Reg.usr_class)


# функция получения расписания для определённого класса
@dp.message(Command("get"))
async def get_sched(message: Message, command: CommandObject):

    if command.args:
        reply = find_in_sched(get=True, new=False, classes=[normal(command.args)])
        await message.answer(text=reply, parse_mode='HTML', reply_markup=kb_back)

    elif student_exists(message.from_user.id):
        reply = find_in_sched(get=True, new=False, classes=[get_student_class(message.from_user.id)])
        await message.answer(text=reply, parse_mode='HTML', reply_markup=kb_back)
    else:
        await message.answer(text="Использование: <blockquote>/get <i>класс</i></blockquote>", parse_mode='HTML', reply_markup=kb_back)


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
            msg_id = int(args[1])

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


# кнопка для привязки после команды /start
inline_start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Привязать', callback_data='start')],
    [InlineKeyboardButton(text='Отвязать', callback_data='stop')],
    [InlineKeyboardButton(text='Получить расписание', callback_data='get')],
    [InlineKeyboardButton(text='О создателе...', callback_data='author')]
])

tgc = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='ТГК автора', url='https://t.me/horunikko')],
    [InlineKeyboardButton(text='GitHub', url='https://github.com/horunikko/sched_bot')],
    [InlineKeyboardButton(text='Назад↩️', callback_data='back')]
])

kb_back = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Назад↩️', callback_data='back')]
])
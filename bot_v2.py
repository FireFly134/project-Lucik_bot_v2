import asyncio
import json
import logging
import math
import os
import time
from datetime import datetime, timedelta
from random import randint
from typing import Any

import pandas as pd

from sqlalchemy import create_engine

import time
import pickle
from threading import Thread


from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaDocument,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import buttons
import chatterbox
from work import BD, TELEGRAM_TOKEN, stop_word

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(process)d-%(levelname)s %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

engine = create_engine(BD)  # данные для соединия с сервером

user_triger = {}


async def start(update: Update, context: CallbackContext):
    search_result = engine.execute(
        f"SELECT name0 FROM users WHERE user_id = '{str(update.effective_chat.id)}';"
    ).fetchall()
    if len(search_result) != 0:
        sms = f"Привет, {str(search_result[0][0])}"
        user(update, context, sms)
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Я тебя не помню. Давай знакомиться! Какой у тебя ник в игре?",
        )
        user_triger[update.effective_chat.id] = {
            "triger": "reg_start",
            "first": True,
            "rename": False,
        }


async def user(update, context, sms):
    if update.effective_chat.id in user_triger:
        user_triger.pop(update.effective_chat.id)
    buttons.new_button(update, context, sms)


#
# Админка
#
async def test_of_admin(user_id):
    info = pd.read_sql(
        f"SELECT user_id, text_for_clan FROM admins WHERE user_id = '{user_id}';",
        engine,
    )
    if len(info) != 0:
        return True
    else:
        return False


async def admin_menu(
    update, context
):  # Получаем инфу кто в клане и можем нажав на любого скинуть шаблонное смс
    info = pd.read_sql(
        f"SELECT user_id, name_clan FROM admins WHERE user_id = '{update.effective_chat.id}';",
        engine,
    )
    if len(info) != 0:
        keyboard = []
        show_user_clan = pd.read_sql(
            f"SELECT user_id, name0, rock0 FROM users WHERE clan = '{info.loc[0,'name_clan']}';",
            engine,
        )
        for i in range(len(show_user_clan)):
            keyboard += [
                [
                    InlineKeyboardButton(
                        f'{show_user_clan.loc[i,"name0"]}{show_user_clan.loc[i,"rock0"]}',
                        callback_data=f'send-{show_user_clan.loc[i,"user_id"]}',
                    )
                ]
            ]
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Все игроки клана:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def admin_menu2(update, context):  # Редактируем шаблон смс для отправки
    if test_of_admin(update.effective_chat.id):
        buttons.cancel_button(
            update, context, "Что будем отправлять непослушным деткам?"
        )
        user_triger[update.effective_chat.id] = {"triger": "edit_send"}


async def admin_send_msg_all_user_clan(
    update, context
):  # Отправить всем из клана СМС
    if test_of_admin(update.effective_chat.id):
        buttons.cancel_button(update, context, "Ну, погнали, что отправим?")
        user_triger[update.effective_chat.id] = {
            "triger": "send_msg_all_user_clan"
        }


async def admin_menu4(update, context):  # Удаление из клана
    info = pd.read_sql(
        f"SELECT user_id, name_clan FROM admins WHERE user_id = '{update.effective_chat.id}';",
        engine,
    )
    if len(info) != 0:
        keyboard = []
        show_user_clan = pd.read_sql(
            f"SELECT user_id, name0, rock0 FROM users WHERE clan = '{info.loc[0,'name_clan']}';",
            engine,
        )
        for i in range(len(show_user_clan)):
            keyboard += [
                [
                    InlineKeyboardButton(
                        f'{show_user_clan.loc[i,"name0"]}',
                        callback_data=f'DelPeopleClan-{show_user_clan.loc[i,"user_id"]}',
                    )
                ]
            ]
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Кто не в клане?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def chat_sms(update, context):  # Отправить смс в чат от имени бота
    if test_of_admin(update.effective_chat.id):
        buttons.cancel_button(update, context, "Что написать в чате?")
        user_triger[update.effective_chat.id] = {"triger": "send_chat"}


async def zero_pres(update, context):  # принудительное обнуление камней
    if update.message.from_user.id == 943180118:
        engine.execute(
            f"UPDATE users SET rock0 = '0', rock1 = '0', rock2 = '0',rock3 = '0',rock4 = '0';"
        )
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Обнулил!"
        )


async def help(update, context):
    search_result = engine.execute(
        f"SELECT name0 FROM users WHERE user_id = '{str(update.effective_chat.id)}';"
    ).fetchall()
    if len(search_result) != 0:
        sms = 'Напиши "Привет" чтобы проверить свой ник.\n Можешь кидать количество камней (цифрами) и спросить сколько у тебя камней.\nЗагляни в настройки пользователя, там можешь подписаться на напоминания по сбору халявной энергии или на напоминания по камням за час до смены К.З.(или отписаться)\nЕсли у тебя не один профель в игре, можешь добавить его ник и также кидать на него кол-во камней, но можно добавить не больше 5 героев!\nЕсли возникли проблемы с кнопками напиши /start (не помогло напиши мне @Menace134)'
        buttons.new_button(update, context, sms)
        info = pd.read_sql("SELECT user_id FROM admins;", engine)
        admins = list(info.user_id.values)
        if update.effective_chat.id in admins:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Для тебя, "
                + update.message.from_user.first_name
                + ", ещё есть настройки администратора.\n Там ты сможешь:\n - отправить напоминалку игроку\n"
                + "- редактировать сообщение напоминалки\n"
                + "- отправить ВСЕМ сообщение\n"
                + '- написать в "флудилку" от имени бота.\n'
                + "- убрать игрока из клана☠",
            )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Я тебя не помню. Давай знакомиться! Какой у тебя ник в игре?",
            )
            user_triger[update.effective_chat.id] = {
                "triger": "reg_start",
                "first": True,
                "rename": False,
            }


async def print_rock(update, context, info, k):  ###вывод камней
    hours = int(info.loc[0, "time_change_KZ"])
    now = datetime.now()
    time1 = timedelta(
        days=now.day, hours=now.hour, minutes=now.minute, seconds=now.second
    )
    time2 = timedelta(days=now.day, hours=hours, minutes=30, seconds=0)
    time3 = time2 - time1
    if time3.days == -1:
        time2 = timedelta(days=now.day + 1, hours=hours, minutes=30, seconds=0)
        time3 = time2 - time1
    if int(info.loc[0, f"rock{k}"]) == 0:
        sms = "Ты еще не вводил количество своих камней. Введи количество цифрами!"
    else:
        sms = (
            f"У твоего героя под ником \"{info.loc[0, f'name{k}']}\" - \"{info.loc[0, f'rock{k}']}\" камней! Осталось добить {600 - int(info.loc[0, f'rock{k}'])}. До обновления К.З. осталось "
            + str(time3)
        )
    context.bot.send_message(chat_id=update.effective_chat.id, text=sms)


async def edit(update, context, num, info, delete):
    if delete:
        callback = "delete"
        text = "Кого будем удалять?"
    else:
        callback = "edit_name"
        text = "Кого будем переименовывать?"
    keyboard = []
    for k in range(num):
        name = info.loc[0, f"name{k}"]
        keyboard += [
            [InlineKeyboardButton(str(name), callback_data=f"{callback}-{k}")]
        ]
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def edit_name(update, context, num=0):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="На какое имя будем менять?"
    )
    user_triger[update.effective_chat.id] = {
        "triger": "edit_name",
        "name_num": num,
    }


async def add_rock(update, context, sms, num):  ### Добавление камней
    try:
        info = pd.read_sql(
            f"SELECT * FROM users WHERE user_id = '{update.effective_chat.id}';",
            engine,
        )
        rock = int(info.loc[0, f"rock{num}"])
        if rock == 0 or rock < sms:
            engine.execute(
                f"UPDATE users SET rock{num} = '{sms}' WHERE user_id = '{update.effective_chat.id}';"
            )
            rock_minus = 600 - sms
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Ок, я внес изменения. Тебе осталось добить "
                + str(rock_minus),
            )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Ты меня не обманешь! В прошлый раз ты писал "
                + str(rock),
            )
    except Exception:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла какая-то ошибка. Попробуй снова!",
        )


async def time_zone(
    update, context, msg, tz
):  ###Узнаем часовой во сколько происходит смена КЗ
    try:
        user_id = update.message.from_user.id  # записываем ID с телеги
        if msg.lower() in stop_word:
            sms = "Отмена"
            buttons.setting_hero_button(update, context, sms)
            return
        else:
            if msg.isnumeric():
                if 1 <= int(msg) <= 24:
                    print(tz)
                    if tz:  # КЗ
                        engine.execute(
                            f"UPDATE users SET time_change_KZ = '{msg}' WHERE user_id = {user_id}"
                        )
                    else:  # энергия
                        engine.execute(
                            f"UPDATE users SET time_collection_energy = '{msg}' WHERE user_id = {user_id}"
                        )
                    sms = "Время умпешно установлено!\n Если Вы ошиблись или время поменяется, всегда можно изменить и тут.\n\n Для этого нажми ⚙️Настройка профиля⚙️ ---> Поменять время..."
                    if update.effective_chat.id in user_triger:
                        user_triger.pop(update.effective_chat.id)
                    buttons.edit_time_button(update, context, sms)
                else:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Введи время по москве!",
                    )
            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id, text="Вводи цифрами"
                )
    except Exception:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Возникла ошибка!Пожалуйста напиши @Menace134 об этом.",
        )
        context.bot.send_message(
            chat_id=943180118,
            text=update.message.from_user.first_name
            + " пытался изменить время...ОШИБКА",
        )


async def delete_person(
    update, context, num
):  # удаляем персонажа, смотрим сколько всего персов и смещаем их к тому который удаляем
    info = pd.read_sql(
        f"SELECT * FROM users WHERE user_id = {update.effective_chat.id};",
        engine,
    )
    """ПРИМЕР
    Удаляем имя3 всего персов 4  
    надо имя4 переместить на имя3 и вся
    
    другой пример:
    Удаляем имя2 всего персов 5  
    надо имя3 переместить на имя2, потом имя4 переместить на имя3 и имя5 переместить на имя4, и имя5 = 0
    тоже самое с камнями
    """
    delName = info.loc[0, f"name{num}"]
    num_pers = info.loc[0, "num_pers"]
    for i in range(num, num_pers):
        if i != 4:
            engine.execute(
                f"UPDATE users SET name{i} = '{info.loc[0,f'name{i+1}']}', rock{i} = '{info.loc[0,f'rock{i+1}']}' WHERE user_id = {update.effective_chat.id};"
            )
        else:
            engine.execute(
                f"UPDATE users SET name{i} = 0, rock{i} = 0 WHERE user_id = {update.effective_chat.id};"
            )
    engine.execute(
        f"UPDATE users SET num_pers = {num_pers - 1} WHERE user_id = {update.effective_chat.id};"
    )
    buttons.setting_hero_button(
        update, context, f'Герой с ником "{delName}" удален!'
    )


async def button(
    update: Update, context: CallbackContext
) -> None:  # реагирует на нажатие кнопок.
    query = update.callback_query
    query.answer()
    if "YES" in query.data:
        update.callback_query.message.delete()
        if "-" in query.data:
            list_answer = query.data.split("-")
            if len(list_answer) > 2 and list_answer[1] == "DELETE":
                num = int(list_answer[2])
                delete_person(update, context, num)
        else:
            buttons.setting_hero_button(
                update, context, "Отлично, будем знакомы)"
            )
        if update.effective_chat.id in user_triger:
            user_triger.pop(update.effective_chat.id)

    elif "NO" in query.data:
        update.callback_query.message.delete()
        if "-" in query.data:
            list_answer = query.data.split("-")
            if len(list_answer) > 2 and list_answer[1] == "DELETE":
                info = pd.read_sql(
                    f"SELECT * FROM users WHERE user_id = '{update.effective_chat.id}';",
                    engine,
                )
                num = int(info.loc[0, "num_pers"])
                edit(update, context, num, info, True)
        else:
            query.edit_message_text(
                "Ок, давай попробуем снова. Какой у тебя ник в игре?"
            )
            user_triger[update.effective_chat.id] = {
                "triger": "reg_start",
                "first": True,
                "rename": True,
            }
    elif "Add_Rock" in query.data:
        sms = str(query.data.split("-")[1])
        num = str(query.data.split("-")[2])
        add_rock(update, context, sms, num)
    elif "delete" in query.data:
        num = str(query.data.split("-")[1])
        update.callback_query.message.delete()
        info = pd.read_sql(
            f"SELECT name{num} FROM users WHERE user_id = {update.effective_chat.id};",
            engine,
        )
        keyboard = [
            [
                InlineKeyboardButton("Да", callback_data=f"YES-DELETE-{num}"),
                InlineKeyboardButton("Нет", callback_data=f"NO-DELETE-{num}"),
            ]
        ]
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Ты хочешь удалить героя под ником \"{info.loc[0,f'name{num}']}\"?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif "send" in query.data:
        pass
    elif "DelPeopleClan" in query.data:
        pass
    elif "print" in query.data:
        pass
    elif "edit_name" in query.data:
        num = int(query.data.split("-")[1])
        edit_name(update, context, num)


async def send_msg_all_user_clan(update, context, sms):
    user_id = update.effective_chat.id
    if update.message.text.lower() in stop_word:
        buttons.setting_admin_button(
            update, context, "А, ну ок... (ничего не отправил!)"
        )
        return
    else:
        admin = pd.read_sql(
            f"SELECT name_clan, name FROM admins WHERE user_id = '{user_id}';",
            engine,
        )
        if len(admin) != 0:
            id_user_clan = pd.read_sql(
                f"SELECT user_id,name0 FROM users WHERE clan = '{admin.loc[0,'name_clan']}'"
            )
            for i in range(len(id_user_clan)):
                try:
                    context.bot.send_message(
                        chat_id=id_user_clan.loc[i, "user_id"], text=sms
                    )
                except Exception:
                    name = id_user_clan.loc[i, "name0"]
                    context.bot.send_message(
                        chat_id=user_id, text=f"{name} sms не получил"
                    )
                    logging.error(
                        f"{admin.loc[i,'name']} отправил sms и {name} sms не получил"
                    )
    buttons.setting_admin_button(update, context, "Все оповещены")


async def manul_kv(update, context):  # Инструкция по КВ
    with open("help/kv1.txt", "r") as file1:
        text1 = file1.read()
    with open("help/kv2.txt", "r") as file2:
        text2 = file2.read()
    with open("help/kv.jpg", "rb") as img:
        img = img.read()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text1)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=img)
    context.bot.send_message(chat_id=update.effective_chat.id, text=text2)


async def schedule_of_clan_tasks(
    update, context
):  # Расписание клановых заданий
    with open("help/schedule_of_clan_tasks.txt", "r") as file:
        text = file.read()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def manul_aptechkam_kv(update, context):  # Гайд по аптечкам в КВ
    files = open("help/Manual_KV.doc", "rb")
    context.bot.send_document(chat_id=update.effective_chat.id, document=files)
    files.close()


async def necessary_heroes_for_events(
    update, context
):  # Необходимые герои для ивентов
    with open("help/ivent.jpg", "rb") as img:
        img = img.read()
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=img)


async def pak_and_counterpak(update, context):  # таблица паков и контропаков
    with open("help/pak_and_counterpak.jpg", "rb") as img:
        img = img.read()
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=img)


async def useful_links(update, context):  # Полезные ссылки
    with open("help/useful_links.txt", "r") as file:
        text = file.read()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


# #
# #Эти функции позволяют отслеживать время
# #
# def time_loop():
#     while True:
#         now = datetime.datetime.now()
#         if now.minute == 30 or now.minute == 0:
#             post()
#             time1 = datetime.timedelta(days=now.day,hours=now.hour,minutes=now.minute)
#             spisokI = []
#             spisokIEnergi = []
#             spisokIZero = []
#             spisokTurnir = []
#             answer = MySQL.show_all_ID('')
#             for id in answer:
#                     try:
#                         info = MySQL.show("Time_KZ, Time_energi",id[0])
#                         time6 = datetime.timedelta(days=now.day,hours=info[0][0],minutes=30)
#                         time7 = datetime.timedelta(days=now.day,hours=(info[0][0])-1,minutes=30)
#
#                         time8 = datetime.timedelta(days=now.day,hours=info[0][1],minutes=00)
#                         time9 = datetime.timedelta(days=now.day,hours=(info[0][1])+6,minutes=00)
#                         time10 = datetime.timedelta(days=now.day,hours=(info[0][1])+9,minutes=00)
#                         time11 = datetime.timedelta(days=now.day, hours=10, minutes=00)
#                         num_weekday = datetime.datetime.today().weekday()
#                         if time6 == time1:
#                             print("Оповещение КЗ")
#                             spisokIZero += [id[0]]
#                         elif time7 == time1:
#                             print("Оповещение КЗ -1ч")
#                             spisokI += [id[0]]
#                         elif time8 == time1 or time9 == time1 or time10 == time1:
#                             print("Оповещение про сбор энергии")
#                             spisokIEnergi += [id[0]]
#                         elif num_weekday == 3:
#                             if time11 == time1:
#                                 print("Оповещение турнира")
#                                 spisokTurnir += [id[0]]
#                     except Exception:
#                         name = MySQL.show("Name0",id[0])
#                         print("Error: "+name+ "У него не указано время смены КЗ.")
#
#             if spisokIZero != []:
#                 zero(spisokIZero)
#             if spisokI != []:
#                 cheek_rock(spisokI)
#             if spisokIEnergi != []:
#                 cheek_energi(spisokIEnergi)
#             if spisokTurnir != []:
#                 cheek_Turnir(spisokTurnir)
#                 print("Отправили на напоминалку Turnir " + str(spisokTurnir))
#
#             time5 = datetime.timedelta(days=now.day,hours=KZ[0]-1,minutes=30) # Оповещение про что остался час до смены КЗ.
#             time8 = datetime.timedelta(days=now.day,hours=KZ[1]-1,minutes=30) # Оповещение про что остался час до смены КЗ.
#             time9 = datetime.timedelta(days=now.day,hours=KZ[4]-1,minutes=30) # Оповещение про что остался час до смены КЗ.
#
#             if time1 == time5:
#                 bot.send_message(Chat[0],"До смены кланового задания остался час! Если остались хвосты, подтягивай!🤖")
#                 bot.send_message(Chat[2],"До смены кланового задания остался час! Если остались хвосты, подтягивай!🤖")
#                 bot.send_message(Chat[3],"До смены кланового задания остался час! Если остались хвосты, подтягивай!🤖")
#                 print("Оповещение произошло в 17:30 по мск!")
#
#             if time1 == time8:
#                 bot.send_message(Chat[1],"До смены кланового задания остался час! Если остались хвосты, подтягивай!🤖")
#                 bot.send_message(Chat[5],"До смены кланового задания остался час! Если остались хвосты, подтягивай!🤖")
#                 print("Оповещение произошло в 18:30 по мск!")
#
#             if time1 == time9:
#                 bot.send_message(Chat[4],"До смены кланового задания остался час! Если остались хвосты, подтягивай!🤖")
#                 print("Оповещение произошло в 16:30 по мск!")
#         time.sleep(60)#Уходим подримать на минутку


########################################################################################################################
########################################################################################################################
########################################################################################################################
############################################################################################################
############################################################################################################
############################################################################################################
async def handle_text(update, context):
    try:
        user_id = update.message.from_user.id  # записываем ID с телеги
        msg = update.message.text
        msg_id = update.message.message_id
        if msg.lower() in stop_word:
            user(update, context, sms="Ок, отмена! Идем в главное меню.")
        if update.effective_chat.id in user_triger:
            triger = user_triger[update.effective_chat.id]["triger"]
            if msg.lower() in stop_word:
                user(update, context, sms="Ок, отмена! Идем в главное меню.")
            if triger == "reg_start":
                if msg.lower() != "/help":
                    name = msg  # после вопроса как звать записываем имя
                    if user_triger[update.effective_chat.id]["first"]:
                        if user_triger[update.effective_chat.id]["rename"]:
                            engine.execute(
                                f"UPDATE users SET name0 = '{name}' WHERE user_id = '{user_id}';"
                            )
                        else:
                            engine.execute(
                                f"INSERT INTO users(user_id, name0) VALUES('{user_id}', '{name}');"
                            )
                    else:
                        info = pd.read_sql(
                            f"SELECT num_pers FROM users WHERE user_id = '{user_id}';",
                            engine,
                        )
                        num_pers = int(info.loc[0, "num_pers"])
                        engine.execute(
                            f"UPDATE users SET name{num_pers-1} = '{name}', num_pers = '{num_pers+1}' WHERE user_id = '{user_id}';"
                        )
                    keyboard = [
                        [
                            InlineKeyboardButton("Да", callback_data="YES"),
                            InlineKeyboardButton("Нет", callback_data="NO"),
                        ]
                    ]
                    context.bot.send_message(
                        chat_id=user_id,
                        text='Ты герой под ником "' + name + '"?',
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
            elif triger == "edit_name":
                name = msg  # после вопроса как звать записываем имя
                num = user_triger[update.effective_chat.id]["name_num"]
                info = pd.read_sql(
                    f"SELECT user_id FROM users WHERE user_id = {user_id};",
                    engine,
                )
                if len(info) != 0:
                    engine.execute(
                        f"UPDATE users SET name{num} = '{name}' WHERE user_id = {user_id}"
                    )
                    sms = 'теперь тебя зовут: "' + name + '"!'
                    context.bot.send_message(chat_id=user_id, text=sms)
            elif triger == "edit_send":
                if msg.lower() in stop_word:
                    buttons.setting_admin_button(update, context, "Отмена")
                    return
                else:
                    buttons.setting_admin_button(update, context, "Сохранил")
                    engine.execute(
                        f"UPDATE admins SET text_for_clan = '{msg}' WHERE user_id = {user_id}"
                    )
            elif triger == "send_msg_all_user_clan":
                send_msg_all_user_clan(update, context, msg)
            elif triger == "send_chat":
                admin = pd.read_sql(
                    f"SELECT name_clan, name FROM admins WHERE user_id = '{user_id}';",
                    engine,
                )
                clan_id = pd.read_sql(
                    f"SELECT clan_id FROM clan_id WHERE name_clan = '{admin.loc[0, 'name_clan']}';",
                    engine,
                )
                try:
                    if msg.lower() in stop_word:
                        buttons.new_button(update, context, "Отмена")
                        return
                    else:
                        context.bot.send_message(
                            chat_id=clan_id.loc[0, "clan_id"], text=msg
                        )
                        buttons.new_button(update, context, "Отправлено!")
                except Exception:
                    print(
                        f"{admin.loc[0,'name']} отправил sms в чат, но произошла ошибка!"
                    )
                    buttons.new_button(
                        update,
                        context,
                        "В чат sms не ушло...хз почему, ошибка!",
                    )
            elif triger == "time_zone":
                time_zone(
                    update,
                    context,
                    msg,
                    user_triger[update.effective_chat.id]["tz"],
                )
            if user_id in user_triger:
                user_triger.pop(user_id)

        ############################################################################################################
        ############################################################################################################
        ############################################################################################################
        else:
            if (msg.isnumeric() and update.message.chat.type == "private") or (
                "люцик добавь" in msg.lower()
                and (
                    update.message.chat.type == "supergroup"
                    or update.message.chat.type == "group"
                )
            ):
                if update.message.chat.type == "supergroup":
                    if msg[13:].isnumeric():
                        sms = msg[13:]
                        context.bot.send_message(
                            chat_id=update.message.chat.id,
                            text="Глянь в личку...",
                        )
                    else:
                        context.bot.send_message(
                            chat_id=update.message.chat.id,
                            text='Ты что, хочешь меня обмануть? Мне нужны цифры! \n(напиши повторно, на пример: "Люцик добавь 400")',
                        )
                        return
                else:
                    sms = msg
                if 0 <= int(sms) <= 600:
                    info = pd.read_sql(
                        f"SELECT * FROM users WHERE user_id = '{update.effective_chat.id}';",
                        engine,
                    )
                    num = int(info.loc[0, "num_pers"])
                    keyboard = []
                    if num >= 2:
                        for k in range(num):
                            keyboard += [
                                [
                                    InlineKeyboardButton(
                                        str(info.loc[0, f"name{k}"]),
                                        callback_data=f"Add_Rock-{sms}-{k}",
                                    )
                                ]
                            ]
                    else:
                        add_rock(
                            update, context, int(sms), 0
                        )  # передаем для записи камней
                else:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Ты что, хочешь меня обмануть? Проверь сколько у тебя камней!",
                    )
            elif (
                ("Сколько у меня камней?" in msg)
                or ("сколько" in msg.lower())
                and update.message.chat.type == "private"
            ):  # or ("люц" in update.message.text.lower() and ("камн" in update.message.text.lower() or "сколько" in update.message.text.lower())  and (update.message.chat.type == "supergroup" or update.message.chat.type == "group")):
                info = pd.read_sql(
                    f"SELECT * FROM users WHERE user_id = '{update.effective_chat.id}';",
                    engine,
                )
                num = int(info.loc[0, "num_pers"])
                keyboard = []
                if num >= 2:
                    for k in range(num):
                        keyboard += [
                            [
                                InlineKeyboardButton(
                                    str(info.loc[0, f"name{k}"]),
                                    callback_data=f"print-{k}-{user_id}",
                                )
                            ]
                        ]
                    context.bot.send_message(
                        chat_id=user_id,
                        text="Кто тебя интересует?",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                else:
                    print_rock(update, context, info, 0)
            elif (
                "прив" in msg.lower() and update.message.chat.type == "private"
            ) or (
                (
                    "люц" in msg.lower()
                    or "всем" in msg.lower()
                    or "доброе" in msg.lower()
                )
                and (
                    "прив" in msg.lower()
                    or "ку" in msg.lower()
                    or "здаров" in msg.lower()
                    or "утр" in msg.lower()
                )
                and (
                    update.message.chat.type == "supergroup"
                    or update.message.chat.type == "group"
                )
            ):

                info = pd.read_sql(
                    f"SELECT * FROM users WHERE user_id = '{update.message.from_user.id}';",
                    engine,
                )
                if len(info) != 0:
                    name = str(info.loc[0, "name0"])
                else:
                    name = update.message.from_user.first_name
                rand_num = randint(1, 5)
                if rand_num == 1:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Привет, " + name + "!",
                        reply_to_message_id=msg_id,
                    )
                elif rand_num == 2:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Привет, "
                        + name
                        + ", как твои дела?.. Хотя, знаешь,не отвечай... и так знаю что хорошо.",
                        reply_to_message_id=msg_id,
                    )
                elif rand_num == 3:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Ку, " + name,
                        reply_to_message_id=msg_id,
                    )
                elif rand_num == 4:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Привет, "
                        + name
                        + ", ты уже набил 600 камней? Если нет, иди и не возвращайся пока не набьешь!",
                        reply_to_message_id=msg_id,
                    )
                elif rand_num == 5:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Ну привет, " + name + ", если не здоровались",
                        reply_to_message_id=msg_id,
                    )
            elif (
                "люц" in msg.lower() and "рейд" in msg.lower()
            ):  # and (update.message.chat.type == "supergroup" or update.message.chat.type == "group")
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Сейчас!",
                    reply_to_message_id=msg_id,
                )
                sms = "Рейд открыт заходим согласно купленным билетам!"
                # send_msg_all_user_clan(update, context, sms)
                if (
                    "что" in msg.lower()
                    or "чё" in msg.lower()
                    or "чо" in msg.lower()
                    or "че" in msg.lower()
                ):
                    rand_num = 4
                else:
                    rand_num = randint(1, 3)
                if rand_num == 1:
                    context.bot.send_message(
                        chat_id=update.message.chat.id,
                        text="Ану быстро в рейд! Кто последний тот ЛОХ!)",
                    )
                    sticker = open("AnimatedSticker.tgs", "rb")
                    context.bot.send_sticker(
                        chat_id=update.message.chat.id, sticker=sticker
                    )
                elif rand_num == 2:
                    context.bot.send_message(
                        chat_id=update.message.chat.id,
                        text="Рейд открыт заходим согласно купленным билетам",
                    )
                    sticker = open("sticker.webp", "rb")
                    context.bot.send_sticker(
                        chat_id=update.message.chat.id, sticker=sticker
                    )
                elif rand_num == 3:
                    context.bot.send_message(
                        chat_id=update.message.chat.id,
                        text="Не вижу ваших жопок на рейде!!! БЫСТРО В РЕЙД!",
                    )
                elif rand_num == 4:
                    context.bot.send_message(
                        chat_id=update.message.chat.id,
                        text="Не знаю как, но нужно закрыть рейд на 100%!",
                    )
                    video = open("frog.mp4", "rb")
                    context.bot.send_video(
                        chat_id=update.message.chat.id, video=video
                    )
            elif (
                "открыт" in msg.lower()
                and "рейд" in msg.lower()
                and (
                    update.message.chat.type == "supergroup"
                    or update.message.chat.type == "group"
                )
            ):
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="В атакууууу... =)",
                    reply_to_message_id=msg_id,
                )
                sms = "Рейд открыт заходим согласно купленным билетам!"
                send_msg_all_user_clan(update, context, sms)
                video = open("video_2021-05-03_21-58-18.mp4", "rb")
                context.bot.send_video(
                    chat_id=update.message.chat.id, video=video
                )
            elif "Помощь" in msg:
                buttons.helpMy_button(
                    update, context, "Вот, листай список, выбирай!"
                )
            elif "Полезная информация" == msg:
                buttons.help_button(
                    update, context, "Вот, листай список, выбирай!"
                )
            elif "Отправить напоминалку игроку" in msg:
                admin_menu(update, context)
            elif "Отправить ВСЕМ сообщение" in msg:
                admin_send_msg_all_user_clan(update, context)
            elif "Редактировать сообщение напоминалки" in msg:
                admin_menu2(update, context)
            # elif "убрать кнопки" in update.message.text.lower():
            #     clear_button(update, context)
            elif "Добавить еще одного героя" in msg:
                info = pd.read_sql(
                    f"SELECT * FROM users WHERE user_id = '{update.effective_chat.id}';",
                    engine,
                )
                num = int(info.loc[0, "num_pers"])
                if num <= 4:
                    buttons.cancel_button(
                        update, context, "Какой у тебя ник в игре?"
                    )
                    user_triger[update.effective_chat.id] = {
                        "triger": "reg_start",
                        "first": False,
                        "rename": False,
                    }
                else:
                    context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Лимит добавления персонажей привышен!",
                    )
            elif "Удалить одного героя" in msg or "Переименовать героя" in msg:
                info = pd.read_sql(
                    f"SELECT * FROM users WHERE user_id = '{update.effective_chat.id}';",
                    engine,
                )
                num = int(info.loc[0, "num_pers"])
                if num >= 2:
                    if "Переименовать героя" in msg:
                        delete = False
                    else:
                        delete = True
                    edit(update, context, num, info, delete)
                else:
                    if "Переименовать героя" in msg:
                        edit_name(update, context)
                    else:
                        context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="У тебя остался только 1 герой!",
                        )
            elif "Написать от имени бота🤖" == msg:
                chat_sms(update, context)
            elif "Подписаться на напоминалку по камням" == msg:
                engine.execute(
                    f"UPDATE users SET subscription_rock = 'True' WHERE user_id = {user_id}"
                )
                buttons.setting_button(
                    update,
                    context,
                    "Если у вас будет меньше 600 камней, я вам напобню об этом за час до смены КЗ.",
                )
            elif "Отписаться от напоминалки по камням" == msg:
                engine.execute(
                    f"UPDATE users SET subscription_rock = 'False' WHERE user_id = {user_id}"
                )
                buttons.setting_button(
                    update,
                    context,
                    "Хорошо, больше не буду вам напоминать про камни... Автоматически.",
                )
            elif "Подписаться на напоминалку по сбору энергии" == msg:
                engine.execute(
                    f"UPDATE users SET subscription_energy = 'True' WHERE user_id = {user_id}"
                )
                buttons.setting_button(
                    update,
                    context,
                    "Теперь я буду напоминать Вам про энергию.",
                )
            elif "Отписаться от напоминалки по сбору энергии" == msg:
                engine.execute(
                    f"UPDATE users SET subscription_energy = 'False' WHERE user_id = {user_id}"
                )
                buttons.setting_button(
                    update,
                    context,
                    "Хорошо, больше не буду вам напоминать про энергию...",
                )
            elif "⚙️Настройка профиля⚙️" == msg:
                buttons.setting_button(update, context, "Что будем изменять?")
            elif "🔙Назад🔙" == msg:
                buttons.new_button(
                    update, context, "Погнали, назад, в главное меню."
                )
            elif "Настройки Админа" == msg:
                if test_of_admin(user_id):
                    buttons.setting_admin_button(
                        update,
                        context,
                        "Для тебя, "
                        + update.message.from_user.first_name
                        + ", ещё есть такие команды",
                    )
            elif "Убрать игрока из клана☠" == msg:
                admin_menu4(update, context)
            elif "Проверить данные профиля" == msg:
                info = pd.read_sql(
                    f"SELECT * FROM users WHERE user_id = '{update.effective_chat.id}';",
                    engine,
                )
                clan = f"Ты в клане \"{info.loc[0, 'clan']}\""
                smena_KZ = str(
                    info.loc[0, "time_change_kz"]
                )  # считываем смену кз
                sbor_energi = str(
                    info.loc[0, "time_collection_energy"]
                )  # считываем сбор энергии

                if info.loc[0, "subscription_rock"]:
                    subscription_Rock_text = (
                        "Вы подписаны на оповещение по камням."
                    )
                else:
                    subscription_Rock_text = (
                        "Вы не подписаны на оповещение по камням."
                    )
                if info.loc[0, "subscription_energy"]:
                    subscription_Energi_text = (
                        "Вы подписаны на оповещение по сбору энергии."
                    )
                else:
                    subscription_Energi_text = (
                        "Вы не подписаны на оповещение по сбору энергии."
                    )
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Твой ник в игре: {info.loc[0,'name0']}\n"
                    f"{subscription_Rock_text}\n"
                    f"{subscription_Energi_text}\n"
                    f"Время смены КЗ: {smena_KZ}:30 по мск \n"
                    f"Время сбора первой энергии: {sbor_energi}:00 по мск\n"
                    f"{clan}",
                )
            elif "Поменять время смены КЗ" == msg:
                buttons.cancel_button(
                    update,
                    context,
                    'Во сколько по москве смена КЗ? Вводи только час.\n Пример: "18"',
                )
                user_triger[update.effective_chat.id] = {
                    "triger": "time_zone",
                    "tz": True,
                }
            elif "Поменять время первого сбора энергии" == msg:
                buttons.cancel_button(
                    update,
                    context,
                    'Во сколько по москве первый сбор энергии (синька и фиолетка)? Вводи только час.\n Пример: "12"',
                )
                user_triger[update.effective_chat.id] = {
                    "triger": "time_zone",
                    "tz": False,
                }
            elif "Инструкция по применению" == msg:
                with open("help/Instructions_for_use.txt", "r") as file:
                    text = file.read()
                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=text
                )
            elif "Инструкция для подключения меня к чату" == msg:
                with open(
                    "help/Instructions_for_implementing_the_bot_in_the_chat.txt",
                    "r",
                ) as file:
                    text = file.read()
                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=text
                )
            elif "Основные команды в чате" == msg or (
                "люц" in msg.lower()
                and (
                    "команды" in msg.lower()
                    or (
                        (
                            "что" in msg.lower()
                            or "че" in msg.lower()
                            or "чё" in msg.lower()
                            or "чо" in msg.lower()
                        )
                        and "умеешь" in msg.lower()
                    )
                )
            ):
                with open("help/Basic_commands_in_the_chat.txt", "r") as file:
                    text = file.read()
                context.bot.send_message(
                    chat_id=update.effective_chat.id, text=text
                )
            elif "Инструкция по КВ" == msg:
                manul_kv(update, context)
            elif "Расписание клановых заданий" == msg:
                schedule_of_clan_tasks(update, context)
            elif "Полезные ссылки" == msg:
                useful_links(update, context)
            elif "Гайд по аптечкам в КВ" == msg:
                manul_aptechkam_kv(update, context)
            elif "Необходимые герои для ивентов" == msg:
                necessary_heroes_for_events(update, context)
            elif "Маницпуляции с героем" == msg:
                buttons.setting_hero_button(
                    update,
                    context,
                    "Тут ты можешь добавить или удалить героя, ну и при необходимости переименовать его",
                )
            elif "Подписки..." == msg:
                buttons.Subscription_button(update, context, "Смотри...")
            elif "Поменять время..." == msg:
                buttons.edit_time_button(update, context, "Меняй...")
            else:
                chatterbox.get_chat_text_messages(update, context)
    except Exception:
        pass


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    # потключаемся к управлению ботом по токену
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # simple start function
    application.add_handler(CommandHandler("start", start))

    # Add command handler to start the payment invoice
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("zero", zero_pres))
    application.add_handler(CommandHandler("manul_kv", manul_kv))
    application.add_handler(
        CommandHandler("clan_tasks", schedule_of_clan_tasks)
    )
    application.add_handler(CommandHandler("useful_links", useful_links))
    application.add_handler(
        CommandHandler("pak_and_counterpak", pak_and_counterpak)
    )
    application.add_handler(
        CommandHandler("heroes_for_events", necessary_heroes_for_events)
    )
    application.add_handler(CommandHandler("manul_ap_kv", manul_aptechkam_kv))

    # Add callback query handler to start the payment invoice
    application.add_handler(CallbackQueryHandler(button))

    application.add_handler(MessageHandler(filters.ALL, handle_text))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

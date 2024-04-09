import random
import buttons
import chatterbox
import logging
from datetime import datetime, timedelta
from random import randint
from typing import Any

import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy import text as sql_text

from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from admin_functions import (
    check_of_admin,
    admin_menu,
    admin_menu2,
    admin_menu4,
    admin_send_msg_all_user_clan,
    chat_sms,
)

from work import (
    TELEGRAM_TOKEN,
    stop_word,
    url_engine,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(process)d-%(levelname)s %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

engine = create_engine(url_engine)
user_triger = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.effective_chat and context:
        if update.message.chat:
            if update.message.chat.type == "private":
                search_result = pd.read_sql(
                    "SELECT name0 FROM users WHERE user_id = :user_id;",
                    params={"user_id": update.effective_chat.id},
                    con=engine,
                )
                if not search_result.empty:
                    sms = f"Привет, {str(search_result['name0'].values[0])}"
                    user(update, context, sms)
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Я тебя не помню. Давай знакомиться! "
                        "Какой у тебя ник в игре?",
                    )
                    user_triger[update.effective_chat.id] = {
                        "triger": "reg_start",
                        "first": True,
                        "rename": False,
                    }


async def user(
    update: Update, context: ContextTypes.DEFAULT_TYPE, sms: str
) -> None:
    if update.effective_chat and context:
        if update.effective_chat.id in user_triger:
            user_triger.pop(update.effective_chat.id)
        buttons.new_button(update, context, sms)


async def zero_pres(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """принудительное обнуление камней"""
    if update.message.from_user.id == 943180118:
        engine.execute(
            f"UPDATE users SET rock0 = '0', rock1 = '0', rock2 = '0',rock3 = '0',rock4 = '0';"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Обнулил!"
        )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    search_result = engine.execute(
        f"SELECT name0 FROM users WHERE user_id = '{str(update.effective_chat.id)}';"
    ).fetchall()
    if len(search_result) != 0:
        sms = 'Напиши "Привет" чтобы проверить свой ник.\n Можешь кидать количество камней (цифрами) и спросить сколько у тебя камней.\nЗагляни в настройки пользователя, там можешь подписаться на напоминания по сбору халявной энергии или на напоминания по камням за час до смены К.З.(или отписаться)\nЕсли у тебя не один профель в игре, можешь добавить его ник и также кидать на него кол-во камней, но можно добавить не больше 5 героев!\nЕсли возникли проблемы с кнопками напиши /start (не помогло напиши мне @Menace134)'
        buttons.new_button(update, context, sms)
        info = pd.read_sql("SELECT user_id FROM admins;", engine)
        admins = list(info.user_id.values)
        if update.effective_chat.id in admins:
            await context.bot.send_message(
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
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Я тебя не помню. Давай знакомиться! Какой у тебя ник в игре?",
            )
            user_triger[update.effective_chat.id] = {
                "triger": "reg_start",
                "first": True,
                "rename": False,
            }


async def print_rock(
    update: Update, context: ContextTypes.DEFAULT_TYPE, info, k
) -> None:
    """вывод камней"""
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
        sms = (
            "Ты еще не вводил количество своих камней. "
            "Введи количество цифрами!"
        )
    else:
        sms = (
            f"У твоего героя под ником \"{info.loc[0, f'name{k}']}\" - \"{info.loc[0, f'rock{k}']}\" камней! Осталось добить {600 - int(info.loc[0, f'rock{k}'])}. До обновления К.З. осталось "
            + str(time3)
        )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=sms)


async def edit(
    update: Update, context: ContextTypes.DEFAULT_TYPE, num, info, delete
):
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
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE, num=0):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="На какое имя будем менять?"
    )
    user_triger[update.effective_chat.id] = {
        "triger": "edit_name",
        "name_num": num,
    }


async def add_rock(
    update: Update, context: ContextTypes.DEFAULT_TYPE, sms, num
):  ### Добавление камней
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
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Ок, я внес изменения. Тебе осталось добить "
                + str(rock_minus),
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Ты меня не обманешь! В прошлый раз ты писал "
                + str(rock),
            )
    except Exception:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла какая-то ошибка. Попробуй снова!",
        )


async def time_zone(
    update: Update, context: ContextTypes.DEFAULT_TYPE, msg, tz
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
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Введи время по москве!",
                    )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text="Вводи цифрами"
                )
    except Exception:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Возникла ошибка!Пожалуйста напиши @Menace134 об этом.",
        )
        await context.bot.send_message(
            chat_id=943180118,
            text=update.message.from_user.first_name
            + " пытался изменить время...ОШИБКА",
        )


async def delete_person(
    update: Update, context: ContextTypes.DEFAULT_TYPE, num
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
        await context.bot.send_message(
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


async def send_msg_all_user_clan(
    update: Update, context: ContextTypes.DEFAULT_TYPE, sms
):
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
                    await context.bot.send_message(
                        chat_id=id_user_clan.loc[i, "user_id"], text=sms
                    )
                except Exception:
                    name = id_user_clan.loc[i, "name0"]
                    await context.bot.send_message(
                        chat_id=user_id, text=f"{name} sms не получил"
                    )
                    logging.error(
                        f"{admin.loc[i,'name']} отправил sms и {name} sms не получил"
                    )
    buttons.setting_admin_button(update, context, "Все оповещены")


async def manul_kv(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):  # Инструкция по КВ
    with open("help/kv1.txt", "r") as file1:
        text1 = file1.read()
    with open("help/kv2.txt", "r") as file2:
        text2 = file2.read()
    with open("help/kv.jpg", "rb") as img:
        img = img.read()
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text1
    )
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text2
    )


async def schedule_of_clan_tasks(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):  # Расписание клановых заданий
    with open("help/schedule_of_clan_tasks.txt", "r") as file:
        text = file.read()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def manul_aptechkam_kv(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Гайд по аптечкам в КВ"""
    with open("help/Manual_KV.doc", "rb") as files:
        await context.bot.send_document(
            chat_id=update.effective_chat.id, document=files
        )
    return


async def necessary_heroes_for_events(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):  # Необходимые герои для ивентов
    with open("help/ivent.jpg", "rb") as img:
        img = img.read()
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img)


async def pak_and_counterpak(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):  # таблица паков и контропаков
    with open("help/pak_and_counterpak.jpg", "rb") as img:
        img = img.read()
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=img)


async def useful_links(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Полезные ссылки"""
    with open("help/useful_links.txt", "r") as file:
        text = file.read()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    return


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                    await context.bot.send_message(
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
                    await context.bot.send_message(chat_id=user_id, text=sms)
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
                        await context.bot.send_message(
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
                        await context.bot.send_message(
                            chat_id=update.message.chat.id,
                            text="Глянь в личку...",
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=update.message.chat.id,
                            text="Ты что, хочешь меня обмануть? Мне нужны "
                            "цифры! \n(напиши повторно, на пример: "
                            '"Люцик добавь 400")',
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
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Ты что, хочешь меня обмануть? Проверь сколько у "
                        "тебя камней!",
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
                    await context.bot.send_message(
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
                if not info.empty:
                    name = str(info["name0"].values[0])
                else:
                    name = update.message.from_user.first_name
                rand_num = random.randint(1, 5)
                if rand_num == 1:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Привет, {name}!",
                        reply_to_message_id=msg_id,
                    )
                elif rand_num == 2:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Привет, {name}, как твои дела?.. Хотя, знаешь,"
                        "не отвечай... и так знаю что хорошо.",
                        reply_to_message_id=msg_id,
                    )
                elif rand_num == 3:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Ку, {name}",
                        reply_to_message_id=msg_id,
                    )
                elif rand_num == 4:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Привет, {name}, ты уже набил 600 камней? "
                        "Если нет, иди и не возвращайся пока не набьешь!",
                        reply_to_message_id=msg_id,
                    )
                elif rand_num == 5:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=f"Ну привет, {name}, если не здоровались",
                        reply_to_message_id=msg_id,
                    )
            elif (
                "люц" in msg.lower() and "рейд" in msg.lower()
            ):  # and (update.message.chat.type == "supergroup" or update.message.chat.type == "group")
                await context.bot.send_message(
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
                    rand_num = random.randint(1, 3)
                if rand_num == 1:
                    await context.bot.send_message(
                        chat_id=update.message.chat.id,
                        text="Ану быстро в рейд! Кто последний тот ЛОХ!)",
                    )
                    with open("AnimatedSticker.tgs", "rb") as sticker:
                        await context.bot.send_sticker(
                            chat_id=update.message.chat.id, sticker=sticker
                        )
                elif rand_num == 2:
                    await context.bot.send_message(
                        chat_id=update.message.chat.id,
                        text="Рейд открыт заходим согласно купленным билетам",
                    )
                    with open("sticker.webp", "rb") as sticker:
                        await context.bot.send_sticker(
                            chat_id=update.message.chat.id, sticker=sticker
                        )
                elif rand_num == 3:
                    await context.bot.send_message(
                        chat_id=update.message.chat.id,
                        text="Не вижу ваших жопок на рейде!!! БЫСТРО В РЕЙД!",
                    )
                elif rand_num == 4:
                    await context.bot.send_message(
                        chat_id=update.message.chat.id,
                        text="Не знаю как, но нужно закрыть рейд на 100%!",
                    )
                    with open("frog.mp4", "rb") as video:
                        await context.bot.send_video(
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
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="В атакууууу... =)",
                    reply_to_message_id=msg_id,
                )
                sms = "Рейд открыт заходим согласно купленным билетам!"
                send_msg_all_user_clan(update, context, sms)
                with open("video_2021-05-03_21-58-18.mp4", "rb") as video:
                    await context.bot.send_video(
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
                    await context.bot.send_message(
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
                        await context.bot.send_message(
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
                    "Если у вас будет меньше 600 камней, я вам напобню об "
                    "этом за час до смены КЗ.",
                )
            elif "Отписаться от напоминалки по камням" == msg:
                engine.execute(
                    f"UPDATE users SET subscription_rock = 'False' WHERE user_id = {user_id}"
                )
                buttons.setting_button(
                    update,
                    context,
                    "Хорошо, больше не буду вам напоминать про камни... "
                    "Автоматически.",
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
                if check_of_admin(user_id):
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
                    "SELECT * FROM users " "WHERE user_id = %(user_id)s;",
                    params={"user_id": update.effective_chat.id},
                    con=engine,
                )
                clan = f"Ты в клане \"{info.loc[0, 'clan']}\""
                smena_kz = str(
                    info.loc[0, "time_change_kz"]
                )  # считываем смену кз
                sbor_energi = str(
                    info.loc[0, "time_collection_energy"]
                )  # считываем сбор энергии

                if info.loc[0, "subscription_rock"]:
                    subscription_rock_text = (
                        "Вы подписаны на оповещение по камням."
                    )
                else:
                    subscription_rock_text = (
                        "Вы не подписаны на оповещение по камням."
                    )
                if info.loc[0, "subscription_energy"]:
                    subscription_energi_text = (
                        "Вы подписаны на оповещение по сбору энергии."
                    )
                else:
                    subscription_energi_text = (
                        "Вы не подписаны на оповещение по сбору энергии."
                    )
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Твой ник в игре: {info.loc[0,'name0']}\n"
                    f"{subscription_rock_text}\n"
                    f"{subscription_energi_text}\n"
                    f"Время смены КЗ: {smena_kz}:30 по мск \n"
                    f"Время сбора первой энергии: {sbor_energi}:00 по мск\n"
                    f"{clan}",
                )
            elif "Поменять время смены КЗ" == msg:
                buttons.cancel_button(
                    update,
                    context,
                    "Во сколько по москве смена КЗ? Вводи только час.\n "
                    'Пример: "18"',
                )
                user_triger[update.effective_chat.id] = {
                    "triger": "time_zone",
                    "tz": True,
                }
            elif "Поменять время первого сбора энергии" == msg:
                buttons.cancel_button(
                    update,
                    context,
                    "Во сколько по москве первый сбор энергии (синька и "
                    'фиолетка)? Вводи только час.\n Пример: "12"',
                )
                user_triger[update.effective_chat.id] = {
                    "triger": "time_zone",
                    "tz": False,
                }
            elif "Инструкция по применению" == msg:
                with open("help/Instructions_for_use.txt", "r") as file:
                    text = file.read()
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text=text
                )
            elif "Инструкция для подключения меня к чату" == msg:
                with open(
                    "help/Instructions_for_implementing_the_bot_in_the_chat."
                    "txt",
                    "r",
                ) as file:
                    text = file.read()
                await context.bot.send_message(
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
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text=text
                )
            elif "Инструкция по КВ" == msg:
                await manul_kv(update, context)
            elif "Расписание клановых заданий" == msg:
                await schedule_of_clan_tasks(update, context)
            elif "Полезные ссылки" == msg:
                await useful_links(update, context)
            elif "Гайд по аптечкам в КВ" == msg:
                await manul_aptechkam_kv(update, context)
            elif "Необходимые герои для ивентов" == msg:
                await necessary_heroes_for_events(update, context)
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
    except Exception as err:
        logging.error(f'В "handle_text" возникла ошибка - {err}')


# В случае если еа вопрос ответ -"НЕТ" то слудующий вопрос почему нет? и переходим сюда, ждем написания ответа и затем сохраняем его.


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    # потключаемся к управлению ботом по токену
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # simple start function
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("zero_pres", zero_pres))
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

import random
from buttons import (
    help_button,
    help_my_button,
    new_button,
    cancel_button,
    edit_time_button,
    setting_button,
    setting_hero_button,
    subscription_button,
)
import chatterbox
import logging
from datetime import datetime, timedelta

import pandas as pd

from sqlalchemy import create_engine

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

from send_query_sql import insert_and_update_sql

from work import (
    TELEGRAM_TOKEN,
    stop_word,
    url_engine,
    my_tid,
    working_folder,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(process)d-%(levelname)s %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

engine = create_engine(url_engine)

user_triger = {}
group_triger = {}


class UserData:
    def __init__(self) -> None:
        self._dict: dict[int, dict[str, str]] = dict()
        return

    @property
    def data(self) -> dict[int, dict[str, str]]:
        return self._dict

    def update(self, user_id: int, data: dict[str, str]) -> None:
        if user_id not in self._dict:
            self._dict.update({user_id: {}})
        self._dict[user_id].update(data)
        return

    def delete(self, user_id: int) -> None:
        if user_id in self._dict:
            self._dict.pop(user_id)
        return


async def get_type_msg(update: Update) -> str:
    if "edited_message" in str(update):
        type_msg: str = "edited_message"
    else:
        type_msg = "message"
    return type_msg


async def chat_type(update: Update) -> str:
    type_msg = await get_type_msg(update)
    return update[type_msg].chat.type


async def get_user_id(update: Update) -> int:
    user_id: int = 0
    type_msg = await get_type_msg(update)
    if update[type_msg] or update.effective_chat:
        if update.message.from_user:
            user_id = update[type_msg].from_user.id
        else:
            user_id = update.effective_chat.id
    return user_id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.effective_chat and context:
        user_id = await get_user_id(update)
        if update.message.chat:
            if update.message.chat.type == "private":
                user_search = pd.read_sql(
                    "SELECT name FROM heroes_of_users "
                    "WHERE user_id = %(user_id)s;",
                    params={"user_id": user_id},
                    con=engine,
                )
                if not user_search.empty:
                    sms = f'Привет, {str(user_search.loc[0,"name"])}'
                    await user(update, context, sms)
                else:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="Я тебя не помню. Давай знакомиться! "
                        "Какой у тебя ник в игре?",
                    )
                    user_triger[user_id] = {
                        "triger": "reg_start",
                        "first": True,
                        "rename": False,
                    }
            else:
                user_search = pd.read_sql(
                    "SELECT name_clan, start FROM clans "
                    "WHERE user_id = %(user_id)s;",
                    params={"user_id": user_id},
                    con=engine,
                )
                if not user_search.empty:
                    if user_search.loc[0, "start"] == 1:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"Привет, {user_search.loc[0,'name_clan']}!",
                        )
                    else:
                        await insert_and_update_sql(
                            "UPDATE clans SET start = '1' "
                            "WHERE chat_id = :chat_id;",
                            params={"chat_id": update.effective_chat.id},
                        )
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f"""Привет, {user_search.loc[0, 'name_clan']}!
Я снова с вами!😈""",
                        )
                else:
                    await insert_and_update_sql(
                        "INSERT INTO clans(chat_id, name_clan) "
                        "VALUES(:chat_id, :name_clan);",
                        params={
                            "chat_id": update.effective_chat.id,
                            "name_clan": update.effective_chat.title,
                        },
                    )

                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Привет, меня зовут Люцик!",
                    )
    return


async def stop(update: Update, context: CallbackContext) -> None:
    if context:
        user_id = await get_user_id(update)
        if chat_type(update) != "private":
            user_search = pd.read_sql(
                "SELECT name_clan, start FROM clans "
                "WHERE user_id = %(user_id)s;",
                params={"user_id": user_id},
                con=engine,
            )
            if not user_search.empty:
                if user_search.loc[0, "start"] == 0:
                    await context.bot.send_message(
                        chat_id=user_id, text=f"А что я? Я молчу!☹️"
                    )
                else:
                    await insert_and_update_sql(
                        "UPDATE clans SET start = '0' "
                        "WHERE chat_id = :chat_id;",
                        params={"chat_id": update.effective_chat.id},
                    )
                    await context.bot.send_message(
                        chat_id=user_id, text=f"Ок, я все понял!☹️\nЯ пошел..."
                    )
    return


async def user(
    update: Update, context: ContextTypes.DEFAULT_TYPE, sms: str
) -> None:
    if update.message or update.effective_chat and context:
        if update.message.from_user.id in user_triger:
            user_triger.pop(update.message.from_user.id)
        elif update.effective_chat.id in user_triger:
            user_triger.pop(update.effective_chat.id)
    if chat_type(update) == "private":
        await new_button(update, sms)


async def helper(update: Update, context: CallbackContext) -> None:
    if chat_type(update) == "private":
        if context:
            user_id: int = await get_user_id(update)
        user_search = pd.read_sql(
            "SELECT name FROM heroes_of_users "
            "WHERE user_id = %(user_id)s';",
            params={"user_id": user_id},
            con=engine,
        )
        if not user_search.empty:
            sms = """
Напиши \"Привет\" чтобы проверить свой ник.
Можешь кидать количество камней (цифрами) и спросить сколько у тебя камней.
Загляни в настройки пользователя, там можешь подписаться на напоминания по \
сбору халявной энергии или на напоминания по камням за час до смены К.З.\
(или отписаться)
Если у тебя не один профель в игре, можешь добавить его ник и также кидать на \
него кол-во камней, но можно добавить не больше 5 героев!
Если возникли проблемы с кнопками напиши /start \
(не помогло напиши мне @Menace134)
"""
            await new_button(update, sms)
            info = pd.read_sql(
                "SELECT COUNT(*) FROM admins " "WHERE user_id = %(user_id)s';",
                params={"user_id": user_id},
                con=engine,
            )
            if info.loc[0, "count"] != 0:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"Для тебя, {update.message.from_user.first_name}, "
                    "ещё есть настройки администратора.\n "
                    "Там ты сможешь:\n - отправить напоминалку игроку\n"
                    "- редактировать сообщение напоминалки\n"
                    "- отправить ВСЕМ сообщение\n"
                    '- написать в "флудилку" от имени бота.\n'
                    "- убрать игрока из клана☠",
                )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text="Я тебя не помню. Давай знакомиться! "
                "Какой у тебя ник в игре?",
            )
            user_triger[user_id] = {
                "triger": "reg_start",
                "first": True,
                "rename": False,
            }
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Привет, скоро будет инструкция...!",
        )


async def print_rock(update, context, info):
    """вывод камней"""
    hours = int(info.loc[0, "time_change_kz"])
    now = datetime.now()
    time1 = timedelta(
        days=now.day, hours=now.hour, minutes=now.minute, seconds=now.second
    )
    time2 = timedelta(days=now.day, hours=hours, minutes=30, seconds=0)
    time3 = time2 - time1
    if time3.days == -1:
        time2 = timedelta(days=now.day + 1, hours=hours, minutes=30, seconds=0)
        time3 = time2 - time1
    if int(info.loc[0, "rock"]) == 0:
        sms = (
            "Ты еще не вводил количество своих камней. "
            "Введи количество цифрами!"
        )
    else:
        sms = (
            f"У твоего героя под ником \"{info.loc[0, 'name']}\" "
            f"- \"{info.loc[0, 'rock']}\" камней! Осталось добить "
            f"{600 - int(info.loc[0, 'rock'])}. До обновления К.З. осталось "
            f"{time3}"
        )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=sms)


async def edit(update, context, num, info, delete):
    if delete:
        callback = "delete"
        text = "Кого будем удалять?"
    else:
        callback = "edit_name"
        text = "Кого будем переименовывать?"
    keyboard = []
    for i in range(num):
        keyboard += [
            [
                InlineKeyboardButton(
                    str(info.loc[i, "name"]),
                    callback_data=f'{callback}-{info.loc[i, "id"]}',
                )
            ]
        ]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def edit_name(update, context, id_hero: int):
    await context.bot.send_message(
        chat_id=update.message.from_user.id, text="На какое имя будем менять?"
    )
    user_triger[update.message.from_user.id] = {
        "triger": "edit_name",
        "id": id_hero,
    }


async def add_rock(update, context, upg_rock: int, id_hero) -> None:
    """Добавление камней"""
    try:
        info = pd.read_sql(
            "SELECT rock FROM heroes_of_users WHERE id = %(id_hero)s;",
            params={"id_hero": id_hero},
            con=engine,
        )
        rock = int(info.loc[0, "rock"])
        if rock == 0 or rock < upg_rock:
            await insert_and_update_sql(
                "UPDATE heroes_of_users "
                "SET rock = :upg_rock WHERE id = :id_hero;",
                params={
                    "upg_rock": upg_rock,
                    "id_hero": id_hero,
                },
            )
            rock_minus = 600 - upg_rock
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Ок, я внес изменения. "
                f"Тебе осталось добить {rock_minus}",
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Ты меня не обманешь! В прошлый раз ты писал {rock}",
            )
    except Exception:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла какая-то ошибка. Попробуй позже! "
            "Или напишите об ошибке @Menace134.",
        )


async def time_zone(update, context, msg, tz, id_hero) -> None:
    """Узнаем часовой во сколько происходит смена КЗ"""
    try:
        user_id = await get_user_id(update)
        if msg in stop_word:
            sms = "Отмена"
            await setting_hero_button(update, sms)
            return
        else:
            if msg.isnumeric():
                if 1 <= int(msg) <= 24:
                    if tz:  # КЗ
                        await insert_and_update_sql(
                            """"UPDATE heroes_of_users
                            SET time_change_kz = :msg
                            WHERE user_id = :user_id and id = :id_hero;""",
                            params={
                                "msg": msg,
                                "user_id": user_id,
                                "id_hero": id_hero,
                            },
                        )
                    else:  # энергия
                        await insert_and_update_sql(
                            """"UPDATE heroes_of_users
                            SET time_collection_energy = :msg
                            WHERE user_id = :user_id and id = :id_hero;""",
                            params={
                                "msg": msg,
                                "user_id": user_id,
                                "id_hero": id_hero,
                            },
                        )
                    sms = (
                        "Время умпешно установлено!\n"
                        "Если Вы ошиблись или время поменяется, "
                        "всегда можно изменить и тут.\n\n"
                        "Для этого нажми ⚙️Настройка профиля⚙️ ---> "
                        "Поменять время..."
                    )

                    await edit_time_button(update, sms)
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
            chat_id=my_tid,
            text=f"{update.message.from_user.first_name} "
            "пытался изменить время...ОШИБКА",
        )


async def delete_person(update, context, id_hero) -> None:
    """Удаляем персонажа, смотрим сколько всего персов
    и смещаем их к тому который удаляем"""
    info = pd.read_sql(
        "SELECT * FROM heroes_of_users WHERE id = %(id_hero)s;",
        params={"id_hero": id_hero},
        con=engine,
    )
    await insert_and_update_sql(
        "DELETE FROM heroes_of_users "
        "WHERE user_id = :user_id AND id = :id_hero;",
        params={
            "user_id": update.effective_chat.id,
            "id_hero": id_hero,
        },
    )
    await new_button(
        update, sms=f"Герой с ником \"{info.loc[0, 'name']}\" удален!"
    )
    return


async def first_sms(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    sms = """Сейчас время смены кланового задания установлено __18:30__, а первый сбор бесплатной энергии установлен на __12:00__ \(__*по МСК*__\)\.

    *Если данное время неверно, то это можно с лёгкостью изменить в настройках\!*
    Для этого нажми *Настройка профиля* \-\-\-\> *Поменять время\.\.\.*

    *Так же можно __бесплатно__ подписаться на напоминалки\!*
    Чтобы это сделать проходим *Настройка профиля* \-\-\-\> *Подписки\.\.\.*
    """
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=sms, parse_mode="MarkdownV2"
    )


async def button(update: Update, context: CallbackContext) -> None:
    """Реагирует на нажатие кнопок."""
    query = update.callback_query
    await query.answer()
    if "YES" in query.data:
        await update.callback_query.message.delete()
        if "-" in query.data:
            list_answer = query.data.split("-")
            if len(list_answer) > 2 and list_answer[1] == "DELETE":
                id_hero = int(list_answer[2])
                await delete_person(update, context, id_hero)
        else:
            await setting_hero_button(update, "Отлично, будем знакомы)")
            try:
                await first_sms(update, context)
            except Exception as err:
                logging.error(err)
                logging.info(f"Пользователь с id = {update.effective_chat.id}")
        if update.effective_chat.id in user_triger:
            user_triger.pop(update.effective_chat.id)

    elif "NO" in query.data:
        await update.callback_query.message.delete()
        if "-" in query.data:
            list_answer = query.data.split("-")
            # if len(list_answer) > 2 and list_answer[1] == "DELETE":
            #     info = pd.read_sql(
            #     f"SELECT * FROM bot_users
            #     WHERE user_id = '{update.effective_chat.id}';", engine)
            #     num = int(info.loc[0, 'num_pers'])
            #     edit(update, context, num, info, True)
        else:
            await query.edit_message_text(
                "Ок, давай попробуем снова. Какой у тебя ник в игре?"
            )
            user_triger[update.effective_chat.id] = {
                "triger": "reg_start",
                "first": True,
                "rename": True,
            }
    elif "Add_Rock" in query.data:
        sms = int(query.data.split("-")[1])
        id_hero = query.data.split("-")[2]
        await add_rock(update, context, sms, id_hero)
    elif "delete" in query.data:
        # Принимаем id строки, которую хотим удалить,
        # и после уточняем, точно ли?
        id_hero = query.data.split("-")[1]
        await update.callback_query.message.delete()
        info = pd.read_sql(
            f"SELECT name FROM heroes_of_users WHERE id = '{id_hero}';", engine
        )
        keyboard = [
            [
                InlineKeyboardButton(
                    "Да", callback_data=f"YES-DELETE-{id_hero}"
                ),
                InlineKeyboardButton(
                    "Нет", callback_data=f"NO-DELETE-{id_hero}"
                ),
            ]
        ]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ты хочешь удалить героя под "
            f"ником \"{info.loc[0, 'name']}\"?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    elif "setting_profile" in query.data:
        id_hero = int(query.data.split("-")[1])
        user_triger[update.effective_chat.id] = {
            "triger": "setting_profile",
            "id": id_hero,
            "setting_hero": False,
        }
        await setting_button(update, "Что будем изменять?")

    elif "print" in query.data:
        id_hero = query.data.split("-")[1]
        info = pd.read_sql(
            "SELECT id, name, rock, time_change_kz "
            "FROM heroes_of_users WHERE id = %(id_hero)s;",
            params={"id_hero": id_hero},
            con=engine,
        )
        await print_rock(update, context, info)
    elif "edit_name" in query.data:
        id_hero = int(query.data.split("-")[1])
        await edit_name(update, context, id_hero)


async def manul_kv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Инструкция по КВ"""
    info = pd.read_sql(
        "SELECT text, name_text FROM text_table "
        "WHERE name_text in ('kv1','kv2');",
        con=engine,
    )
    if info.loc[0, "name_text"] == "kv1":
        text1 = info.iloc[0, 0]
        text2 = info.iloc[1, 0]
    else:
        text1 = info.iloc[1, 0]
        text2 = info.iloc[0, 0]
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text1
    )
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=open(working_folder + "help/kv.jpg", "rb"),
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text2
    )


async def date_x2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Инструкция по КВ"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Сорян, эта команда еще не работает. =(",
    )


async def schedule_of_clan_tasks(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Расписание клановых заданий"""
    info = pd.read_sql(
        "SELECT text FROM text_table "
        "WHERE name_text = 'schedule_of_clan_tasks';",
        con=engine,
    )
    text = info.iloc[0, 0]
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


async def manul_aptechkam_kv(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Гайд по аптечкам в КВ"""
    with open(working_folder + "help/Manual_KV.doc", "rb") as file:
        await context.bot.send_document(
            chat_id=update.effective_chat.id, document=file
        )


async def necessary_heroes_for_events(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Необходимые герои для ивентов"""
    file_name = {
        "All_Event_Overviews_5_LQ.png": "Все герои из событий.",
        "Sandariel-Event.png": "Сандариэль.",
        "Magnus-Event_Pass.png": "Магнус.",
        "Balthazar-Event.png": "Бальтазар.",
        "Gobliana-Event.png": "Гоблушка.",
        "zigfrid.jpg": "Зигфрид.",
        "Daghan.jpg": "Да'Гана.",
        "ivent_AOM.jpg": "структурированный гайд от Pulcho.",
        "Infographic_Events-1.png": "гайд по событиям.",
    }
    for name in file_name:
        with open(
            working_folder + f"help/necessary_heroes_for_events/{name}", "rb"
        ) as img:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img,
                caption=file_name[name],
            )
    return


async def pak_and_counterpak(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Таблица паков и контропаков"""
    with open(working_folder + "help/pak_and_counterpak.jpg", "rb") as img:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id, photo=img
        )
    return


async def useful_links(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Полезные ссылки"""
    info = pd.read_sql(
        "SELECT text FROM text_table " "WHERE name_text = 'useful_links';",
        con=engine,
    )
    text = info.iloc[0, 0]
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=text, parse_mode="MarkdownV2"
    )
    return


# Для новичков
async def for_new_gamers(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    with open(working_folder + "help/manual_for_new_gamers.pdf", "rb") as pdf:
        await context.bot.send_document(
            chat_id=update.effective_chat.id, document=pdf
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""Полезные каналы:

[канал со списком кланов для новичков](https://t.me/aomstart)

Гайды:

[Гайды для новичков по пунктам](https://t.me/helpaom2)

[Гайды по игре](https://t.me/AoM_Jr/7)

Чаты:

[чат для общения](https://t.me/floodAoM2)

[официальный чат игры](https://t.me/+-kXDhI4uG4Y4YTdi)""",
        parse_mode="MarkdownV2",
    )
    return


async def update_time_change_clan_task(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    type_msg = await get_type_msg(update)
    user_id = update[type_msg]["from_user"]["id"]
    msg_id = update[type_msg]["message_id"]
    chat_type = update[type_msg]["chat"]["type"]

    if chat_type == "supergroup" or chat_type == "group":
        group_triger[f"{user_id}@{update.effective_chat.id}"] = {
            "triger": "update_time_change_clan_task",
            "group": update.effective_chat.id,
            "user_id": user_id,
        }
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Во сколько по москве смена КЗ? Вводи только час.\n"
            "Пример: 18",
            reply_to_message_id=msg_id,
        )
    return


async def remin15(
    update: Update, context: ContextTypes.DEFAULT_TYPE, if_start: bool
) -> None:
    """Start or stop remind time rock"""
    type_msg = await get_type_msg(update)
    chat_id = update.effective_chat.id
    msg_id = update[type_msg]["message_id"]
    chat_type = update[type_msg]["chat"]["type"]
    if chat_type == "supergroup" or chat_type == "group":
        await insert_and_update_sql(
            "UPDATA clans SET remain_zero_rock = :start "
            "WHERE chat_id = :chat_id;",
            params={
                "start": if_start,
                "chat_id": chat_id,
            },
        )
    if if_start:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ок, я напомню вам за час, о том что будет обнуление камней.",
            reply_to_message_id=msg_id,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Не хотите, как хотите!😝",
            reply_to_message_id=msg_id,
        )

    return


async def start_remin15(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await remin15(update, context, if_start=True)
    return


async def stop_remin15(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    await remin15(update, context, if_start=False)
    return


async def handle_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    try:
        """{'update_id': 597348238,
        'message': {'delete_chat_photo': False,
                    'entities': [],
                    'new_chat_photo': [],
                    'date': 1665683250,
                    'chat': {'type': 'private',
                            'id': 943180118,
                            'first_name': 'Константин',
                            'username': 'Menace134'},
                            'caption_entities': [],
                            'supergroup_chat_created': False,
                            'text': '⚙️Настройка профиля⚙️',
                            'group_chat_created': False,
                            'channel_chat_created': False,
                            'photo': [],
                            'new_chat_members': [],
                            'message_id': 7075,
                            'from': {'id': 943180118,
                                    'is_bot': False,
                                    'language_code': 'ru',
                                    'first_name': 'Константин',
                                    'username': 'Menace134'
                                    }
                            }
                    }"""
        type_msg = get_type_msg(update)
        user_id = update[type_msg]["from_user"]["id"]  # записываем ID с телеги
        msg = update[type_msg]["text"].lower()
        msg_id = update[type_msg]["message_id"]
        chat_type = update[type_msg]["chat"]["type"]

        if chat_type == "private":
            if msg in stop_word:
                await user(
                    update, context, sms="Ок, отмена! Идем в главное меню."
                )
            if user_id in user_triger:
                triger = user_triger[user_id]["triger"]
                if msg in stop_word:
                    await user(
                        update, context, sms="Ок, отмена! Идем в главное меню."
                    )
                if triger == "reg_start":
                    if msg != "/help":
                        name = (
                            update.message.text
                        )  # после вопроса как звать записываем имя
                        if user_triger[user_id]["first"]:
                            if user_triger[user_id]["rename"]:
                                await insert_and_update_sql(
                                    "UPDATE heroes_of_users SET name = :name "
                                    "WHERE user_id = :user_id;",
                                    params={
                                        "name": name,
                                        "user_id": user_id,
                                    },
                                )
                            else:
                                variables = ""
                                values = ""
                                from_user = update.message.from_user
                                values_params = {
                                    "user_id": user_id,
                                    "first_name": from_user.first_name,
                                    "language_code": from_user.language_code,
                                    "last_name": from_user.last_name,
                                    "username": from_user.username,
                                }
                                if values_params["first_name"] is not None:
                                    variables += ", first_name"
                                    values += ", :first_name"
                                if values_params["language_code"] is not None:
                                    variables += ", language_code"
                                    values += ", :language_code"
                                if values_params["last_name"] is not None:
                                    variables += ", last_name"
                                    values += ", :last_name"
                                if values_params["username"] is not None:
                                    variables += ", username"
                                    values += ", :username"
                                try:
                                    await insert_and_update_sql(
                                        f"INSERT INTO telegram_users_id"
                                        f"(user_id{variables}) "
                                        f"VALUES(:user_id{values});",
                                        params=values_params,
                                    )
                                except Exception as err:
                                    print(err)
                                await insert_and_update_sql(
                                    "INSERT INTO heroes_of_users"
                                    "(user_id, name, clan_id) "
                                    "VALUES(:user_id, :name, :clan_id);",
                                    params={
                                        "user_id": user_id,
                                        "name": name,
                                        "clan_id": 1,
                                    },
                                )
                        else:
                            await insert_and_update_sql(
                                "INSERT INTO heroes_of_users"
                                "(user_id, name, clan_id) "
                                "VALUES(:user_id, :name, :clan_id);",
                                params={
                                    "user_id": user_id,
                                    "name": name,
                                    "clan_id": 1,
                                },
                            )
                        keyboard = [
                            [
                                InlineKeyboardButton(
                                    "Да", callback_data="YES"
                                ),
                                InlineKeyboardButton(
                                    "Нет", callback_data="NO"
                                ),
                            ]
                        ]
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f'Ты герой под ником "{name}"?',
                            reply_markup=InlineKeyboardMarkup(keyboard),
                        )
                elif triger == "edit_name":
                    # после вопроса как звать записываем имя
                    name = update.message.text
                    id_hero = user_triger[update.message.from_user.id]["id"]
                    info = pd.read_sql(
                        "SELECT COUNT(*) FROM heroes_of_users "
                        "WHERE user_id = %(user_id)s AND id = %(id_hero)s;",
                        params={
                            "user_id": user_id,
                            "id_hero": id_hero,
                        },
                        con=engine,
                    )
                    if info.loc[0, "count"] != 0:
                        await insert_and_update_sql(
                            "UPDATE heroes_of_users SET name = :name "
                            "WHERE user_id = :user_id AND id = :id_hero",
                            params={
                                "name": name,
                                "user_id": user_id,
                                "id_hero": id_hero,
                            },
                        )
                        sms = f'Теперь тебя зовут: "{name}"!'
                        await context.bot.send_message(
                            chat_id=user_id, text=sms
                        )
                elif triger == "time_zone":
                    await time_zone(
                        update,
                        context,
                        msg,
                        user_triger[user_id]["tz"],
                        user_triger[user_id]["id"],
                    )
                elif triger == "setting_profile":
                    if "манипуляции с героем" == msg:
                        await setting_hero_button(
                            update,
                            "Тут ты можешь добавить или удалить героя, "
                            "ну и при необходимости переименовать его.",
                        )
                        user_triger[user_id]["setting_hero"] = True
                    elif "подписки" in msg:
                        await subscription_button(
                            update, "Смотри...", user_triger[user_id]["id"]
                        )
                        user_triger[user_id]["setting_hero"] = True
                    elif "поменять время..." == msg:
                        await edit_time_button(update, "Меняй...")
                        user_triger[user_id]["setting_hero"] = True
                    elif "проверить данные профиля" == msg:
                        info = pd.read_sql_query(
                            """
                            SELECT heroes_of_users.*, clans.name_clan
                            FROM heroes_of_users INNER JOIN clans
                                ON (clans.id=heroes_of_users.clan_id)
                            WHERE heroes_of_users.user_id = %(user_id)s
                                AND heroes_of_users.id = %(id_hero)s;
                            """,
                            params={
                                "user_id": user_id,
                                "id_hero": user_triger[user_id]["id"],
                            },
                            con=engine,
                        )
                        if str(info.loc[0, "name_clan"]) != "Без клана":
                            clan = f"Ты в клане \"{info.loc[0, 'name_clan']}\""
                        else:
                            clan = ""
                        # считываем смену кз
                        smena_kz = str(info.loc[0, "time_change_kz"])
                        # считываем сбор энергии
                        sbor_energi = str(
                            info.loc[0, "time_collection_energy"]
                        )

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
                                "Вы не подписаны на оповещение "
                                "по сбору энергии."
                            )
                        if info.loc[0, "subscription_energy"]:
                            description_of_the_kz_text = (
                                "Вы подписаны на ежедневное описание КЗ."
                            )
                        else:
                            description_of_the_kz_text = (
                                "Вы не подписаны на ежедневное описание КЗ."
                            )
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"Твой ник в игре: {info.loc[0, 'name']}\n"
                            f"{subscription_rock_text}\n"
                            f"{subscription_energi_text}\n"
                            f"{description_of_the_kz_text}\n"
                            f"Время смены КЗ: {smena_kz}:30 по мск \n"
                            "Время сбора первой энергии: "
                            f"{sbor_energi}:00 по мск\n"
                            f"{clan}",
                        )
                    elif "поменять время смены кз" == msg:
                        await cancel_button(
                            update,
                            sms="Во сколько по москве смена КЗ? "
                            "Вводи только час.\n Пример: 18",
                        )
                        user_triger[user_id] = {
                            "triger": "time_zone",
                            "tz": True,
                            "id": user_triger[user_id]["id"],
                        }
                    elif "поменять время первого сбора энергии" == msg:
                        await cancel_button(
                            update,
                            sms="Во сколько по москве первый сбор энергии "
                            "(синька и фиолетка)? Вводи только час.\n "
                            "Пример: 12",
                        )
                        user_triger[user_id] = {
                            "triger": "time_zone",
                            "tz": False,
                            "id": user_triger[user_id]["id"],
                        }
                    elif (
                        "удалить одного героя" in msg
                        or "переименовать героя" in msg
                    ):
                        # info = pd.read_sql(
                        # f"SELECT * FROM heroes_of_users
                        # WHERE user_id = '{user_id}'
                        # and id = '{user_triger[user_id]['id']}';", engine)
                        # num = len(info)
                        # if num >= 2:
                        #     if "переименовать героя" in msg:
                        #         delete = False
                        #     else:
                        #         delete = True
                        #     edit(update, context, num, info, delete)
                        # else:
                        if "переименовать героя" in msg:
                            await edit_name(
                                update,
                                context,
                                int(user_triger[user_id]["id"]),
                            )
                        else:
                            await delete_person(
                                update,
                                context,
                                int(user_triger[user_id]["id"]),
                            )
                    elif "подписаться" in msg or "отписаться" in msg:
                        who_edit = ""
                        text = ""
                        if (
                            "подписаться на напоминалку о смене кз за час"
                            == msg
                        ):
                            who_edit = "subscription_rock = '1'"
                            text = "Если у вас будет меньше 600 камней, \
я вам напомню об этом за час до смены КЗ."
                        elif (
                            "отписаться от напоминалки о смене кз за час"
                            == msg
                        ):
                            who_edit = "subscription_rock = '0'"
                            text = "Хорошо, больше не буду вам напоминать \
про камни... Автоматически."
                        elif (
                            "подписаться на напоминалку по сбору энергии"
                            == msg
                        ):
                            who_edit = "subscription_energy = '1'"
                            text = "Теперь я буду напоминать Вам про энергию."
                        elif (
                            "отписаться от напоминалки по сбору энергии" == msg
                        ):
                            who_edit = "subscription_energy = '0'"
                            text = "Хорошо, больше не буду Вам напоминать \
про энергию..."
                        elif "подписаться на ежедневное описание кз" == msg:
                            who_edit = "description_of_the_kz = '1'"
                            text = "Теперь я буду присылать Вам краткое \
описание кланового задания."
                        elif "отписаться от ежедневного описания кз" == msg:
                            who_edit = "description_of_the_kz = '0'"
                            text = "Хорошо, больше не буду присылать Вам \
краткое описание кланового задания."
                        await insert_and_update_sql(
                            f"UPDATE heroes_of_users SET {who_edit} "
                            "WHERE user_id = :user_id AND id = :id_hero",
                            params={
                                "user_id": user_id,
                                "id_hero": user_triger[user_id]["id"],
                            },
                        )
                        await subscription_button(
                            update, text, int(user_triger[user_id]["id"])
                        )
                    elif "добавить еще одного героя" in msg:
                        await cancel_button(update, "Какой у тебя ник в игре?")
                        user_triger[user_id] = {
                            "triger": "reg_start",
                            "first": False,
                            "rename": False,
                        }
                    elif "🔙назад🔙" == msg:
                        if user_triger[user_id]["setting_hero"]:
                            await setting_button(update, "Ок, вернулись.")
                            user_triger[user_id]["setting_hero"] = False
                        else:
                            await new_button(
                                update, "Погнали, назад, в главное меню."
                            )
                            user_triger.pop(user_id)
                if user_id in user_triger and triger != "setting_profile":
                    if triger == "edit_name" or triger == "time_zone":
                        user_triger[user_id] = {
                            "triger": "setting_profile",
                            "id": user_triger[user_id]["id"],
                            "setting_hero": True,
                        }
                    else:
                        user_triger.pop(user_id)

            else:
                if (
                    msg.isnumeric() and update.message.chat.type == "private"
                ) or (
                    "люцик добавь" in msg
                    and (
                        update.message.chat.type == "supergroup"
                        or update.message.chat.type == "group"
                    )
                ):
                    if update.message.chat.type == "supergroup":
                        if (
                            msg.replace("люцик добавь", "")
                            .replace(" ", "")
                            .isnumeric()
                        ):
                            sms = msg.replace("люцик добавь", "").replace(
                                " ", ""
                            )
                            await context.bot.send_message(
                                chat_id=update.message.chat.id,
                                text="Глянь в личку...",
                            )
                        else:
                            await context.bot.send_message(
                                chat_id=update.message.chat.id,
                                text="Ты что, хочешь меня обмануть? "
                                "Мне нужны цифры! \n(напиши повторно, "
                                'на пример: "Люцик добавь 400")',
                            )
                            return
                    else:
                        sms = msg
                    if 0 <= int(sms) <= 600:
                        info = pd.read_sql(
                            "SELECT id, name FROM heroes_of_users "
                            "WHERE user_id = %(user_id)s;",
                            params={"user_id": user_id},
                            con=engine,
                        )
                        keyboard = []
                        if len(info) == 1:
                            await add_rock(
                                update, context, int(sms), info.loc[0, "id"]
                            )  # передаем для записи камней
                        else:
                            for idx, row in info.iterrows():
                                keyboard.append(
                                    [
                                        InlineKeyboardButton(
                                            str(row["name"]),
                                            callback_data=f"Add_Rock-{sms}-"
                                            f'{row["id"]}',
                                        )
                                    ]
                                )
                            await context.bot.send_message(
                                chat_id=user_id,
                                text="Кому добавим камни?",
                                reply_markup=InlineKeyboardMarkup(keyboard),
                            )
                    else:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text="Ты что, хочешь меня обмануть? "
                            "Проверь сколько у тебя камней!",
                        )
                elif (
                    ("сколько у меня камней?" in msg)
                    or ("сколько" in msg)
                    and update.message.chat.type == "private"
                ):
                    info = pd.read_sql(
                        "SELECT id, name, rock, time_change_kz "
                        "FROM heroes_of_users WHERE user_id = %(user_id)s;",
                        params={"user_id": user_id},
                        con=engine,
                    )  # поиск айди в БД
                    keyboard = []
                    if len(info) == 1:
                        await print_rock(update, context, info)
                    else:
                        for idx, row in info.iterrows():
                            keyboard.append(
                                [
                                    InlineKeyboardButton(
                                        str(row["name"]),
                                        callback_data=f'print-{row["id"]}',
                                    )
                                ]
                            )
                        await context.bot.send_message(
                            chat_id=user_id,
                            text="Кто тебя интересует?",
                            reply_markup=InlineKeyboardMarkup(keyboard),
                        )
                elif (
                    "прив" in msg and update.message.chat.type == "private"
                ) or (
                    ("люц" in msg or "всем" in msg or "доброе" in msg)
                    and (
                        "прив" in msg
                        or "ку" in msg
                        or "здаров" in msg
                        or "утр" in msg
                    )
                    and (
                        update.message.chat.type == "supergroup"
                        or update.message.chat.type == "group"
                    )
                ):
                    name = ""
                    info = pd.read_sql(
                        "SELECT name FROM heroes_of_users "
                        "WHERE user_id = %(user_id)s;",
                        params={"user_id": user_id},
                        con=engine,
                    )
                    if not info.empty:
                        name = str(info.loc[0, "name"])
                    else:
                        if update.message.from_user.first_name is not None:
                            name = update.message.from_user.first_name
                        elif update.message.from_user.username is not None:
                            name = update.message.from_user.username
                    rand_num = random.randint(1, 5)
                    if rand_num == 1:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"Привет, {name}!",
                            reply_to_message_id=msg_id,
                        )
                    elif rand_num == 2:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"Привет, {name}, как твои дела?.. "
                            "Хотя, знаешь,не отвечай... "
                            "и так знаю что хорошо.",
                            reply_to_message_id=msg_id,
                        )
                    elif rand_num == 3:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"Ку, {name}.",
                            reply_to_message_id=msg_id,
                        )
                    elif rand_num == 4:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"Привет, {name}, ты уже набил 600 камней? "
                            "Если нет, иди и не возвращайся "
                            "пока не набьешь!",
                            reply_to_message_id=msg_id,
                        )
                    elif rand_num == 5:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"Ну привет, {name}, если не здоровались",
                            reply_to_message_id=msg_id,
                        )
                elif "люц" in msg and "рейд" in msg:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="Сейчас!",
                        reply_to_message_id=msg_id,
                    )
                    sms = "Рейд открыт заходим согласно купленным билетам!"
                    if (
                        "что" in msg
                        or "чё" in msg
                        or "чо" in msg
                        or "че" in msg
                    ):
                        rand_num = 4
                    else:
                        rand_num = random.randint(1, 3)
                    if rand_num == 1:
                        await context.bot.send_message(
                            chat_id=update.message.chat.id,
                            text="Ану быстро в рейд! Кто последний тот ЛОХ!)",
                        )
                        with open(
                            working_folder + "AnimatedSticker.tgs", "rb"
                        ) as sticker:
                            await context.bot.send_sticker(
                                chat_id=update.message.chat.id, sticker=sticker
                            )
                    elif rand_num == 2:
                        await context.bot.send_message(
                            chat_id=update.message.chat.id,
                            text="Рейд открыт заходим согласно "
                            "купленным билетам",
                        )
                        with open(
                            working_folder + "sticker.webp", "rb"
                        ) as sticker:
                            await context.bot.send_sticker(
                                chat_id=update.message.chat.id, sticker=sticker
                            )
                    elif rand_num == 3:
                        await context.bot.send_message(
                            chat_id=update.message.chat.id,
                            text="Не вижу ваших жопок на рейде!!! "
                            "БЫСТРО В РЕЙД!",
                        )
                    elif rand_num == 4:
                        await context.bot.send_message(
                            chat_id=update.message.chat.id,
                            text="Не знаю как, но нужно закрыть рейд на 100%!",
                        )
                        with open(working_folder + "frog.mp4", "rb") as video:
                            await context.bot.send_video(
                                chat_id=update.message.chat.id, video=video
                            )
                elif (
                    "открыт" in msg
                    and "рейд" in msg
                    and (
                        update.message.chat.type == "supergroup"
                        or update.message.chat.type == "group"
                    )
                ):
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="В атакууууу... =)",
                        reply_to_message_id=msg_id,
                    )
                    sms = "Рейд открыт заходим согласно купленным билетам!"
                    with open(
                        working_folder + "video_2021-05-03_21-58-18.mp4", "rb"
                    ) as video:
                        await context.bot.send_video(
                            chat_id=update.message.chat.id, video=video
                        )
                elif "💵пожертвование моему создателю💸" == msg:
                    rand_num = random.randint(1, 15)
                    if rand_num == 1:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="Мне на жилье, на большой и просторный "
                            "сервер😇",
                        )
                    elif rand_num == 2:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="Моему созадтелю на кофе☕️",
                        )
                    elif rand_num == 3:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="Моему созадтелю на еду🍲️",
                        )
                    elif rand_num == 4:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="Моему созадтелю на еду🍺😈",
                        )
                    elif rand_num == 5:
                        await context.bot.send_sticker(
                            chat_id=update.effective_chat.id,
                            sticker="CAACAgIAAxkBAAEIdXBkLGI0l7SBevxq54AYD"
                            "fwqgrRUAAOwDQAC4mD4SPhHhqikFBgNLwQ",
                        )
                    elif rand_num == 6:
                        await context.bot.send_sticker(
                            chat_id=update.effective_chat.id,
                            sticker="CAACAgIAAxkBAAEIdXJkLGJcvt8bKENug5F9C3"
                            "b8lLUC8gACuQsAAsqaoUkN2KXU8e7Say8E",
                        )
                    elif rand_num == 7:
                        await context.bot.send_sticker(
                            chat_id=update.effective_chat.id,
                            sticker="CAACAgIAAxkBAAEIdXRkLGJ2W6EizKHiIMyMp"
                            "QvRhSfxUgACSBMAAt2FmElzhpwNSO5yBy8E",
                        )
                    elif rand_num == 8:
                        await context.bot.send_sticker(
                            chat_id=update.effective_chat.id,
                            sticker="CAACAgIAAxkBAAEIdXZkLGKYqURjcg-n55R5to"
                            "5rxaAcyQACnwoAApNloUnjCXxz3frjTi8E",
                        )
                    elif rand_num == 9:
                        await context.bot.send_sticker(
                            chat_id=update.effective_chat.id,
                            sticker="CAACAgIAAxkBAAEIdXhkLGKn4-BH-6ihPjj4Yl"
                            "PIhaumAwACIQsAAjooAUkWkfFshXQHLi8E",
                        )
                    elif rand_num == 10:
                        await context.bot.send_sticker(
                            chat_id=update.effective_chat.id,
                            sticker="CAACAgIAAxkBAAEIdXpkLGLSR9RNFUtB6SNh5S"
                            "JN5GIWYAACTwsAAs4XAAFJ4ud9u0yjrhgvBA",
                        )
                    elif rand_num == 11:
                        await context.bot.send_sticker(
                            chat_id=update.effective_chat.id,
                            sticker="CAACAgIAAxkBAAEIdX9kLGLwylwuMSwGj_kXkWc"
                            "U_SPb9QACwRQAAqUqCUhsSHVuhH-2XC8E",
                        )
                    elif rand_num == 12:
                        await context.bot.send_sticker(
                            chat_id=update.effective_chat.id,
                            sticker="CAACAgIAAxkBAAEIdYFkLGMILgAB7VKOrsNO5e"
                            "S3qrtzps0AAl0oAALZEiFKDZLyZ6WHRZMvBA",
                        )
                    elif rand_num == 13:
                        await context.bot.send_sticker(
                            chat_id=update.effective_chat.id,
                            sticker="CAACAgIAAxkBAAEIdYNkLGMcwyMEgf3qBdt6X6"
                            "T3ey4-QQACaAsAAtv7OUnL_oTTDlslMi8E",
                        )
                    elif rand_num == 14:
                        await context.bot.send_sticker(
                            chat_id=update.effective_chat.id,
                            sticker="CAACAgQAAxkBAAEIdYdkLGQWkK6dqfhrxqQo53"
                            "zEuqSqHAAC5gsAAk8cWVNQLKJXQdhgTi8E",
                        )
                    elif rand_num == 15:
                        await context.bot.send_sticker(
                            chat_id=update.effective_chat.id,
                            sticker="CAACAgQAAxkBAAEIdYlkLGQat8x1t7j2NPJ01v"
                            "ge-ixN7QACxQwAAplx6FAZ8I5wA_llpi8E",
                        )
                    # keyboard = [[InlineKeyboardButton(
                    # "Ссылка на пожертвование через сайт Тинькофф",
                    # url='https://www.tinkoff.ru/rm/tkachev.'
                    #     'konstantin69/3j6lJ87953'
                    # )]]
                    # with open(working_folder + "QR-code.jpg", "rb") as img:
                    #     await context.bot.send_photo(
                    #         chat_id=update.effective_chat.id,
                    #         photo=img,
                    #         caption="QR\-код на пожертвование через "
                    #                 "сайт Тинькофф",
                    #         parse_mode='MarkdownV2',
                    #         reply_markup=InlineKeyboardMarkup(keyboard)
                    #     )
                    # "[Создатель бота](https://t.me/Menace134)
                    # \- Константин Т\.", parse_mode='MarkdownV2'
                    # await context.bot.send_message(
                    #     chat_id=update.effective_chat.id,
                    #     text='Отсканируйте QR-код или просто нажмите на '
                    #          'ссылку, чтобы отблагодарить автора.'
                    # )
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="СБП по номеру, это временно... @menace134",
                    )
                elif "помощь" in msg:
                    await help_my_button(
                        update, "Вот, листай список, выбирай!"
                    )
                elif "полезная информация" == msg:
                    await help_button(update, "Вот, листай список, выбирай!")
                elif "добавить еще одного героя" in msg:
                    await cancel_button(update, "Какой у тебя ник в игре?")
                    user_triger[user_id] = {
                        "triger": "reg_start",
                        "first": False,
                        "rename": False,
                    }
                elif "⚙️настройка профиля⚙️" == msg:
                    info = pd.read_sql_query(
                        "SELECT id, name FROM heroes_of_users "
                        "WHERE user_id = %(user_id)s",
                        params={"user_id": user_id},
                        con=engine,
                    )
                    if len(info) == 1:
                        user_triger[user_id] = {
                            "triger": "setting_profile",
                            "id": info.loc[0, "id"],
                            "setting_hero": False,
                        }
                        await setting_button(update, "Что будем изменять?")
                    else:
                        keyboard = []
                        for idx, row in info.iterrows():
                            keyboard += [
                                [
                                    InlineKeyboardButton(
                                        str(row["name"]),
                                        callback_data="setting_profile-"
                                        f'{row["id"]}',
                                    )
                                ]
                            ]
                        await context.bot.send_message(
                            chat_id=user_id,
                            text="Выберите, какого героя будем редактировать.",
                            reply_markup=InlineKeyboardMarkup(keyboard),
                        )
                elif "инструкция по применению" == msg:
                    info = pd.read_sql(
                        "SELECT text FROM text_table "
                        "WHERE name_text = 'Instructions_for_use';",
                        con=engine,
                    )
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id, text=info.iloc[0, 0]
                    )
                elif "инструкция для подключения меня к чату" == msg:
                    info = pd.read_sql(
                        "SELECT text FROM text_table WHERE name_text = "
                        "'Instructions_for_implementing_the_bot_in_the_chat';",
                        con=engine,
                    )
                    text = (
                        str(info.iloc[0, 0])
                        .replace(">", "\>")
                        .replace("#", "\#")
                        .replace("+", "\+")
                        .replace("=", "\=")
                        .replace("-", "\-")
                        .replace("{", "\{")
                        .replace("}", "\}")
                        .replace(".", "\.")
                        .replace("!", "\!")
                    )
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=text,
                        parse_mode="MarkdownV2",
                    )
                elif "основные команды в чате" == msg or (
                    "люц" in msg
                    and (
                        "команды" in msg
                        or (
                            (
                                "что" in msg
                                or "че" in msg
                                or "чё" in msg
                                or "чо" in msg
                            )
                            and "умеешь" in msg
                        )
                    )
                ):
                    info = pd.read_sql(
                        "SELECT text FROM text_table "
                        "WHERE name_text = 'Basic_commands_in_the_chat';",
                        con=engine,
                    )
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id, text=info.iloc[0, 0]
                    )
                elif "инструкция по кв" == msg:
                    await manul_kv(update, context)
                elif "расписание клановых заданий" == msg:
                    await schedule_of_clan_tasks(update, context)
                elif "полезные ссылки" == msg:
                    await useful_links(update, context)
                elif "гайд по аптечкам в кв" == msg:
                    await manul_aptechkam_kv(update, context)
                elif "кого качать для получения героев из событий?" == msg:
                    await necessary_heroes_for_events(update, context)
                elif "для новичков" == msg:
                    await for_new_gamers(update, context)
                elif (
                    "как зайти в игру, "
                    "если по каким-то причинам не получается зайти" == msg
                ):
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="https://telegra.ph/Kak-zajti-v-igru-esli-po-"
                        "kakim-to-prichinam-ne-poluchaetsya-zajti-07-22-3",
                    )
                elif "кого качать в начале" == msg:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="По данному вопросу zOrg написал "
                        "[статью](https://telegra.ph/Nachalnyj-pak-11-"
                        "17)\, вот держи\!\)",
                        parse_mode="MarkdownV2",
                    )
                elif "когда кв?" == msg:
                    info = pd.read_sql(
                        "SELECT text FROM text_table "
                        "WHERE name_text = 'when_kv';",
                        con=engine,
                    )
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id, text=info.iloc[0, 0]
                    )
                elif "расписание х2, х3 и даты кв" == msg:
                    with open(
                        working_folder + "help/schedule_x2_x3.jpg", "rb"
                    ) as img:
                        await context.bot.send_photo(
                            chat_id=update.effective_chat.id,
                            photo=img,
                            caption="Расписание х2, х3 и кв на 2023г",
                        )
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="Канал с расписаниями: х2, х3 и "
                        "предположительными датами кв:\n@AoMx2",
                    )
                elif "паки и контрпаки" == msg:
                    for name in [
                        "pak_and_counterpak1",
                        "pak_and_counterpak2",
                        "pak_and_counterpak3",
                        "pak_and_counterpak4",
                        "pak_and_counterpak5",
                    ]:
                        with open(
                            working_folder + f"help/{name}.jpg", "rb"
                        ) as img:
                            await context.bot.send_photo(
                                chat_id=update.effective_chat.id, photo=img
                            )
                elif "испытания на 3*" == msg:
                    with open(
                        working_folder + "help/recent_trials.doc", "rb"
                    ) as doc:
                        await context.bot.send_document(
                            chat_id=update.effective_chat.id, document=doc
                        )
                elif "схемы всех рейдов" == msg:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text="[Схемы всех рейдов](https://drive.google.com/"
                        "folderview?id=1-9P7YK6He09vgheEQd4rK5zf-H5QXDFi)"
                        "\n\n[Схемы всех рейдов от 🔥 Li \[Феникс\]]"
                        "(https://telegra.ph/Shemy-rejdov-05-19)",
                        parse_mode="MarkdownV2",
                    )
                elif "🔙назад🔙" == msg:
                    await new_button(update, "Погнали, назад, в главное меню.")
                    if user_id in user_triger:
                        user_triger.pop(user_id)
                else:
                    await chatterbox.get_chat_text_messages(update, context)
        elif chat_type == "supergroup" or chat_type == "group":
            if f"{user_id}@{update.effective_chat.id}" in group_triger:
                triger = group_triger[f"{user_id}@{update.effective_chat.id}"][
                    "triger"
                ]
                if triger == "update_time_change_clan_task":
                    if msg.isnumeric():
                        if 1 <= int(msg) <= 24:
                            await insert_and_update_sql(
                                "UPDATE clans SET time_kz = :msg "
                                "WHERE chat_id = :chat_id;",
                                params={
                                    "msg": msg,
                                    "chat_id": update.effective_chat.id,
                                },
                            )
                            await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text="Время умпешно установлено!",
                            )
                        else:
                            await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text="Введи время по москве!",
                            )
                    else:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="Вводи цифрами",
                        )
                group_triger.pop(f"{user_id}@{update.effective_chat.id}")

            elif "id" == msg:
                try:
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id, message_id=msg_id
                    )
                except Exception:
                    await context.bot.send_message(
                        chat_id=my_tid,
                        text=f"ID: {update.effective_chat.id}\nname: \
{update.effective_chat.title}\nUser_id: {user_id}\nНе получилось удалить \
смс 'id'",
                    )
                info = pd.read_sql(
                    "SELECT COUNT(*) FROM clans "
                    "WHERE chat_id = %(chat_id)s;",
                    params={
                        "chat_id": update.effective_chat.id,
                    },
                    con=engine,
                )
                if info.loc[0, "count"] == 0:
                    await insert_and_update_sql(
                        "INSERT INTO clans(chat_id, name_clan) "
                        "VALUES(:chat_id, :name_clan);",
                        params={
                            "chat_id": update.effective_chat.id,
                            "name_clan": update.effective_chat.title,
                        },
                    )
    except Exception as error:
        # фиксируем ошибки в логи
        logging.error(f"Ошибочка вышла {error}")


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    # потключаемся к управлению ботом по токену
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # simple start function
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CommandHandler("help", helper))
    application.add_handler(CommandHandler("edit_name", edit_name))
    application.add_handler(
        CommandHandler("clan_tasks", schedule_of_clan_tasks)
    )
    application.add_handler(CommandHandler("manul_kv", manul_kv))
    application.add_handler(CommandHandler("manul_ap_kv", manul_aptechkam_kv))
    application.add_handler(
        CommandHandler("heroes_for_events", necessary_heroes_for_events)
    )
    # application.add_handler(CommandHandler('date_x2', date_x2))
    application.add_handler(
        CommandHandler("pak_and_counterpak", pak_and_counterpak)
    )
    application.add_handler(CommandHandler("useful_links", useful_links))

    # chat commands
    application.add_handler(
        CommandHandler(
            "update_time_change_clan_task", update_time_change_clan_task
        )
    )
    application.add_handler(CommandHandler("start_remin15", start_remin15))
    application.add_handler(CommandHandler("stop_remin15", stop_remin15))

    # Add callback query handler to start the payment invoice
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.ALL, handle_text))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    u_data = UserData()
    main()

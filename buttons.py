import pandas as pd

import telegram
from telegram import (
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from sqlalchemy import create_engine

from work import TELEGRAM_TOKEN, url_engine

bot = telegram.Bot(TELEGRAM_TOKEN)

engine = create_engine(url_engine)


async def send_button(
    update: Update,
    sms: str,
    reply_keyboard: list[list[str]],
) -> None:
    await bot.send_message(
        chat_id=update.effective_chat.id,
        text=sms,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=False
        ),
    )
    return


async def setting_button(
    update: Update, context: ContextTypes, sms: str
) -> None:
    """Вывод кнопок Настроек"""
    reply_keyboard = [
        ["Маницпуляции с героем"],
        ["Подписки...", "Поменять время..."],
        ["Проверить данные профиля"],
        ["🔙Назад🔙"],
    ]
    await send_button(update=update, sms=sms, reply_keyboard=reply_keyboard)
    return


async def setting_hero_button(
    update: Update, context: ContextTypes, sms: str
) -> None:
    """Манапуляции с героем"""
    reply_keyboard = []
    info = pd.read_sql(
        "SELECT COUNT(*) FROM heroes_of_users " "WHERE user_id = %(user_id)s;",
        params={"user_id": update.effective_chat.id},
        con=engine,
    )
    num = int(info.loc[0, "count"])
    if num == 5:
        reply_keyboard += [
            ["Удалить одного героя"],
            ["Переименовать героя"],
            ["🔙Назад🔙"],
        ]
    elif num == 1:
        reply_keyboard += [
            ["Добавить еще одного героя"],
            ["Переименовать героя"],
            ["🔙Назад🔙"],
        ]
    else:
        reply_keyboard += [
            ["Добавить еще одного героя"],
            ["Удалить одного героя"],
            ["Переименовать героя"],
            ["🔙Назад🔙"],
        ]
    await send_button(update=update, sms=sms, reply_keyboard=reply_keyboard)
    return


async def subscription_button(
    update: Update, context: ContextTypes, sms: str
) -> None:
    """Подписки..."""
    subscription = pd.read_sql(
        "SELECT subscription_rock, subscription_energy FROM users"
        "WHERE user_id = %(user_id)s;",
        params={"user_id": update.effective_chat.id},
        con=engine,
    )
    reply_keyboard = []
    if subscription.loc[0, "subscription_rock"]:
        reply_keyboard += [["Отписаться от напоминалки о смене КЗ за час"]]
    else:
        reply_keyboard += [["Подписаться на напоминалку о смене КЗ за час"]]
    if subscription.loc[0, "subscription_energy"]:
        reply_keyboard += [["Отписаться от напоминалки по сбору энергии"]]
    else:
        reply_keyboard += [["Подписаться на напоминалку по сбору энергии"]]
    if subscription.loc[0, "description_of_the_kz"]:
        reply_keyboard += [["Отписаться от ежедневного описания КЗ"]]
    else:
        reply_keyboard += [["Подписаться на ежедневное описание КЗ"]]
    reply_keyboard += [["🔙Назад🔙"]]
    await send_button(update=update, sms=sms, reply_keyboard=reply_keyboard)
    return


async def edit_time_button(
    update: Update, context: ContextTypes, sms: str
) -> None:
    """Поменять время..."""
    reply_keyboard = [
        ["Поменять время смены КЗ"],
        ["Поменять время первого сбора энергии"],
        ["🔙Назад🔙"],
    ]
    await send_button(update=update, sms=sms, reply_keyboard=reply_keyboard)
    return


async def new_button(update: Update, context: ContextTypes, sms: str) -> None:
    """Вывод кнопок"""
    reply_keyboard = [
        ["🆘 Помощь 🆘"],
        ["Сколько у меня камней?", "Полезная информация"],
        ["⚙️Настройка профиля⚙️"],
    ]
    info = pd.read_sql("SELECT user_id FROM admins;", engine)
    if update.effective_chat.id in info["user_id"].to_list():
        reply_keyboard += [["Настройки Админа"]]
    await send_button(update=update, sms=sms, reply_keyboard=reply_keyboard)
    return


async def setting_admin_button(
    update: Update, context: ContextTypes, sms: str
) -> None:
    """Вывод кнопок админовских настроек"""
    reply_keyboard = [
        [
            "Отправить напоминалку игроку ✏️✉️🧍‍♂️",
            "Редактировать сообщение напоминалки 📝",
            "Написать от имени бота🤖",
        ],
        ["Отправить ВСЕМ сообщение ✏️✉️👨‍👩‍👧‍👦", "Убрать игрока из клана☠"],
        ["🔙Назад🔙"],
    ]
    await send_button(update=update, sms=sms, reply_keyboard=reply_keyboard)
    return


async def help_my_button(
    update: Update, context: ContextTypes, sms: str
) -> None:
    """Вывод кнопок помощи"""
    reply_keyboard = [
        ["Инструкция по применению"],
        ["Инструкция для подключения меня к чату"],
        ["Основные команды в чате"],
        ["🔙Назад🔙"],
    ]
    await send_button(update=update, sms=sms, reply_keyboard=reply_keyboard)
    return


async def help_button(update: Update, context: ContextTypes, sms: str) -> None:
    """Вывод кнопок помощи"""
    reply_keyboard = [
        ["Для новичков"],
        ["Как зайти в игру, если по каким-то причинам не " "получается зайти"],
        [
            "Кого качать в начале",
            "Кого качать для получения героев из событий?",
        ],
        ["Полезные ссылки"],
        ["Когда КВ?", "Расписание х2, х3 и даты КВ"],
        ["Инструкция по КВ", "Гайд по аптечкам в КВ"],
        ["Паки и контрпаки", "Испытания на 3*"],
        ["Схемы всех рейдов"],
        ["Расписание клановых заданий"],
        ["🔙Назад🔙"],
    ]
    await send_button(update=update, sms=sms, reply_keyboard=reply_keyboard)
    return


async def cancel_button(
    update: Update, context: ContextTypes, sms: str
) -> None:
    reply_keyboard = [["Отмена"]]
    await send_button(update=update, sms=sms, reply_keyboard=reply_keyboard)
    return

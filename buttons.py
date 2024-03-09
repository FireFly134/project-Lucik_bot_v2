#!/usr/bin/python

import telegram
import pandas as pd

from work import *
from telegram import ReplyKeyboardMarkup
from sqlalchemy import create_engine

bot = telegram.Bot(token_test)  # _test

engine = create_engine(BD)


def setting_button(update, context, sms):  ### Вывод кнопок Настроек
    reply_keyboard = [
        ["Маницпуляции с героем"],
        ["Подписки...", "Поменять время..."],
        ["Проверить данные профиля"],
        ["🔙Назад🔙"],
    ]
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=sms,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=False
        ),
    )


def setting_hero_button(update, context, sms):  # Манапуляции с героем
    reply_keyboard = []
    info = pd.read_sql(
        f"SELECT * FROM users WHERE user_id = '{update.effective_chat.id}';",
        engine,
    )
    num = int(info.loc[0, "num_pers"])
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
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=sms,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=False
        ),
    )


def Subscription_button(update, context, sms):  # Подписки...
    subscription = pd.read_sql(
        f"SELECT subscription_rock, subscription_energy FROM users WHERE user_id = '{update.effective_chat.id}';",
        engine,
    )
    reply_keyboard = []
    if subscription.loc[0, "subscription_rock"]:
        reply_keyboard += [["Отписаться от напоминалки по камням"]]
    else:
        reply_keyboard += [["Подписаться на напоминалку по камням"]]
    if subscription.loc[0, "subscription_energy"]:
        reply_keyboard += [["Отписаться от напоминалки по сбору энергии"]]
    else:
        reply_keyboard += [["Подписаться на напоминалку по сбору энергии"]]
    reply_keyboard += [["🔙Назад🔙"]]
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=sms,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=False
        ),
    )


def edit_time_button(update, context, sms):  # Поменять время...
    reply_keyboard = [
        ["Поменять время смены КЗ"],
        ["Поменять время первого сбора энергии"],
        ["🔙Назад🔙"],
    ]
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=sms,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=False
        ),
    )


def new_button(update, context, sms):  ### Вывод кнопок
    reply_keyboard = [
        ["🆘 Помощь 🆘"],
        ["Сколько у меня камней?", "Полезная информация"],
        ["⚙️Настройка профиля⚙️"],
    ]
    info = pd.read_sql("SELECT user_id FROM admins;", engine)
    admins = list(info.user_id.values)
    if update.effective_chat.id in admins:
        reply_keyboard += [["Настройки Админа"]]
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=sms,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=False
        ),
    )


def setting_admin_button(
    update, context, sms
):  ### Вывод кнопок админовских настроек
    reply_keyboard = [
        [
            "Отправить напоминалку игроку ✏️✉️🧍‍♂️",
            "Редактировать сообщение напоминалки 📝",
            "Написать от имени бота🤖",
        ],
        ["Отправить ВСЕМ сообщение ✏️✉️👨‍👩‍👧‍👦", "Убрать игрока из клана☠"],
        ["🔙Назад🔙"],
    ]
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=sms,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=False
        ),
    )


def helpMy_button(update, context, sms):  ### Вывод кнопок помощи
    reply_keyboard = [
        ["Инструкция по применению"],
        ["Инструкция для подключения меня к чату"],
        ["Основные команды в чате"],
        ["🔙Назад🔙"],
    ]
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=sms,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=False
        ),
    )


def help_button(update, context, sms):  ### Вывод кнопок помощи
    reply_keyboard = [
        ["Инструкция по КВ"],
        ["Расписание клановых заданий"],
        ["Полезные ссылки"],
        ["Гайд по аптечкам в КВ"],
        ["Необходимые герои для ивентов"],
        ["🔙Назад🔙"],
    ]
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=sms,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=False
        ),
    )


def cancel_button(update, context, sms):
    reply_keyboard = [["Отмена"]]
    bot.send_message(
        chat_id=update.effective_chat.id,
        text=sms,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, resize_keyboard=True, one_time_keyboard=False
        ),
    )

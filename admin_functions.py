import buttons

import pandas as pd

from sqlalchemy import create_engine

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from work import url_engine

engine = create_engine(url_engine)

user_triger = {}


async def check_of_admin(user_id: int | str) -> bool:
    info = pd.read_sql(
        "SELECT user_id, text_for_clan"
        "FROM admins WHERE user_id = %(user_id)s;",
        params={"user_id": user_id},
        con=engine,
    )
    if not info.empty:
        return True
    else:
        return False


async def admin_menu(update: Update, context: ContextTypes) -> None:
    """Получаем информацию, кто в клане и можем нажав на любого скинуть \
шаблонное смс"""
    info = pd.read_sql(
        "SELECT user_id, name_clan "
        "FROM admins WHERE user_id = %(user_id)s;",
        params={"user_id": update.effective_chat.id},
        con=engine,
    )
    if not info.empty:
        keyboard = []
        show_user_clan = pd.read_sql(
            "SELECT user_id, name0, rock0 "
            "FROM users WHERE clan = %(clan)s;",
            params={"clan": info.loc[0, "name_clan"]},
            con=engine,
        )
        for idx, row in show_user_clan.iterrows():
            keyboard += [
                [
                    InlineKeyboardButton(
                        f'{row["name0"]}-{row["rock0"]}',
                        callback_data=f'send-{row["user_id"]}',
                    )
                ]
            ]
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Все игроки клана:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def admin_menu2(update: Update, context: ContextTypes) -> None:
    """Редактируем шаблон смс для отправки"""
    if check_of_admin(update.effective_chat.id):
        buttons.cancel_button(
            update, context, "Что будем отправлять непослушным деткам?"
        )
        user_triger[update.effective_chat.id] = {"triger": "edit_send"}


async def admin_send_msg_all_user_clan(
    update: Update, context: ContextTypes
) -> None:
    """Отправить всем из клана СМС"""
    if check_of_admin(update.effective_chat.id):
        buttons.cancel_button(update, context, "Ну, погнали, что отправим?")
        user_triger[update.effective_chat.id] = {
            "triger": "send_msg_all_user_clan"
        }


async def admin_menu4(update: Update, context: ContextTypes) -> None:
    """Удаление из клана"""
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


async def chat_sms(update: Update, context: ContextTypes) -> None:
    """Отправить смс в чат от имени бота"""
    if update.effective_chat and context:
        if check_of_admin(user_id=update.effective_chat.id):
            buttons.cancel_button(update, context, "Что написать в чате?")
            user_triger[update.effective_chat.id] = {"triger": "send_chat"}

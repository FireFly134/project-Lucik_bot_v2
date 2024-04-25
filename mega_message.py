import asyncio
import logging

import pandas as pd

from sqlalchemy import create_engine

import telegram

from work import (
    TELEGRAM_TOKEN,
    url_engine,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(process)d-%(levelname)s %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

engine = create_engine(url_engine)

bot = telegram.Bot(TELEGRAM_TOKEN)


async def main() -> None:
    id_list = []
    info = pd.read_sql(
        "SELECT user_id, name FROM heroes_of_users "
        "WHERE time_change_kz = '18' "
        "AND time_collection_energy = '12';",
        engine,
    )
    sms = """Привет, я заметил что ты не менял время\.
Сейчас время смены кланового задания установлено __18:30__, \
а первый сбор бесплатной энергии установлен на __12:00__ \(__*по МСК*__\)\.

*Если данное время неверно, то это можно с лёгкостью изменить в настройках\!*
Для этого нажми *Настройка профиля* \-\-\-\> *Поменять время\.\.\.*

*Так же можно __бесплатно__ подписаться на напоминалки\!*
Чтобы это сделать проходим *Настройка профиля* \-\-\-\> *Подписки\.\.\.*
"""

    for idx, row in info.iterrows():
        if row["user_id"] not in id_list:
            id_list.append(row["user_id"])
            await send_msg_markdown_v2(
                str(row["user_id"]),
                sms,
            )


async def send_msg_markdown_v2(user_id: str, sms: str) -> None:
    try:
        await bot.send_message(
            chat_id=user_id, text=sms, parse_mode="MarkdownV2"
        )
    except Exception as err:
        logging.error(err)
        logging.info(f"Пользователь с id = {user_id}")


if __name__ == "__main__":
    asyncio.run(main())

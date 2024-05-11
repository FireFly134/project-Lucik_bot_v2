import logging
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine

import telegram
from threading import Thread

from send_query_sql import insert_and_update_sql
from work import url_engine, TELEGRAM_TOKEN


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(process)d-%(levelname)s %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

engine = create_engine(url_engine)

bot = telegram.Bot(TELEGRAM_TOKEN)


def correction_name(name) -> str:
    return (
        str(name)
        .replace("_", "\_")
        .replace("*", "\*")
        .replace("[", "\[")
        .replace("]", "\]")
        .replace("(", "\(")
        .replace(")", "\)")
        .replace("`", "\`")
        .replace("~", "\~")
        .replace(">", "\>")
        .replace("#", "\#")
        .replace("+", "\+")
        .replace("=", "\=")
        .replace("-", "\-")
        .replace("|", "\|")
        .replace("{", "\{")
        .replace("}", "\}")
        .replace(".", "\.")
        .replace("!", "\!")
    )


def update_clan_task(
    info: pd.DataFrame,
    name_column: str = "time_change_kz",
    clan_chat: bool = False,
) -> None:
    time_kz = time + timedelta(hours=1)
    # Ищем героев (клан чат) у которых смена КЗ через час
    info_kz = info[info[name_column] == int(time_kz.strftime("%H"))]
    # И одновременно они подписан на напоминалку
    info_kz = info_kz[info_kz["subscription_rock"] == 1]
    # Напоминание про смену КЗ
    if not info_kz.empty:
        logging.info(f"info_kz GO = {len(info_kz)}")
        logging.info(f"{clan_chat=}")
        for idx, row in info_kz.iterrows():
            sms = "До смены кланового задания остался 1 час!"
            if not clan_chat:
                sms += f" ({row['name']})"
            t = Thread(
                target=send_msg,
                args=(
                    row["user_id"],
                    sms,
                ),
            )
            t.start()
            logging.info(f"info_kz START idx = {idx}")
            t.join()
            logging.info(f"info_kz END idx = {idx}")
    return


def information_about_new_clan_task(
    info: pd.DataFrame,
    name_column: str = "time_change_kz",
    clan_chat: bool = False,
) -> None:
    # Ищем героев или чат у которых смена сейчас КЗ
    info_kz_description = info[info[name_column] == int(time.strftime("%H"))]
    # И одновременно они подписан на описание заданий
    info_kz_description = info_kz_description[
        info_kz_description["description_of_the_kz"] == 1
    ]
    if not info_kz_description.empty:
        logging.info(f"info_kz_description GO = {len(info_kz_description)}")
        info = pd.read_sql(
            "SELECT text FROM text_table " "WHERE name_text = %(time)s;",
            params={"time": int(time.strftime("%w"))},
            con=engine,
        )
        if not info.empty:
            for idx, row in info_kz_description.iterrows():
                sms = ""
                if not clan_chat:
                    sms += f"{correction_name(row['name'])}\!\n"
                    chat_id = row["user_id"]
                else:
                    chat_id = row["chat_id"]
                sms += str(info.loc[0, "text"])
                t = Thread(
                    target=send_msg,
                    args=(
                        chat_id,
                        sms,
                    ),
                )
                t.start()
                logging.info(f"info_kz_description START idx = {idx}")
                t.join()
                logging.info(f"info_kz_description END idx = {idx}")
    return


def reminder_kz() -> None:
    time_kz = time + timedelta(hours=1)

    # Получаем данные по всем героям
    info_heroes_of_users = pd.read_sql(
        "SELECT id, rock, user_id, name, time_change_kz, "
        "   subscription_rock, description_of_the_kz "
        "FROM heroes_of_users"
        "WHERE subscription_rock = 'true' OR description_of_the_kz = 'true';",
        engine,
    )

    # Получаем данные по всем кланам
    info_clans = pd.read_sql(
        "SELECT * FROM clans " "WHERE start = 'True' AND chat_id IS NOT NULL;",
        engine,
    )

    # Оповещение об обновлении в личку игрокам
    update_clan_task(info_heroes_of_users)
    information_about_new_clan_task(info_heroes_of_users)

    # Оповещение об обновлении в клан чате
    update_clan_task(info_clans, name_column="time_kz", clan_chat=True)
    information_about_new_clan_task(
        info_clans, name_column="time_kz", clan_chat=True
    )


def reminder_zero(text="До обнуления камушков остался 1 час!") -> None:
    info_clans = pd.read_sql(
        "SELECT * FROM clans "
        "WHERE start = 'True'"
        " AND remain_zero_rock = 'True'"
        " AND chat_id IS NOT NULL;",
        engine,
    )
    # Напоминание в чат про смену КЗ
    for idx, row in info_clans.iterrows():
        t = Thread(
            target=send_msg,
            args=(
                row["chat_id"],
                text,
            ),
        )
        t.start()
        logging.info(f"reminder_zero_Clan START idx = {idx}")
        t.join()
        logging.info(f"reminder_zero_Clan END idx = {idx}")


def clear_rock() -> None:
    info_heroes_of_users = pd.read_sql(
        "SELECT id FROM heroes_of_users WHERE rock > 0;", engine
    )
    logging.info(f"clear_rock GO = {len(info_heroes_of_users)}")
    list_id_hero = info_heroes_of_users["id"].to_list()
    # list_id_hero = list(set(info_heroes_of_users["id"].tolist()))
    # list_to_zero = [str(id_hero) for id_hero in list_id_hero]
    str_list_to_zero = str(list_id_hero).replace("[", "(").replace("]", ")")
    insert_and_update_sql(
        "UPDATE heroes_of_users SET rock = '0' "
        f"WHERE id in {str_list_to_zero};"
    )
    reminder_zero(text="Камушки обнулились. Пора набивать новые!😎")


def reminder_energy() -> None:
    """Проверяем в БД кто подписан на напоминалку по энергии
    и кому пора напоминать"""
    time2_energy = time - timedelta(hours=6)
    time3_energy = time - timedelta(hours=9)
    info_energy = pd.read_sql(
        "SELECT user_id, name FROM heroes_of_users "
        "WHERE (time_collection_energy = %(time)s"
        " OR time_collection_energy = %(time2_energy)s"
        " OR time_collection_energy = %(time3_energy)s)"
        " AND subscription_energy = 'True';",
        params={
            "time": int(time.strftime("%H")),
            "time2_energy": int(time2_energy.strftime("%H")),
            "time3_energy": int(time3_energy.strftime("%H")),
        },
        con=engine,
    )
    for idx, row in info_energy.iterrows():
        name = correction_name(row["name"])
        t = Thread(
            target=send_msg_markdown_v2,
            args=(
                row["user_id"],
                f"*Зайди в игру и забери халявную энергию*\. \({name}\)",
            ),
        )
        t.start()
        t.join()


def send_msg(user_id, sms) -> None:
    try:
        bot.send_message(chat_id=user_id, text=sms)
    except Exception as err:
        logging.error(err)
        logging.info(f"Пользователь с id = {user_id}")


def send_msg_markdown_v2(user_id, sms) -> None:
    """
    In all other places characters
    '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|',
    '{', '}', '.', '!' must be escaped with the preceding character ''.
    """
    try:
        bot.send_message(chat_id=user_id, text=sms, parse_mode="MarkdownV2")
    except Exception as err:
        logging.error(err)
        logging.info(f"Пользователь с id = {user_id}")


if __name__ == "__main__":
    time = datetime.now()  # текущее время
    # Проверка на наличия энергии по времени для подписчиков
    if int(time.strftime("%M")) == 0:
        reminder_energy()
        if int(time.strftime("%H")) == 14:
            reminder_zero()
        if int(time.strftime("%H")) == 15:
            clear_rock()

    if int(time.strftime("%M")) == 30:
        reminder_kz()

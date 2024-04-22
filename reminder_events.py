# coding=UTF-8
#
#
import logging
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine

import telegram
from threading import Thread

from work import *

#########################################################
### настройка лога, прописываем куда будет помещаться ###
#########################################################
logging.basicConfig(
    filename=working_folder + "send_msg_errors.log",
    filemode="a",
    level=logging.INFO,
    format="%(asctime)s %(process)d-%(levelname)s %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
#########################################################
#########################################################
#########################################################

engine = create_engine(db)

bot = telegram.Bot(
    TOKEN
)  # - эта строка используется только когда мы используем отдельный файл чисто для отправки (смс, документов...) оповещения, тут она не нужно


def main():
    time = datetime.now()  # текущее время
    time_add_two_days = time + timedelta(days=2)
    time_add_two_week = time + timedelta(
        days=16
    )  # через 2 дня будет ивент и через 2 недели будет повтор поэтому 14+2=16
    ### Проверка на наличия энергии по времени для подписчиков ###
    info_event = pd.read_sql(
        f"SELECT * FROM check_events WHERE date = '{str(time_add_two_days)[:10]}';",
        engine,
    )
    info_user = pd.read_sql("SELECT user_id FROM telegram_users_id;", engine)
    if len(info_event) != 0:
        engine.execute(
            f"UPDATE check_events SET date = '{str(time_add_two_week)[:10]} 00:00:00.0' WHERE date = '{str(time_add_two_days)[:10]}';"
        )
        for idx, row in info_event.iterrows():
            text = (
                str(row["description"])
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
            for idx, row_us in info_user.iterrows():
                t = Thread(
                    target=send_msg,
                    args=(
                        str(row_us["user_id"]),
                        f"*Через два дня {text}*",
                    ),
                )
                t.start()
                t.join()

    # Просыпаемся каждые 30 мин и проверяем


def send_msg(user_id, sms):
    try:
        bot.send_message(chat_id=user_id, text=sms, parse_mode="MarkdownV2")
    except Exception as err:
        logging.error(err)
        logging.info(f"Пользователь с id = {user_id}")


if __name__ == "__main__":
    main()

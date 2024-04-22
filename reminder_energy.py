# coding=UTF-8
#
#
import logging
from datetime import datetime, timedelta
from time import sleep
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
    # Узнаём сколько нужно проспать до следующего часа и 0 мин.
    sleep_time = (
        datetime.strptime(f"{int(time.strftime('%H')) + 1}:00:00", "%H:%M:%S")
        - time
    )
    sleep(sleep_time.seconds)
    while True:
        time = datetime.now()  # текущее время
        ### Проверка на наличия энергии по времени для подписчиков ###
        if int(time.strftime("%M")) == 0:
            time2_energy = time - timedelta(hours=6)
            time3_energy = time - timedelta(hours=9)
            # info_energy = pd.read_sql(f"SELECT user_id, name FROM heroes_of_users WHERE (time_collection_energy = '{int(time.strftime('%H'))}' OR time_collection_energy = '{int(time2_energy.strftime('%H'))}' OR time_collection_energy = '{int(time3_energy.strftime('%H'))}') AND subscription_energy = '1';", engine)
            info_energy = pd.read_sql(
                f"SELECT user_id, name FROM heroes_of_users WHERE (time_collection_energy = '{int(time.strftime('%H'))}' OR time_collection_energy = '{int(time2_energy.strftime('%H'))}' OR time_collection_energy = '{int(time3_energy.strftime('%H'))}') AND subscription_energy = 'True';",
                engine,
            )
            if len(info_energy) != 0:
                for idx, row in info_energy.iterrows():
                    name = (
                        str(row["name"])
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
                    t = Thread(
                        target=send_msg,
                        args=(
                            row["user_id"],
                            f"*Зайди в игру и забери халявную энергию*\. \({name}\)",
                        ),
                    )
                    t.start()
                    t.join()
            # Просыпаемся каждые 30 мин и проверяем
            sleep(1800)


def send_msg(user_id, sms):
    try:
        bot.send_message(chat_id=user_id, text=sms, parse_mode="MarkdownV2")
    except Exception as err:
        logging.error(err)
        logging.info(f"Пользователь с id = {user_id}")


if __name__ == "__main__":
    main()

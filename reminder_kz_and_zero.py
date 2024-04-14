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
logging.basicConfig(filename=working_folder + 'send_msg_errors_zero.log',
                    filemode='a',
                    level=logging.INFO,
                    format='%(asctime)s %(process)d-%(levelname)s %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')
#########################################################
#########################################################
#########################################################

engine = create_engine(db)

bot = telegram.Bot(TOKEN) # - эта строка используется только когда мы используем отдельный файл чисто для отправки (смс, документов...) оповещения, тут она не нужно

def main():
    time = datetime.now()  # текущее время
    # Узнаём сколько нужно проспать до следующего часа и 0 мин.
    sleep_time1 = datetime.strptime(f"{int(time.strftime('%H'))}:30:00", "%H:%M:%S") - time
    sleep_time2 = datetime.strptime(f"{int(time.strftime('%H')) + 1}:30:00", "%H:%M:%S") - time
    if sleep_time1.seconds < 1800:
        # print(sleep_time1.seconds)
        sleep(sleep_time1.seconds)
    else:
        # print(sleep_time2.seconds)
        sleep(sleep_time2.seconds)
    while True:
        time = datetime.now() #текущее время
        ### Проверка на наличия энергии по времени для подписчиков ###
        if int(time.strftime("%M")) == 30:
            time_kz = time + timedelta(hours=1)
            info_heroes_of_users = pd.read_sql(f"SELECT id, rock, user_id, name, time_change_kz, subscription_rock, description_of_the_kz FROM heroes_of_users;", engine)
            # info_clans_kz = pd.read_sql(f"SELECT chat_id FROM clans WHERE time_kz = '{int(time_kz.strftime('%H'))}' AND chat_id IS NOT NULL;", engine)
            info_clans = pd.read_sql(f"SELECT chat_id FROM clans WHERE start = 'True' AND chat_id IS NOT NULL;", engine)

            info_kz = info_heroes_of_users[info_heroes_of_users['time_change_kz'] == int(time_kz.strftime('%H'))]
            info_kz = info_kz[info_kz['subscription_rock'] == 1]
            info_kz_info = info_heroes_of_users[info_heroes_of_users['time_change_kz'] == int(time.strftime('%H'))]
            info_kz_zero = info_kz_info[info_kz_info['rock'] > 0]
            info_kz_info = info_kz_info[info_kz_info['description_of_the_kz'] == 1]
            logging.info(f"info_kz len() = {len(info_kz)}")
            logging.info(f"info_clans_kz len() = {len(info_clans_kz)}")
            logging.info(f"info_kz_zero len() = {len(info_kz_zero)}")
            logging.info(f"info_kz_info len() = {len(info_kz_info)}")

            ### Напоминание в личку про смену КЗ ###
            if len(info_kz) != 0:
                logging.info(f"info_kz GO = {len(info_kz)}")
                for idx, row in info_kz.iterrows():
                    t = Thread(target=send_msg, args=(row['user_id'], f"До смены кланового задания остался 1 час! ({row['name']})",))
                    t.start()
                    logging.info(f"info_kz START idx = {idx}")
                    t.join()
                    logging.info(f"info_kz END idx = {idx}")

            if len(info_kz_zero) != 0:
                logging.info(f"info_kz_zero GO = {len(info_kz_zero)}")
                list_to_zero = [str(id_hero) for id_hero in info_kz_zero['id'].tolist()]
                engine.execute(f"UPDATE heroes_of_users SET rock = '0' WHERE id in {str(list_to_zero).replace('[','(').replace(']',')')};")

            if len(info_kz_info) != 0:
                logging.info(f"info_kz_info GO = {len(info_kz_info)}")
                info = pd.read_sql(f"SELECT text FROM text_table WHERE name_text = '{int(time.strftime('%w'))}';", engine)
                if len(info) != 0:
                    for idx, row in info_kz_info.iterrows():
                        name = str(row['name']).replace('_', '\_').replace('*', '\*').replace('[', '\[').replace(']', '\]').replace('(', '\(').replace(')', '\)').replace('`', '\`').replace('~', '\~').replace('>', '\>').replace('#', '\#').replace('+', '\+').replace('=', '\=').replace('-', '\-').replace('|', '\|').replace('{', '\{').replace('}', '\}').replace('.', '\.').replace('!', '\!')
                        t = Thread(target=send_msg_MarkdownV2, args=(row['user_id'], f"{name}\!\n{info.loc[0, 'text']}",))
                        t.start()
                        logging.info(f"info_kz_info START idx = {idx}")
                        t.join()
                        logging.info(f"info_kz_info END idx = {idx}")

            ### Напоминание в чат про смену КЗ ###
            info_clans_kz = info_clans[info_clans['time_kz'] == int(time_kz.strftime('%H'))]
            info_clans_kz = info_clans_kz[info_clans_kz['subscription_rock'] == 1]
            if len(info_clans_kz) != 0:
                logging.info(f"info_clans_kz GO = {len(info_clans_kz)}")
                for idx, row in info_clans_kz.iterrows():
                    t = Thread(target=send_msg, args=(row['chat_id'], "До смены кланового задания остался 1 час!",))
                    t.start()
                    logging.info(f"info_clans_kz START idx = {idx}")
                    t.join()
                    logging.info(f"info_clans_kz END idx = {idx}")

            ### Описание нового КЗ в чат ###
            info_clans_description_of_the_kz = info_clans[info_clans['time_kz'] == int(time.strftime('%H'))]
            info_clans_description_of_the_kz = info_clans_description_of_the_kz[info_clans_description_of_the_kz['description_of_the_kz'] == 1]
            if len(info_clans_description_of_the_kz) != 0:
                logging.info(f"info_clans_description_of_the_kz GO = {len(info_clans_description_of_the_kz)}")
                info = pd.read_sql(f"SELECT text FROM text_table WHERE name_text = '{int(time.strftime('%w'))}';", engine)
                if len(info) != 0:
                    for idx, row in info_clans_description_of_the_kz.iterrows():
                        t = Thread(target=send_msg_MarkdownV2, args=(row['chat_id'], f"{info.loc[0, 'text']}",))
                        t.start()
                        logging.info(f"info_clans_description_of_the_kz START idx = {idx}")
                        t.join()
                        logging.info(f"info_clans_description_of_the_kz END idx = {idx}")
            # Просыпаемся каждые 30 мин и проверяем
            sleep(1800)

def send_msg(user_id,sms):
    try:
        bot.send_message(chat_id=user_id, text=sms)
    except Exception as err:
        logging.error(err)
        logging.info(f"Пользователь с id = {user_id}")

def send_msg_MarkdownV2(user_id,sms):
    "In all other places characters '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!' must be escaped with the preceding character '\'."
    try:
        bot.send_message(chat_id=user_id, text=sms, parse_mode='MarkdownV2')
    except Exception as err:
        logging.error(err)
        logging.info(f"Пользователь с id = {user_id}")

if __name__ == "__main__":
    main()


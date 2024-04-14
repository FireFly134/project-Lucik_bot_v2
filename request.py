import logging
import os.path
import time
import requests
import json
import datetime

import pandas as pd
from sqlalchemy import create_engine

import telegram
from threading import Thread

from work import (
    TELEGRAM_TOKEN,
    url_engine,
    ACCESS_TOKEN,
    working_folder,
    my_tid,
)

bot = telegram.Bot(TELEGRAM_TOKEN)
engine = create_engine(url_engine)

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/105.0.0.0 Safari/537.36"
}
URL = 'https://api.vk.com/method/wall.get',
v = 5.131
domain = 'ageofmagicgame'




#########################################################
### настройка лога, прописываем куда будет помещаться ###
#########################################################
logging.basicConfig(filename=working_folder + 'post_errors.log',
                    filemode='a',
                    level=logging.INFO,
                    format='%(asctime)s %(process)d-%(levelname)s %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')
########################################################
#########################################################
#########################################################


def data_collection() -> None:
    while True:
        try:
            posts_list = []
            r = requests.get(
                'https://api.vk.com/method/wall.get',
                headers=headers,
                params={
                        'access_token': ACCESS_TOKEN,
                        'v': v,
                        'domain': domain,
                        'count': 5
                        }
            )

            data = r.json()['response']['items']
            items_id = []
            for item in data:
                timestamp = item['date']
                value = datetime.datetime.fromtimestamp(timestamp)
                date_pub = value.strftime('%Y-%m-%d')
                images = []

                for i in range(len(item['attachments'])):
                    if item['attachments'][i]['type'] == 'photo':
                        max_val = max([sizes['height'] for sizes in item['attachments'][i]['photo']['sizes']])
                        for dist in item['attachments'][i]['photo']['sizes']:
                            if dist['height'] == max_val:
                                images.append(dist['url'])
                                break
                if items_id not in posts_list:
                    posts_list.append(
                        {
                            'id': item['id'],
                            'text': item['text'],
                            'photo': images,
                            'date_pub': date_pub
                        }
                    )
                    items_id.append({'id': item['id']})
            if os.path.isfile(working_folder + 'post_id.txt'):
                with open(working_folder + 'post_id.txt', 'r') as file:
                    post_id = file.read()
            else:
                post_id = '0'

            date = '1994-10-07'
            num = 0

            for i in range(len(posts_list)):
                if posts_list[i]['date_pub'] > date:
                    date = posts_list[i]['date_pub']
                    num = i
            if str(post_id) != str(posts_list[num]['id']):
                post_id = str(posts_list[num]['id'])
                with open(working_folder + 'posts_data.json', 'w') as file:
                    json.dump(posts_list, file, indent=4)
                with open(working_folder + 'post_id.txt', 'w') as file:
                    file.write(post_id)
                info = pd.read_sql(
                    "SELECT chat_id FROM clans "
                    "WHERE news = 'True' AND start = 'True';",
                    engine)
                for idx, row in info.iterrows():
                    t = Thread(target=send_post, args=(row['chat_id'], num,))
                    t.start()
                    t.join()

        except Exception as err:
            logging.info(f"Ошибка при попытке парсинга: {err}")
        time.sleep(300)

def send_post(chat_id: str | int = my_tid, num: int = 1) -> None:
    try:
        with open(working_folder + 'posts_data.json') as file:
            posts_list = json.load(file)
        media_group = []
        for i in range(len(posts_list[num]['photo'])):
            if media_group == []:
                media_group.append(
                    telegram.InputMediaPhoto(
                        posts_list[num]['photo'][i],
                        posts_list[num]['text']
                    )
                )
            else:
                media_group.append(
                    telegram.InputMediaPhoto(posts_list[num]['photo'][i])
                )
        try:
            bot.send_media_group(chat_id=chat_id, media=media_group)
        except telegram.error.BadRequest:
            media_group[0] = telegram.InputMediaPhoto(
                posts_list[num]['photo'][0]
            )
            bot.send_media_group(chat_id=chat_id, media=media_group)
            bot.send_message(chat_id=chat_id, text=posts_list[num]['text'])
    except Exception as err:
        logging.info(
            f"Ошибка при попытке отправить пост в группу {chat_id}: {err}"
        )
    return


if __name__ == '__main__':
    data_collection()
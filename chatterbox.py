import pandas as pd

import telegram
from telegram import (
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from random import randint
from datetime import datetime, timedelta

from sqlalchemy import create_engine

from work import TELEGRAM_TOKEN, url_engine

bot = telegram.Bot(TELEGRAM_TOKEN)

engine = create_engine(url_engine)


async def get_chat_text_messages(
    update: Update, context: ContextTypes
) -> None:
    """Балтовня в чате"""
    if update.effective_chat:

        await bot.send_message(
            chat_id=update.effective_chat.id, text=str(update.edited_message)
        )
    if update.message:
        user_id = update.message.from_user.id  # записываем ID с телеги
        msg = update.message.text
        msg_id = update.message.message_id
        chat_type = update.message.chat.type
    else:
        user_id = update.edited_message.from_user.id
        msg = update.edited_message.text
        msg_id = update.edited_message.message_id
        chat_type = update.edited_message.chat.type

    if (
        ("спс" in msg.lower() or "спасиб" in msg.lower())
        and chat_type == "private"
    ) or (
        "люц" in msg.lower()
        and ("спс" in msg.lower() or "спасиб" in msg.lower())
        and (chat_type == "supergroup" or chat_type == "group")
    ):
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text="Всегда пожалуйста! ;)",
            reply_to_message_id=msg_id,
        )
    elif (
        "люц" in msg.lower()
        and ("красав" in msg.lower() or "молодец" in msg.lower())
        and (chat_type == "supergroup" or chat_type == "group")
    ):
        rand_num = randint(1, 3)
        if rand_num == 1:
            await bot.send_message(
                chat_id=update.effective_chat.id,
                text="Спасибо ☺️",
                reply_to_message_id=msg_id,
            )
        elif rand_num == 2:
            await bot.send_message(
                chat_id=update.effective_chat.id,
                text="Рад стараться! ☺️",
                reply_to_message_id=msg_id,
            )
        elif rand_num == 3:
            with open(f"./molodec.tgs", "rb") as sticker:
                await bot.send_sticker(
                    chat_id=update.effective_chat.id,
                    sticker=sticker,
                    reply_to_message_id=msg_id,
                )
    elif (
        "люц" in msg.lower()
        and ("врем" in msg.lower() or "кон" in msg.lower())
        and "кз" in msg.lower()
        and (chat_type == "supergroup" or chat_type == "group")
    ):
        info = pd.read_sql(
            f"SELECT * FROM users WHERE user_id = '{update.effective_chat.id}';",
            engine,
        )
        hours = int(info.loc[0, "time_change_KZ"])
        now = datetime.now()
        time1 = timedelta(
            days=now.day,
            hours=now.hour,
            minutes=now.minute,
            seconds=now.second,
        )
        time2 = timedelta(days=now.day, hours=hours, minutes=30, seconds=0)
        time3 = time2 - time1
        if time3.days == -1:
            time2 = timedelta(
                days=now.day + 1, hours=hours, minutes=30, seconds=0
            )
            time3 = time2 - time1
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text="До обновления К.З. осталось " + str(time3),
            reply_to_message_id=msg_id,
        )
    elif "id" == msg.lower() and (
        chat_type == "supergroup" or chat_type == "group"
    ):
        try:
            await bot.delete_message(
                chat_id=update.effective_chat.id, message_id=msg_id
            )
        except Exception as err:
            print(err)
        info = pd.read_sql(
            f"SELECT * FROM clan_id WHERE clan_id = '{update.effective_chat.id}';",
            engine,
        )
        user_name = pd.read_sql(
            f"SELECT * FROM users WHERE user_id = '{user_id}';", engine
        )
        if len(info) == 0 and len(user_name) != 0:
            engine.execute(
                f"INSERT INTO clan_id(clan_id, name_clan) VALUES('{update.effective_chat.id}', '{update.effective_chat.title}');"
            )
            engine.execute(
                f"INSERT INTO admins(user_id, name, name_clan) VALUES('{user_id}', '{user_name.loc[0,'name0']}', '{update.effective_chat.title}');"
            )
        await bot.send_message(
            chat_id=943180118,
            text="ID: "
            + str(update.effective_chat.id)
            + "\n name: "
            + str(update.effective_chat.title)
            + "\n 1й админ: "
            + str(user_id),
        )
    elif (
        "люц" in msg.lower()
        and ("дай" in msg.lower() or "подкинь" in msg.lower())
        and ("денег" in msg.lower() or "монет" in msg.lower())
        and (chat_type == "supergroup" or chat_type == "group")
    ):
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text="Не, не варик... сам в аду на съемной хате существую... =(",
            reply_to_message_id=msg_id,
        )
    elif (
        "люц" in msg.lower()
        and ("тут" in msg.lower() or "живой" in msg.lower())
        and (chat_type == "supergroup" or chat_type == "group")
    ):
        await bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ну, а где мне еще быть!?",
            reply_to_message_id=msg_id,
        )
    elif (
        "бой" == msg.lower()
        or "битва" in msg.lower()
        or "наказать" in msg.lower()
        or "побить" in msg.lower()
        or "дуэль в ответ" in msg.lower()
    ) and update.message.reply_to_message is not None:
        fighter = [
            update.message.from_user.first_name,
            update.message.reply_to_message.from_user.first_name,
        ]
        if fighter[0] != fighter[1]:
            action1 = [
                "Хитрый жук ",
                "Легендарный воин ",
                "Как ниндзя в ночи ",
                "Бесстрашный герой ",
            ]
            action2 = [
                " напал на беззащитного, ",
                " дал пощёчину, ",
                " метнул копьё, ",
                " закидал камнями, ",
                " ущипнул за попу, ",
            ]
            action3 = [
                " не растерялся! ",
                " неожиданно для нападавшего, заблокировал атаку! ",
                " этого не ожидал! ",
                " увернулся и дал в ответ мега-леща! ",
                " отразил удар! ",
            ]
            action4 = [
                "Завязалась драка...",
                "Свершилось эпическое сражение...",
                "Началась грандиозная битва, не на жизнь, а на смерть...",
                "... и треснул мир напополам дымит разлом...",
            ]
            action_num1 = randint(0, 3)
            action_num2 = randint(0, 4)
            action_num3 = randint(0, 4)
            action_num4 = randint(0, 3)
            fighter1 = randint(0, 100)
            fighter2 = randint(0, 100)
            if fighter1 == fighter2:
                await bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=action1[action_num1]
                    + str(fighter[0])
                    + action2[action_num2]
                    + str(fighter[1])
                    + action3[action_num3]
                    + action4[action_num4],
                )
                with open("./fight/fight2.mp4", "rb") as video:
                    await bot.send_video(
                        chat_id=update.effective_chat.id, video=video
                    )
                await bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Вы сражались очень долго, но потом устали и "
                    "помирились! 🤝 НИЧЬЯ 🤝 \n\n Шансы на победу:\n"
                    + str(fighter[0])
                    + ": "
                    + str(fighter1)
                    + "% \n"
                    + str(fighter[1])
                    + ": "
                    + str(fighter1)
                    + "%",
                )
            else:
                if fighter1 > fighter2:
                    winer = 0
                else:
                    winer = 1
                num = randint(1, 13)
                await bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=action1[action_num1]
                    + str(fighter[0])
                    + action2[action_num2]
                    + str(fighter[1])
                    + action3[action_num3]
                    + action4[action_num4],
                )
                with open(f"./fight/fight{num}.mp4", "rb") as video:
                    await bot.send_video(
                        chat_id=update.effective_chat.id, video=video
                    )
                await bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Победил: 👑"
                    + str(fighter[winer])
                    + "👑\n\nШансы на победу:\n"
                    + str(fighter[0])
                    + ": "
                    + str(fighter1)
                    + "% \n"
                    + str(fighter[1])
                    + ": "
                    + str(fighter2)
                    + "%",
                )
        else:
            with open("./fight/fightSelf.mp4", "rb") as video:
                await bot.send_video(
                    chat_id=update.effective_chat.id, video=video
                )
            await bot.send_message(
                chat_id=update.effective_chat.id,
                text="Ну ты просто дал сам себе в глаз, вырубился и уснул!🤕",
            )
    elif (
        "люц" in msg.lower()
        and (
            "балбес" in msg.lower()
            or "плохой" in msg.lower()
            or "тупой" in msg.lower()
        )
        and (chat_type == "supergroup" or chat_type == "group")
    ):
        with open("./balbes.tgs", "rb") as sticker:
            await bot.send_sticker(
                chat_id=update.effective_chat.id, sticker=sticker
            )
    else:
        if chat_type == "supergroup" or chat_type == "group":
            pass
        else:
            await bot.send_message(
                chat_id=update.effective_chat.id,
                text="Я тебя не понимаю, я еще не настолько продвинутый. "
                "Нажми помощь, и там будут инструкции по применению ;) "
                "(Вопросы и предложения можно написать ему: @Menace134)",
            )

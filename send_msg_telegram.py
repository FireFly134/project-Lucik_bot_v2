import logging
from asyncio import run
from typing import BinaryIO

import telegram

from work import TELEGRAM_TOKEN, my_tid


async def main(
    chat_id: int | str,
    text: str | None = None,
    sticker: str | BinaryIO | None = None,
    video: BinaryIO | None = None,
    message_id: int | None = None,
) -> bool:
    try:
        bot = telegram.Bot(TELEGRAM_TOKEN)
        if text is not None and sticker is None and video is None:
            await bot.send_message(
                chat_id=chat_id, text=text, reply_to_message_id=message_id
            )
        if text is None and sticker is None and video is not None:
            await bot.send_message(
                chat_id=chat_id, video=video, reply_to_message_id=message_id
            )
        elif text is None and sticker is None and video is None:
            await bot.delete_message(chat_id=chat_id, message_id=message_id)
        else:
            await bot.send_sticker(
                chat_id=chat_id,
                sticker=sticker,
                reply_to_message_id=message_id,
            )
        return True
    except telegram.error.BadRequest as err:
        logging.error(f"{chat_id} - {err}")
        return False


async def send_msg(
    chat_id: int | str, text: str, reply_to_message_id: int | None = None
) -> bool:
    return await main(
        chat_id=chat_id, text=text, message_id=reply_to_message_id
    )


async def send_sticker(
    chat_id: int | str,
    sticker: str | BinaryIO,
    reply_to_message_id: int | None = None,
) -> bool:
    return await main(
        chat_id=chat_id, sticker=sticker, message_id=reply_to_message_id
    )


async def send_video(
    chat_id: int | str, video: BinaryIO, reply_to_message_id: int | None = None
) -> bool:
    return await main(
        chat_id=chat_id, video=video, message_id=reply_to_message_id
    )


async def del_msg(chat_id: int | str, message_id: int) -> bool:
    return await main(chat_id=chat_id, message_id=message_id)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(process)d-%(levelname)s %(message)s",
        datefmt="%d-%b-%y %H:%M:%S",
    )
    logging.info(run(send_msg(chat_id=my_tid, text="Test")))

from os import getenv

TELEGRAM_TOKEN: str = getenv("TELEGRAM_TOKEN", "")
BD: str = getenv("BD", "")
stop_word = ["Отмена"]

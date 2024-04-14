import os

login = os.getenv("POSTGRES_USER", "")
ip_server = os.getenv("POSTGRES_HOST", "")
port = os.getenv("POSTGRES_PORT", "")
name_db = os.getenv("POSTGRES_DB", "")
PASSWD_DB = os.getenv("POSTGRES_PASSWORD", "")
url_engine = f"postgresql://{login}:{PASSWD_DB}@{ip_server}:{port}/{name_db}"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
my_tid = os.getenv("MY_TID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
working_folder = "./"
stop_word = ("stop", "стоп", "отмена")

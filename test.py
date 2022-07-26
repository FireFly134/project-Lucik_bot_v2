# coding=UTF-8
#
#
import pandas as pd
from sqlalchemy import create_engine

from work import db


engine = create_engine(db, encoding='ascii')

info = pd.read_sql("SELECT * FROM user_id;", engine)
print(info)
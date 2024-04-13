from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from work import url_engine

engine = create_engine(url_engine)


async def insert_and_update_sql(
    text_for_sql: str | Any,
    params: dict[str, Any] | None = None,
    eng: Any = engine,
) -> bool:
    try:
        with eng.connect() as con:
            if type(text_for_sql) is str:
                con.execute(text(text_for_sql), parameters=params)
            else:
                con.execute(text_for_sql, parameters=params)
            con.commit()
        return True
    except SQLAlchemyError as err:
        print("ERROR insert_and_update_sql - " + str(err))
        return False

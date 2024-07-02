from sqlite3 import Connection, connect

from pandas import DataFrame, read_excel
from streamlit.runtime.uploaded_file_manager import UploadedFile


def readExcel(uf: UploadedFile) -> DataFrame:
    return read_excel(io=uf)


def toSQLiteDB(df: DataFrame, dbPath: str = ":memory:") -> Connection:
    conn: Connection = connect(database=dbPath)
    df.to_sql(
        name="schedule",
        con=conn,
        if_exists="replace",
        index=False,
    )

    return conn

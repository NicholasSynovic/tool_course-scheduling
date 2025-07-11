import sqlite3
from sqlite3 import Connection

import pandas as pd
from pandas import DataFrame
from streamlit.runtime.uploaded_file_manager import UploadedFile

from cs import api


def read_excel_file(uploaded_file: UploadedFile) -> DataFrame:
    # Read Excel file into pd.DataFrame and:
    # set columns to be upper case, and
    # rename DataFrame columns,
    data: DataFrame = pd.read_excel(io=uploaded_file, engine="openpyxl")
    data.columns = data.columns.str.upper()
    data = data.rename(columns={"ENROLLMENT TOTAL": "ENROLL TOTAL"})

    # Set default values for columns
    data["INSTRUCTOR"] = data["INSTRUCTOR"].fillna(value=api.DEFAULT_INSTRUCTOR)
    data["FACILITY"] = data["FACILITY"].fillna(value=api.DEFAULT_FACILITY)

    # Set datetime type for specific columns
    data["CLASS START TIME"] = pd.to_datetime(
        data["CLASS START TIME"],
        format="%I:%M %p",
    ).dt.strftime("%H:%M:%S")

    data["CLASS END TIME"] = pd.to_datetime(
        data["CLASS END TIME"],
        format="%I:%M %p",
    ).dt.strftime("%H:%M:%S")

    return data


def add_dataframe_columns(data: DataFrame) -> DataFrame:
    # Make a copy of the data
    df: DataFrame = data.copy()

    # Create new column for traditional meeting patterns
    df["TRAD MEETING PATTERN"] = (
        df["MEETING PATTERN"]
        .replace("Th", "R")
        .replace("TTh", "TR")
        .replace("SA", "S")
        .replace("SU", "X")
        .fillna("No Meeting Pattern")
    )

    # Create fully qualified catalog numbers and sections
    df["FQ CATALOG NUMBER"] = df["SUBJECT"] + "-" + df["CATALOG NUMBER"]
    df["FQ CLASS SECTION"] = df["CATALOG NUMBER"] + "-" + df["SECTION"]

    # Drop duplicate fully qualified class sections
    df = df.drop_duplicates(
        subset=["FQ CLASS SECTION"],
        ignore_index=True,
    )

    return df


# def readExcelToDB(uf: UploadedFile, dbPath: str = ":memory:") -> Connection:
#     conn: Connection = connect(database=dbPath)


#     df["UNIT CLASS DURATION"] = df.apply(_computeTotalTime, axis=1)

#     df["COMBINED ID"] = df.apply(_createCombinedID, axis=1)

#     df["INSTRUCTIONAL TIME"] = df.apply(_computeInstructionalTime, axis=1)

#     df["WEIGHTED ENROLL TOTAL"] = df.apply(
#         _computeWeightedEnrollment,
#         axis=1,
#     )

#     df["WEIGHTED SCH TOTAL"] = df.apply(_computeWeightedSchedule, axis=1)

#     df.to_sql(
#         name="schedule",
#         con=conn,
#         if_exists="replace",
#         index=False,
#     )

#     return conn

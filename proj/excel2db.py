from datetime import datetime
from sqlite3 import Connection, connect

import pandas
from pandas import DataFrame, Series, read_excel
from streamlit.runtime.uploaded_file_manager import UploadedFile

from proj.utils import datetimeToMinutes


def _computeInstructionalTime(row: Series):
    # TODO: Implement this.
    # Instructional time is computed as the sum of UNIT CLASS DURATION per day
    # that the class is taught
    return 0


def _computeTotalTime(row: Series) -> int:
    startTime: datetime = pandas.to_datetime(
        row["CLASS START TIME"],
    )
    endTime: datetime = pandas.to_datetime(
        row["CLASS END TIME"],
    )

    if pandas.isnull(obj=startTime):
        return 0

    if pandas.isnull(endTime):
        return 0

    startMinutes: int = datetimeToMinutes(dt=startTime)
    endMinutes: int = datetimeToMinutes(dt=endTime)

    return endMinutes - startMinutes


def _computeWeightedEnrollment(row: Series):
    if "300" <= row["CATALOG NUMBER"] < "400":
        return row["ENROLL TOTAL"] * 1.0
    elif "400" <= row["CATALOG NUMBER"]:
        return row["ENROLL TOTAL"] * 5 / 3
    else:
        return row["ENROLL TOTAL"]


def _computeWeightedSchedule(row: Series):
    credits = 3
    if row["CATALOG NUMBER"] in set(["395"]):
        credits = 1
    return int(credits * row["WEIGHTED_ENROLL_TOTAL"])


def readExcelToDB(uf: UploadedFile, dbPath: str = ":memory:") -> Connection:
    conn: Connection = connect(database=dbPath)

    df: DataFrame = read_excel(io=uf, engine="openpyxl")

    df["INSTRUCTOR"] = df["INSTRUCTOR"].fillna(value="UNKNOWN")

    df["CLASS START TIME"] = pandas.to_datetime(
        df["CLASS START TIME"],
        format="%I:%M %p",
    ).dt.strftime("%H:%M:%S")

    df["CLASS END TIME"] = pandas.to_datetime(
        df["CLASS END TIME"],
        format="%I:%M %p",
    ).dt.strftime("%H:%M:%S")

    df["TRAD MEETING PATTERN"] = (
        df["MEETING PATTERN"]
        .replace("TR", "R")
        .replace("SA", "S")
        .replace("SU", "X")
    )

    df["UNIT CLASS DURATION"] = df.apply(
        _computeTotalTime,
        axis=1,
    )

    df["INSTRUCTIONAL TIME"] = df.apply(
        _computeInstructionalTime,
        axis=1,
    )

    df["WEIGHTED_ENROLL_TOTAL"] = df.apply(
        _computeWeightedEnrollment,
        axis=1,
    )

    df["WEIGHTED_SCH_TOTAL"] = df.apply(
        _computeWeightedSchedule,
        axis=1,
    )

    df.to_sql(
        name="schedule",
        con=conn,
        if_exists="replace",
        index=False,
    )

    return conn

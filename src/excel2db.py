from datetime import datetime
from sqlite3 import Connection, connect

import pandas
from pandas import DataFrame, Series, read_excel
from streamlit.runtime.uploaded_file_manager import UploadedFile

from src.utils import datetimeToMinutes


def _computeInstructionalTime(row: Series):
    """
    Computes the instructional time for a class.

    Parameters:
    ----------
    row : pandas.Series
        A pandas Series containing data for a single class.

    Returns:
    -------
    int
        The instructional time computed as the sum of UNIT CLASS DURATION per day that the class is taught.

    TODO:
    -----
    Implement this function to compute the instructional time as described.

    """  # noqa: E501

    # TODO: Implement this.
    # Instructional time is computed as the sum of UNIT CLASS DURATION per day
    # that the class is taught
    return 0


def _computeTotalTime(row: Series) -> int:
    """
    Computes the total time in minutes between the start and end times of a class.

    Parameters:
    ----------
    row : pandas.Series
        A pandas Series containing data for a single class, including 'CLASS START TIME' and 'CLASS END TIME'.

    Returns:
    -------
    int
        The total time in minutes between the start and end times.

    Examples:
    --------
    Example 1:
    >>> import pandas as pd
    >>> from datetime import datetime
    >>> row1 = pd.Series({"CLASS START TIME": "2024-07-03 10:00:00", "CLASS END TIME": "2024-07-03 11:30:00"})
    >>> _computeTotalTime(row1)
    90

    Example 2:
    >>> row2 = pd.Series({"CLASS START TIME": "2024-07-03 14:00:00", "CLASS END TIME": None})
    >>> _computeTotalTime(row2)
    0

    Computes the total time in minutes between the start and end times of a class. Returns 0 if 'CLASS START TIME' or 'CLASS END TIME' is null.

    """  # noqa: E501

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
    """
    Computes the weighted enrollment based on the catalog number of a class.

    Parameters:
    ----------
    row : pandas.Series
        A pandas Series containing data for a single class.

    Returns:
    -------
    float
        The weighted enrollment value based on the catalog number.

    Examples:
    --------
    Example 1:
    >>> row1 = {"CATALOG NUMBER": "350", "ENROLL TOTAL": 50}
    >>> _computeWeightedEnrollment(row1)
    50.0

    Example 2:
    >>> row2 = {"CATALOG NUMBER": "420", "ENROLL TOTAL": 60}
    >>> _computeWeightedEnrollment(row2)
    100.0

    Computes the weighted enrollment based on the catalog number of a class. If 'CATALOG NUMBER' falls within the range '300' to '400', multiplies 'ENROLL TOTAL' by 1.0. If 'CATALOG NUMBER' is greater than or equal to '400', multiplies 'ENROLL TOTAL' by 5/3. Returns 'ENROLL TOTAL' unchanged if 'CATALOG NUMBER' does not meet the above conditions.

    """  # noqa: E501
    if "300" <= row["CATALOG NUMBER"] < "400":
        return row["ENROLL TOTAL"] * 1.0
    elif "400" <= row["CATALOG NUMBER"]:
        return row["ENROLL TOTAL"] * 5 / 3
    else:
        return row["ENROLL TOTAL"]


def _computeWeightedSchedule(row: Series):
    """
    Computes the weighted schedule value based on the catalog number and weighted enrollment total of a class.

    Parameters:
    ----------
    row : pandas.Series
        A pandas Series containing data for a single class, including 'CATALOG NUMBER' and 'WEIGHTED_ENROLL_TOTAL'.

    Returns:
    -------
    int
        The computed weighted schedule value.

    Examples:
    --------
    Example 1:
    >>> import pandas as pd
    >>> row1 = pd.Series({"CATALOG NUMBER": "395", "WEIGHTED_ENROLL_TOTAL": 50})
    >>> _computeWeightedSchedule(row1)
    50

    Example 2:
    >>> row2 = pd.Series({"CATALOG NUMBER": "300", "WEIGHTED_ENROLL_TOTAL": 60})
    >>> _computeWeightedSchedule(row2)
    180

    Computes the weighted schedule value based on the catalog number and weighted enrollment total of a class.
    """  # noqa: E501

    credits = 3
    if row["CATALOG NUMBER"] in set(["395"]):
        credits = 1
    return int(credits * row["WEIGHTED_ENROLL_TOTAL"])


def readExcelToDB(uf: UploadedFile, dbPath: str = ":memory:") -> Connection:
    """
    Reads data from an uploaded Excel file, processes it, and stores it in an SQLite in-memory database.

    Parameters:
    ----------
    uf : UploadedFile
        The uploaded Excel file object containing class schedule data.
    dbPath : str, optional
        Path to the SQLite database (default is ":memory:").

    Returns:
    -------
    Connection
        SQLite database connection object.

    Examples:
    --------
    Example:
    >>> from pandas import DataFrame
    >>> from sqlalchemy.engine.base import Connection
    >>> conn = readExcelToDB(uploaded_file, dbPath="my_db.sqlite")

    Reads data from an uploaded Excel file, processes it by converting times, calculating durations,
    and computing weighted metrics, and stores it in an SQLite database.
    """  # noqa: E501

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

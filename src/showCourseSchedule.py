from sqlite3 import Connection
from typing import List

import pandas
from pandas import DataFrame, Series


def _fixTraditionalMeetingPattern(row: Series) -> Series | None:
    meeting_pattern: Series = row["MEETING_PATTERN"]
    if meeting_pattern:
        return (
            meeting_pattern.replace("TR", "R")
            .replace("SA", "S")
            .replace("SU", "X")
        )
    else:
        return None


def filterCourses(conn: Connection, department: str = "COMP") -> DataFrame:
    depts: List[str] = [department]

    filterQuery: str = f"""
        SUBJECT = '{department}'
            and
        CATALOG_NUMBER not in ('391', '398', '490', '499', '605')
            and
        CATALOG_NUMBER not in ('215', '231', '331', '431', '381', '386', '383', '483')
            and
        SECTION not in ('01L', '02L', '03L', '04L', '05L', '06L', '700N')
    """

    departmentFilters: dict[str, str] = {"COMP": filterQuery}

    whereClause: str = "\n  WHERE " + " or ".join(
        [
            "(" + departmentFilters[filter] + ")"
            for filter in departmentFilters
        ],
    )

    sqlQuery: str = (
        """
    SELECT
        SUBJECT,
        CATALOG_NUMBER,
        SUBJECT || "-" || CATALOG_NUMBER as FQ_CATALOG_NUMBER,
        CATALOG_NUMBER || '-' || SECTION as FQ_CLASS_SECTION,
        CLASS_TITLE,
        INSTRUCTOR,
        ENROLL_TOTAL,
        MEETING_PATTERN,
        CLASS_START_TIME,
        CLASS_END_TIME,
        FACILITY,
        '(' || INSTRUCTOR || ',' || FACILITY || ',' || MEETING_PATTERN || ',' ||CLASS_START_TIME || ',' || CLASS_END_TIME || ')' as COMBINED_ID
    FROM
        schedule """
        + whereClause
    ).strip()

    return pandas.read_sql_query(sql=sqlQuery, con=conn)


def cleanData(df: DataFrame) -> DataFrame:
    df.drop_duplicates(
        subset=["FQ_CLASS_SECTION"],
        inplace=True,
    )

    df["INSTRUCTOR"].fillna(value="UNKNOWN", inplace=True)

    df["COMBINED_ID"].fillna(
        value="(Doyle Center, No Start Time, No End Time)",
        inplace=True,
    )

    df["TRAD_MEETING_PATTERN"] = df.apply(
        f=_fixTraditionalMeetingPattern,
        axis=1,
    )

    return df


def time_to_minutes(t):
    return t.hour * 60 + t.minute


def unit_class_duration(row):
    start = row["CLASS_START_TIME"]
    end = row["CLASS_END_TIME"]

    if not start or not end:
        return 0
    start_time = datetime.strptime(start, "%H:%M:%S")
    end_time = datetime.strptime(end, "%H:%M:%S")
    start_minutes = time_to_minutes(start_time)
    end_minutes = time_to_minutes(end_time)
    total_minutes = end_minutes - start_minutes
    return total_minutes


def instructional_time(row):
    meeting_pattern = row["TRAD_MEETING_PATTERN"]
    return len(meeting_pattern) * row["UNIT_CLASS_DURATION"]


# df2 = df2.copy()
# Really bad LOCUS thing: M,T,W,TR,F,SA
# I'm using M,T,W,T,F. If we ever use SU it would become X to denote why we shouldn't do it.


# A bit of data cleansing just to remove the unwanted time information from the Excel to SQLLite3 conversion.

df2["CLASS_START_TIME"] = df["CLASS_START_TIME"].str.split(" ").str[1]
df2["CLASS_END_TIME"] = df["CLASS_END_TIME"].str.split(" ").str[1]
df2["COMBINED_ID"] = df["COMBINED_ID"].str.replace("1900-01-01", "")

df2["UNIT_CLASS_DURATION"] = df2.apply(unit_class_duration, axis=1)
df2["INSTRUCTIONAL_TIME"] = df2.apply(instructional_time, axis=1)

# key_fields_of_interest = ['SUBJECT','CATALOG_NUMBER','FQ_CATALOG_NUMBER','FQ_CLASS_SECTION', 'CLASS_TITLE', 'INSTRUCTOR', 'ENROLL_TOTAL', 'MEETING_PATTERN','CLASS_START_TIME','CLASS_END_TIME', 'FACILITY','COMBINED_ID']
FILTER_FIELDS = [
    "FQ_CLASS_SECTION",
    "CLASS_TITLE",
    "INSTRUCTOR",
    "ENROLL_TOTAL",
    "TRAD_MEETING_PATTERN",
    "INSTRUCTIONAL_TIME",
    "MEETING_PATTERN",
    "UNIT_CLASS_DURATION",
    "CLASS_START_TIME",
    "CLASS_END_TIME",
    "FACILITY",
    "COMBINED_ID",
]

# Now 'df' holds the contents of 'your_table' as a Pandas DataFrame
# Filter out any sectinos with 0. If enrollment is 0, likely to be cancelled anyway.
group = df2[df2["ENROLL_TOTAL"] >= 0]

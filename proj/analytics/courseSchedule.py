from sqlite3 import Connection
from typing import List

import pandas
import streamlit
from pandas import DataFrame

from proj.utils import clearContent


class CourseSchedule:
    """
    A class to manage and retrieve course schedules from a database based on predefined department filters.

    This class allows filtering and retrieving detailed information about course schedules, excluding certain
    catalog numbers and sections according to department-specific criteria.

    :param conn: A connection to the database containing the course schedules.
    :type conn: Connection
    """  # noqa: E501

    def __init__(self, conn: Connection) -> None:
        self.conn: Connection = conn

        # NOTE: Other departments can be added by creating a
        # new key and SQL query per department
        self.departmentFilters: dict[str, str] = {
            "COMP": """SUBJECT = 'COMP' AND "CATALOG NUMBER" NOT IN ('391', '398', '490', '499', '605') AND "CATALOG NUMBER" NOT IN ('215', '231', '331', '431', '381', '386', '383', '483') AND SECTION NOT IN ('01L', '02L', '03L', '04L', '05L', '06L', '700N')"""  # noqa: E501
        }

    def compute(self, minimumEnrollment: int = 0) -> DataFrame:
        if minimumEnrollment < 0:
            minimumEnrollment = 0

        whereClasues: str = "WHERE " + " or ".join(
            [
                "(" + self.departmentFilters[filter] + ")"
                for filter in self.departmentFilters
            ]
        )

        query: str = (
            """SELECT SUBJECT, "CATALOG NUMBER", SUBJECT || '-' || "CATALOG NUMBER" as FQ_CATALOG_NUMBER, "CATALOG NUMBER" || '-' || SECTION as FQ_CLASS_SECTION, "CLASS TITLE", INSTRUCTOR, "ENROLL TOTAL", "TRAD MEETING PATTERN", "CLASS START TIME", "CLASS END TIME", "UNIT CLASS DURATION", "INSTRUCTIONAL TIME", FACILITY, '(' || INSTRUCTOR || ',' || FACILITY || ',' || "MEETING PATTERN" || ',' || "CLASS START TIME" || ',' || "CLASS END TIME" || ')' as COMBINED_ID FROM schedule """  # noqa: E501
        )

        query = query + whereClasues + ";"
        query = query.strip()

        df: DataFrame = pandas.read_sql_query(
            sql=query,  # nosec
            con=self.conn,
        )

        df.drop_duplicates(
            subset=["FQ_CLASS_SECTION"],
            inplace=True,
            ignore_index=True,
        )

        df["COMBINED_ID"] = df["COMBINED_ID"].fillna(
            value="(UNKNOWN, N/A, N/A)",
        )

        df = df[df["ENROLL TOTAL"] >= minimumEnrollment]

        df.reset_index(drop=True, inplace=True)

        return df

    def run(self) -> None:
        clearContent()

        dfs: List[DataFrame] = [self.compute()]

        streamlit.session_state["analyticTitle"] = "Course Schedule"
        streamlit.session_state["analyticSubtitle"] = (
            "The current course \
        schedule"
        )
        streamlit.session_state["dfList"] = dfs

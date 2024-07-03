from sqlite3 import Connection

import pandas
import streamlit
from pandas import DataFrame


class CourseSchedule:
    def __init__(self, conn: Connection) -> None:
        self.conn: Connection = conn

        # NOTE: Other departments can be added by creating a
        # new key and SQL query per department
        self.departmentFilters: dict[str, str] = {
            "COMP": """SUBJECT = 'COMP' AND "CATALOG NUMBER" NOT IN ('391', '398', '490', '499', '605') AND "CATALOG NUMBER" NOT IN ('215', '231', '331', '431', '381', '386', '383', '483') AND SECTION NOT IN ('01L', '02L', '03L', '04L', '05L', '06L', '700N')"""  # noqa: E501
        }

    def get(self, minimumEnrollment: int = 0) -> DataFrame:
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
        streamlit.session_state["df"] = None
        streamlit.session_state["fig"] = None

        df: DataFrame = self.get()

        streamlit.session_state["df"] = df

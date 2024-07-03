from sqlite3 import Connection
from typing import List, Tuple

import streamlit
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy
from proj.analytics.courseSchedule import CourseSchedule
from proj.utils import clearContent


class CourseEnrollmentHealth:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def compute(self) -> List[Tuple[str, DataFrame, str, int]]:
        data: List[Tuple[str, DataFrame, str]] = []

        FILTER_FIELDS: List[str] = [
            "FQ_CLASS_SECTION",
            "CLASS TITLE",
            "INSTRUCTOR",
            "ENROLL TOTAL",
            "TRAD MEETING PATTERN",
            "CLASS START TIME",
            "CLASS END TIME",
        ]

        report: List[Tuple[int, str, DataFrame]] = []

        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        dfs: DataFrameGroupBy = df.groupby(by="COMBINED_ID")

        name: str
        group: DataFrame
        for name, group in dfs:
            report.append((group["WEIGHTED_ENROLL_TOTAL"].sum(), name, group))

        report = sorted(report, key=lambda tup: tup[0])

        entry: Tuple[int, str, DataFrame]
        for entry in report:
            color: str = "blue"

            filteredDF: DataFrame = entry[2][FILTER_FIELDS]

            groupSum: int = entry[0]

            if groupSum < 12:
                color = "red"

            if groupSum < 32:
                color = "green"

            data.append((entry[1], filteredDF, color, groupSum))

        return data

    def run(self) -> None:
        data: List[Tuple[str, DataFrame, str, int]] = self.compute()

        clearContent()

        dfs: List[DataFrame] = [datum[1] for datum in data]

        streamlit.session_state["analyticTitle"] = "Course Enrollment Health"
        streamlit.session_state["analyticSubtitle"] = "Health of each course"
        streamlit.session_state["dfList"] = dfs
        streamlit.session_state["dfListTitles"] = [datum[0] for datum in data]
        streamlit.session_state["dfListSubtitles"] = [
            f":{color}[Weighted Enrollments = {amount}]"
            for _, _, color, amount in data
        ]

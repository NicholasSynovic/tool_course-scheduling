from itertools import count
from math import ceil
from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent


class InTroubleCourses:
    def __init__(self, conn: Connection) -> None:
        self.conn: Connection = conn

    def compute(self) -> DataFrameGroupBy:
        FILTER_FIELDS: List[str] = [
            "FQ_CLASS_SECTION",
            "CLASS TITLE",
            "INSTRUCTOR",
            "ENROLL TOTAL",
            "TRAD MEETING PATTERN",
            "CLASS START TIME",
            "CLASS END TIME",
            "WEIGHTED_ENROLL_TOTAL",
            "COMBINED_ID",
        ]

        df: DataFrame = CourseSchedule(conn=self.conn).compute()
        df = df[FILTER_FIELDS]

        return df.groupby(by="COMBINED_ID")

    def run(self) -> None:
        clearContent()

        streamlit.session_state["analyticTitle"] = "In Trouble Courses"
        streamlit.session_state["analyticSubtitle"] = "Courses in trouble"

        dfList: List[DataFrame] = []
        dfListTitles: List[str] = []

        troubleThreshold: int = 10
        inTroubleCount: count = count(start=1)

        dfs: DataFrameGroupBy = self.compute()

        group: DataFrame
        for _, group in dfs:
            group_sum: int = ceil(group["WEIGHTED_ENROLL_TOTAL"].sum())
            if group_sum < troubleThreshold:
                in_trouble_val = next(inTroubleCount)
                group_color = "green" if group_sum >= 12 else "red"  # for now
                dfListTitles.append(
                    f":{group_color}[Course {in_trouble_val} has {group_sum} enrollments]"  # noqa: E501
                )
                dfList.append(group)

        streamlit.session_state["dfList"] = dfList
        streamlit.session_state["dfListTitles"] = dfListTitles

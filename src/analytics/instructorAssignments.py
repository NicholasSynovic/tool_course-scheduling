from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent


class InstructorAssignments:
    def __init__(self, conn: Connection) -> None:
        self.conn: Connection = conn

    def compute(self) -> DataFrameGroupBy:
        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        return df.groupby(by="INSTRUCTOR")

    def run(self) -> None:
        clearContent()
        dfList: List[DataFrame] = []
        dfListTitles: List[str] = []

        dfs: DataFrameGroupBy = self.compute()

        streamlit.session_state["analyticTitle"] = "Instructor Assignments"
        streamlit.session_state["analyticSubtitle"] = (
            "Show instructor assignments"
        )

        instructor: str
        df: DataFrame
        for instructor, df in dfs:
            group: DataFrameGroupBy = df.groupby(by="COMBINED_ID")

            _df: DataFrame
            for _, _df in group:
                dfList.append(_df)
                dfListTitles.append(instructor)

        streamlit.session_state["dfList"] = dfList
        streamlit.session_state["dfListTitles"] = dfListTitles

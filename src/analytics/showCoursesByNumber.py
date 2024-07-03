from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy
from proj.analytics.courseSchedule import CourseSchedule
from proj.utils import clearContent


class ShowCoursesByNumber:
    def __init__(self, conn: Connection) -> None:
        self.conn: Connection = conn

    def compute(self) -> DataFrameGroupBy:
        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        return df.groupby(by="FQ_CATALOG_NUMBER")

    def run(self) -> None:
        clearContent()

        streamlit.session_state["analyticTitle"] = (
            "Show Courses by Course Number"
        )
        streamlit.session_state["analyticSubtitle"] = (
            "A view of courses that share a course number"
        )

        dfList: List[DataFrame] = []
        dfListTitles: List[str] = []
        dfListSubtitles: List[str] = []

        df: DataFrame
        for name, df in self.compute():
            dfList.append(df)
            dfListTitles.append(name)
            dfListSubtitles.append(df["CLASS TITLE"].unique()[0])

        streamlit.session_state["dfList"] = dfList
        streamlit.session_state["dfListTitles"] = dfListTitles
        streamlit.session_state["dfListSubtitles"] = dfListSubtitles

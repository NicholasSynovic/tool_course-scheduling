from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame

from proj.analytics.courseSchedule import CourseSchedule
from proj.utils import clearContent


class OnlineCourseSchedule:
    def __init__(self, conn: Connection) -> None:
        self.conn: Connection = conn

    def compute(self) -> DataFrame:
        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        df = df[df["FACILITY"] == "ONLINE"]

        df.reset_index(drop=True, inplace=True)

        return df

    def run(self) -> None:
        clearContent()

        dfs: List[DataFrame] = [self.compute()]

        streamlit.session_state["analyticTitle"] = (
            "Online Only Course Schedule"
        )
        streamlit.session_state["analyticSubtitle"] = (
            "The current course \
        schedule for online only courses"
        )
        streamlit.session_state["dfList"] = dfs

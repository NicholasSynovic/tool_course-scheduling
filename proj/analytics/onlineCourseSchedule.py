from sqlite3 import Connection

import streamlit
from pandas import DataFrame

from proj.analytics.courseSchedule import CourseSchedule


class OnlineCourseSchedule:
    def __init__(self, conn: Connection) -> None:
        self.conn: Connection = conn

    def get(self) -> DataFrame:
        df: DataFrame = CourseSchedule(conn=self.conn).get()

        df = df[df["FACILITY"] == "ONLINE"]

        df.reset_index(drop=True, inplace=True)

        return df

    def run(self) -> None:
        streamlit.session_state["df"] = None
        streamlit.session_state["fig"] = None

        df: DataFrame = self.get()

        streamlit.session_state["df"] = df

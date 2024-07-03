from sqlite3 import Connection

import streamlit
from pandas import DataFrame, Series
from plotly import express
from plotly.graph_objects import Figure

from proj.analytics.courseSchedule import CourseSchedule


class AssignmentsPerFaculty:
    def __init__(self, conn: Connection) -> None:
        self.conn = conn

    def compute(self) -> DataFrame:
        df: DataFrame = CourseSchedule(conn=self.conn).get()

        data: Series[int] = df["INSTRUCTOR"].value_counts(
            sort=True,
            ascending=True,
        )

        dataDF: DataFrame = data.reset_index()
        dataDF.columns = ["Instructor Name", "Number of Courses"]

        return dataDF[dataDF["Instructor Name"] != "UNKNOWN"]

    def plot(self, df: DataFrame) -> Figure:
        fig = express.bar(
            data_frame=df,
            y="Instructor Name",
            x="Number of Courses",
            orientation="h",
            title="Number of Assignments per Instructor",
            labels={
                "Instructor Name": "Instructor Name",
                "Number of Courses": "Number of Courses",
            },
        )

        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Number of Courses",
            yaxis_title="Instructor Name",
        )

        return fig

    def run(self) -> None:
        streamlit.session_state["df"] = None
        streamlit.session_state["fig"] = None

        df: DataFrame = self.compute()
        fig: Figure = self.plot(df=df)

        streamlit.session_state["fig"] = fig

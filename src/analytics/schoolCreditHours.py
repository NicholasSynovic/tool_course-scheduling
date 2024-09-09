from sqlite3 import Connection
from typing import List, Tuple

import plotly.graph_objs as go
import streamlit
from pandas import DataFrame
from plotly.graph_objects import Figure

from src.analytics.courseSchedule import CourseSchedule
from src.utils.analytic import Analytic


class SchoolCreditHours(Analytic):

    def __init__(self, conn: Connection) -> None:
        """
        Initialize the CourseEnrollmentHealth class with a database
        connection.

        This constructor sets up the database connection which will be used to
        compute and visualize the health of course enrollments.

        :param conn: A database connection object.
        :type conn: Connection
        """
        self.conn = conn

    def compute(self) -> List[Tuple[str, DataFrame, str, int]]:

        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        if (
            "ENROLL TOTAL" not in df.columns
            or "WEIGHTED ENROLL TOTAL" not in df.columns
            or "CATALOG NUMBER" not in df.columns
        ):
            raise KeyError(
                "Necessary columns ('ENROLL TOTAL', 'WEIGHTED ENROLL TOTAL', 'CATALOG NUMBER') are missing from the data."  # noqa: E501
            )

        df["COURSE LEVEL"] = (
            df["CATALOG NUMBER"].astype(str).str[:3].astype(int) // 100 * 100
        )

        groupedDF = (
            df.groupby("COURSE LEVEL")
            .agg({"ENROLL TOTAL": "sum", "WEIGHTED ENROLL TOTAL": "sum"})
            .reset_index()
        )

        # by 3 credits
        groupedDF["ENROLL TOTAL"] *= 3
        groupedDF["WEIGHTED ENROLL TOTAL"] *= 3

        return groupedDF

    def run(self) -> None:

        data: DataFrame = self.compute()
        fig: Figure = self.plot(data)

        streamlit.session_state["analyticTitle"] = "School Credit Hours"
        streamlit.session_state["dfList"] = [data]
        streamlit.session_state["dfListTitles"] = [
            "Total Credit Hours by Course Level"
        ]

        streamlit.session_state["figList"] = [fig]

    def plot(self, data: DataFrame) -> Figure:

        if data is not None and not data.empty:

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=data["COURSE LEVEL"],
                    y=data["ENROLL TOTAL"],
                    name="Enroll Total",
                    marker_color="blue",
                )
            )

            fig.add_trace(
                go.Bar(
                    x=data["COURSE LEVEL"],
                    y=data["WEIGHTED ENROLL TOTAL"],
                    name="Weighted Enroll Total",
                    marker_color="green",
                )
            )

            fig.update_layout(
                title="Enrollment by Course Level",
                xaxis_title="Course Level",
                yaxis_title="Enrollment",
                barmode="group",
                width=800,
                height=600,
            )
        return fig

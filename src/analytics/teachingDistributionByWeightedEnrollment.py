from sqlite3 import Connection

import plotly.express as px
import streamlit
from pandas import DataFrame, Series
from plotly.graph_objects import Figure

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent


class TeachingDistributionByWeightedEnrollment:
    def __init__(self, conn: Connection) -> None:
        self.conn: Connection = conn

    def compute(self) -> Series:
        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        data: Series = (
            df.groupby(by="INSTRUCTOR")["WEIGHTED_ENROLL_TOTAL"]
            .sum()
            .reset_index()
        )

        return data.sort_values(by="WEIGHTED_ENROLL_TOTAL", ascending=False)

    def plot(self, data: Series) -> Figure:
        fig: Figure = px.bar(
            data,
            x="WEIGHTED_ENROLL_TOTAL",
            y="INSTRUCTOR",
            orientation="h",  # Horizontal bar chart
            title="Total Weighted Enrollment per Instructor",
            labels={
                "WEIGHTED_ENROLL_TOTAL": "Total Weighted Enrollment (courses, not SCH)",  # noqa: E501
                "INSTRUCTOR": "Instructor",
            },
            height=600,  # Adjust the height of the plot as needed
        )

        # Customize the layout for better readability
        fig.update_layout(
            xaxis_title="Total Weighted Enrollment (courses, not SCH)",
            yaxis_title="Instructor",
            yaxis={
                "categoryorder": "total ascending"
            },  # Sort the y-axis by the total enrollment
            plot_bgcolor="white",
        )

        return fig

    def run(self) -> None:
        clearContent()

        streamlit.session_state["analyticTitle"] = (
            "Teaching Distribution By Weighted Enrollment"
        )
        streamlit.session_state["analyticSubtitle"] = (
            "Teaching Distribution By Weighted Enrollment"
        )

        data: Series = self.compute()

        streamlit.session_state["figList"] = [self.plot(data=data)]

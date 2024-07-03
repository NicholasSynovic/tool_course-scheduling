from sqlite3 import Connection
from typing import List, Tuple

import plotly.graph_objects as go
import streamlit
from pandas import DataFrame
from plotly.graph_objects import Figure

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent


class EnrollmentByCourseLevel:
    def __init__(self, conn: Connection) -> None:
        self.conn: Connection = conn

    def compute(self) -> DataFrame:
        return CourseSchedule(conn=self.conn).compute()

    def plot(self) -> Tuple[str, Figure]:
        figList: Tuple[str, Figure] = []

        df: DataFrame = self.compute()

        for level in range(0, 500, 100):
            this_level = str(level + 100)
            df = df[df["CATALOG NUMBER"] >= this_level]
            next_level = str(level + 200)
            df = df[df["CATALOG NUMBER"] < next_level]

            if len(df) == 0:
                break

            course_enrollment = (
                df.groupby("FQ_CATALOG_NUMBER")["WEIGHTED_ENROLL_TOTAL"]
                .sum()
                .reset_index()
            )
            course_enrollment = course_enrollment.sort_values(
                by="WEIGHTED_ENROLL_TOTAL", ascending=False
            )

            # Create Plotly bar chart
            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    y=course_enrollment["FQ_CATALOG_NUMBER"],
                    x=course_enrollment["WEIGHTED_ENROLL_TOTAL"],
                    orientation="h",
                    marker=dict(
                        color=course_enrollment["WEIGHTED_ENROLL_TOTAL"],
                        colorscale="Viridis",
                        showscale=True,
                        colorbar=dict(title="Weighted Enrollment"),
                    ),
                )
            )

            title: str = f"Enrollment at {this_level}-level"

            fig.update_layout(
                title=title,
                xaxis_title="Enrollment",
                yaxis_title="Course",
                width=800,
                height=600,
            )

            # Calculate and plot the average weighted enrollment
            average_enrollment = course_enrollment[
                "WEIGHTED_ENROLL_TOTAL"
            ].mean()
            fig.add_vline(
                x=average_enrollment,
                line=dict(color="red", dash="dash"),
                annotation=dict(
                    text=f"Average ({average_enrollment:.2f})",
                    showarrow=True,
                    arrowhead=1,
                ),
            )

            figList.append((title, fig))

        return figList

    def run(self) -> None:
        clearContent()

        data: List[Tuple[str, Figure]] = self.plot()

        streamlit.session_state["analyticTitle"] = "Enrollment by course level"
        streamlit.session_state["analyticSubtitle"] = (
            "Enrollment by course level"
        )

        streamlit.session_state["figList"] = [datum[1] for datum in data]
        streamlit.session_state["figListTitles"] = [datum[0] for datum in data]

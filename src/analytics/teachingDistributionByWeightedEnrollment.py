from sqlite3 import Connection

import plotly.express as px
import streamlit
from pandas import DataFrame, Series
from plotly.graph_objects import Figure

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent
from src.utils.analytic import Analytic


class TeachingDistributionByWeightedEnrollment(Analytic):
    """
    TeachingDistributionByWeightedEnrollment class to compute and visualize
    the distribution of teaching assignments based on weighted enrollment.

    This class provides functionalities to compute and plot the total weighted
    enrollment per instructor.
    """

    def __init__(self, conn: Connection) -> None:
        """
        Initialize the TeachingDistributionByWeightedEnrollment class with a
        database connection.

        This constructor sets up the database connection which will be used to
        compute and visualize the teaching distribution by weighted
        enrollment.

        :param conn: A database connection object.
        :type conn: Connection
        """
        self.conn: Connection = conn

    def compute(self) -> Series:
        """
        Compute the total weighted enrollment per instructor.

        This method fetches the course schedule data from the database,
        computes the total weighted enrollment per instructor, and sorts the
        results in descending order.

        :return: A Series containing the total weighted enrollment per
            instructor.
        :rtype: Series
        """
        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        data: Series = (
            df.groupby(by="INSTRUCTOR")["WEIGHTED ENROLL TOTAL"]
            .sum()
            .reset_index()
        )

        return data.sort_values(by="WEIGHTED ENROLL TOTAL", ascending=False)

    def plot(self, data: Series) -> Figure:
        """
        Plot the total weighted enrollment per instructor.

        This method creates a horizontal bar chart to visualize the total
        weighted enrollment per instructor.

        :param data: A Series containing the total weighted enrollment per
            instructor.
        :type data: Series
        :return: A Plotly Figure representing the total weighted enrollment
            per instructor.
        :rtype: Figure
        """
        fig: Figure = px.bar(
            data,
            x="WEIGHTED ENROLL TOTAL",
            y="INSTRUCTOR",
            orientation="h",  # Horizontal bar chart
            title="Total Weighted Enrollment per Instructor",
            labels={
                "WEIGHTED ENROLL TOTAL": "Total Weighted Enrollment (courses, not SCH)",  # noqa: E501
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
        """
        Execute the workflow to compute and visualize the teaching
            distribution by weighted enrollment.

        This method performs the following steps:
        1. Clears existing content.
        2. Computes the total weighted enrollment per instructor.
        3. Updates the Streamlit session state with the resulting figure for
            visualization.

        :return: None
        :rtype: None
        """
        clearContent()

        streamlit.session_state["analyticTitle"] = (
            "Teaching Distribution By Weighted Enrollment"
        )
        streamlit.session_state["analyticSubtitle"] = (
            "Teaching Distribution By Weighted Enrollment"
        )

        data: Series = self.compute()

        streamlit.session_state["figList"] = [self.plot(data=data)]

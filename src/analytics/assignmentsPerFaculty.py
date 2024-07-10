from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame, Series
from plotly import express
from plotly.graph_objects import Figure

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent
from src.utils.analytic import Analytic


class AssignmentsPerFaculty(Analytic):
    """
    Class to compute and visualize assignments per faculty member.

    This class provides functionalities to compute the number of courses
    assigned to each faculty member and visualize these assignments using
    interactive plots. It leverages a database connection to fetch the required
    data.
    """

    def __init__(self, conn: Connection) -> None:
        """
        Initialize the AssignmentsPerFaculty class with a database connection.

        This constructor initializes the AssignmentsPerFaculty class, setting
        up the database connection which will be used to compute and visualize
        assignments per faculty member.

        :param conn: A database connection object.
        :type conn: Connection
        """
        self.conn = conn

    def compute(self) -> DataFrame:
        """
        Compute the number of courses taught by each instructor.

        This method fetches the course schedule from the database, calculates
        the number of courses taught by each instructor, and returns this
        information as a DataFrame. Instructors with the name "UNKNOWN" are
        excluded from the final DataFrame.

        :return: A DataFrame containing the number of courses taught by each
            instructor.
        :rtype: DataFrame
        """
        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        data: Series[int] = df["INSTRUCTOR"].value_counts(
            sort=True,
            ascending=False,
        )

        dataDF: DataFrame = data.reset_index()
        dataDF.columns = ["Instructor Name", "Number of Courses"]

        return dataDF[dataDF["Instructor Name"] != "UNKNOWN"]

    def plot(self, df: DataFrame) -> Figure:
        """
        Plot a horizontal bar chart showing the number of courses taught by
        each instructor.

        This method creates a Plotly figure that displays a horizontal bar
        chart, with the number of courses on the x-axis and instructor names on
        the y-axis. The chart provides a visual representation of the number of
        assignments per instructor.

        :param df: A DataFrame containing the number of courses taught by each
            instructor.
        :type df: pd.DataFrame
        :return: A Plotly Figure object representing the horizontal bar chart.
        :rtype: plotly.graph_objs.Figure
        """
        fig: Figure = express.bar(
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
            xaxis_title="Number of Courses",
            yaxis_title="Instructor Name",
        )

        return fig

    def run(self) -> None:
        """
        Run the workflow to compute and plot assignments per instructor.

        This method clears any existing content, computes the number of courses
        taught by each instructor, plots the results, and updates the Streamlit
        session state with the resulting data and figures.

        :return: None
        """
        clearContent()

        dfs: List[DataFrame] = [self.compute()]
        figs: List[Figure] = [self.plot(df=df) for df in dfs]

        streamlit.session_state["analyticTitle"] = (
            "Number of Assignments Per Faculty Member"
        )
        streamlit.session_state["analyticSubtitle"] = (
            "The number of courses that are assigned to each faculty member \
                for the current term"
        )
        streamlit.session_state["dfList"] = dfs
        streamlit.session_state["dfListTitles"] = ["Faculty Assignment Count"]

        streamlit.session_state["figList"] = figs
        streamlit.session_state["figListTitles"] = [
            "Faculty Assignment Count Plot"
        ]

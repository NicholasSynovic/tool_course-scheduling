from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent
from src.utils.analytic import Analytic


class OnlineCourseSchedule(Analytic):
    """
    OnlineCourseSchedule class to retrieve and manage online course schedule
    data.

    This class provides functionalities to compute and visualize the course
    schedule data for online courses.
    """

    def __init__(self, conn: Connection) -> None:
        """
        Initialize the OnlineCourseSchedule class with a database connection.

        This constructor sets up the database connection which will be used to
        compute and visualize the online course schedule data.

        :param conn: A database connection object.
        :type conn: Connection
        """
        self.conn: Connection = conn

    def compute(self) -> DataFrame:
        """
        Compute the course schedule data filtered by 'ONLINE' facility.

        This method fetches the course schedule data from the database and
        filters it to include only the courses held online.

        :return: A DataFrame containing course schedule data filtered by
            'ONLINE' facility.
        :rtype: DataFrame
        """
        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        df = df[df["FACILITY"] == "ONLINE"]

        df.reset_index(drop=True, inplace=True)

        return df

    def run(self) -> None:
        """
        Execute the workflow to retrieve and store online course schedule
        data.

        This method computes the online course schedule data, clears existing
        content, and updates the Streamlit session state with the resulting
        data for visualization.

        :return: None
        :rtype: None
        """
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

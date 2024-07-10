from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent
from src.utils.analytic import Analytic


class ShowCoursesByNumber(Analytic):
    """
    ShowCoursesByNumber class to display courses grouped by their course
    number.

    This class provides functionalities to compute and visualize courses that
    share the same course number.
    """

    def __init__(self, conn: Connection) -> None:
        """
        Initialize the ShowCoursesByNumber class with a database connection.

        This constructor sets up the database connection which will be used to
        compute and visualize the courses grouped by their course number.

        :param conn: A database connection object.
        :type conn: Connection
        """
        self.conn: Connection = conn

    def compute(self) -> DataFrameGroupBy:
        """
        Compute the courses grouped by their course number.

        This method fetches the course schedule data from the database and
        groups the courses by their fully qualified course number
        (FQ_CATALOG_NUMBER).

        :return: A DataFrameGroupBy object containing the grouped course
            schedule data.
        :rtype: DataFrameGroupBy
        """
        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        return df.groupby(by="FQ CATALOG NUMBER")

    def run(self) -> None:
        """
        Execute the workflow to compute and display courses grouped by their
        course number.

        This method performs the following steps:
        1. Clears existing content.
        2. Retrieves and groups the course schedule data by course number.
        3. Updates the Streamlit session state with the resulting data for
            visualization.

        :return: None
        :rtype: None
        """
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

    def plot(self, data: None) -> None:
        """
        Empty function required by Analytic ABC
        :param data: Null
        :type data: None
        """
        pass

from sqlite3 import Connection
from typing import List, Tuple

import streamlit
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent
from src.utils.analytic import Analytic


class CourseEnrollmentHealth(Analytic):
    """
    Class to compute and visualize the health of course enrollments.

    This class provides functionalities to compute the enrollment health of
    each course and visualize the results using interactive plots. It
    leverages a database connection to fetch the required data.
    """

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
        """
        Compute and return a list of tuples containing course enrollment
        health data.

        This method fetches the course schedule from the database, groups the
        data by combined course ID, calculates the weighted enrollment total
        for each group, and assigns a health color based on the total
        enrollment. Courses with a weighted enrollment total less than 12 are
        marked red, those with a total less than 32 are marked green, and
        others are marked blue.

        :return: A list of tuples where each tuple contains:
            - Combined course ID (str)
            - Filtered DataFrame for the course (DataFrame)
            - Health color (str)
            - Group weighted enrollment total (int)

        :rtype: List[Tuple[str, DataFrame, str, int]]
        """
        data: List[Tuple[str, DataFrame, str]] = []

        FILTER_FIELDS: List[str] = [
            "FQ_CLASS_SECTION",
            "CLASS TITLE",
            "INSTRUCTOR",
            "ENROLL TOTAL",
            "TRAD MEETING PATTERN",
            "CLASS START TIME",
            "CLASS END TIME",
        ]

        report: List[Tuple[int, str, DataFrame]] = []

        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        dfs: DataFrameGroupBy = df.groupby(by="COMBINED_ID")

        name: str
        group: DataFrame
        for name, group in dfs:
            report.append((group["WEIGHTED_ENROLL_TOTAL"].sum(), name, group))

        report = sorted(report, key=lambda tup: tup[0])

        entry: Tuple[int, str, DataFrame]
        for entry in report:
            color: str = "blue"

            filteredDF: DataFrame = entry[2][FILTER_FIELDS]

            groupSum: int = entry[0]

            if groupSum < 12:
                color = "red"

            if groupSum < 32:
                color = "green"

            data.append((entry[1], filteredDF, color, groupSum))

        return data

    def run(self) -> None:
        """
        Execute the workflow to compute and display course enrollment health.

        This method computes the health of course enrollments, clears existing
        content, and updates the Streamlit session state with the resulting
        data and metadata for visualization.

        :return: None
        """
        data: List[Tuple[str, DataFrame, str, int]] = self.compute()

        clearContent()

        dfs: List[DataFrame] = [datum[1] for datum in data]

        streamlit.session_state["analyticTitle"] = "Course Enrollment Health"
        streamlit.session_state["analyticSubtitle"] = "Health of each course"
        streamlit.session_state["dfList"] = dfs
        streamlit.session_state["dfListTitles"] = [datum[0] for datum in data]
        streamlit.session_state["dfListSubtitles"] = [
            f":{color}[Weighted Enrollments = {amount}]"
            for _, _, color, amount in data
        ]

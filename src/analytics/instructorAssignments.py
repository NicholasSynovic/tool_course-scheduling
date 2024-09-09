from collections import defaultdict
from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent
from src.utils.analytic import Analytic


class InstructorAssignments(Analytic):
    """
    Class to compute and display instructor assignments.

    This class provides functionalities to compute the number of courses
    assigned to each instructor and visualize these assignments using
    Streamlit.
    """

    def __init__(self, conn: Connection) -> None:
        """
        Initialize the InstructorAssignments class with a database connection.

        Sets up the database connection which will be used to compute and
        visualize the assignments for each instructor.

        :param conn: A database connection object.
        :type conn: Connection
        """
        self.conn: Connection = conn

    def compute(self, filterZeroEnrollment: bool = False) -> DataFrameGroupBy:
        """
        Initialize the InstructorAssignments class with a database connection.

        Sets up the database connection which will be used to compute and
        visualize the assignments for each instructor.

        :param conn: A database connection object.
        :type conn: Connection
        """
        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        if filterZeroEnrollment:
            df = df[df["ENROLL TOTAL"] > 0]

        return df.groupby(by="INSTRUCTOR")

    def run(self) -> None:
        """
        Execute the workflow to compute and display instructor assignments.

        Computes the instructor assignments data, clears existing content, and
        updates the Streamlit session state with the resulting data for
        visualization.

        :return: None
        :rtype: None
        """
        clearContent()
        dfList: List[DataFrame] = []
        dfListTitles: List[str] = []

        dfs: DataFrameGroupBy = self.compute(
            filterZeroEnrollment=streamlit.session_state["filterZero"]
        )

        streamlit.session_state["analyticTitle"] = "Instructor Assignments"
        streamlit.session_state["analyticSubtitle"] = (
            "Show instructor assignments"
        )

        streamlit.session_state["filterZero"] = streamlit.checkbox(
            "Filter out rows with ENROLL TOTAL as 0", value=False
        )

        # streamlit.session_state["filterZero"] = False

        instructor_counts = defaultdict(int)
        instructor: str
        df: DataFrame
        for instructor, df in dfs:
            group: DataFrameGroupBy = df.groupby(by="COMBINED ID")

            _df: DataFrame
            for _, _df in group:
                dfList.append(_df)
                instructor_counts[instructor] += 1

        dfListTitles = []

        for instructor, count in instructor_counts.items():
            for i in range(1, count + 1):
                dfListTitles.append(f"{instructor} ({i}/{count})")

        streamlit.session_state["dfList"] = dfList
        streamlit.session_state["dfListTitles"] = dfListTitles

    def plot(self, data: None) -> None:
        """
        Empty function required by Analytic ABC
        :param data: Null
        :type data: None
        """
        pass

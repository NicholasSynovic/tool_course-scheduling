from itertools import count
from math import ceil
from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy

from cs.analytics.courseSchedule import CourseSchedule
from cs.utils import clearContent
from cs.utils.analytic import Analytic


class zeroEnrollment(Analytic):
    """
    Analytic class for identifying and displaying courses with zero enrollment.

    Inherits from the Analytic abstract base class and implements methods
    for computing and visualizing courses with zero student enrollment.

    Attributes:
        conn (Connection): Database connection object used for querying course data.

    Methods:
        __init__(self, conn: Connection) -> None:
            Initialize the zeroEnrollment class with a database connection.

        compute(self) -> DataFrameGroupBy:
            Compute the course data and group by combined ID.

        run(self) -> None:
            Analyzes and displays courses with zero enrollment.

        plot(self, data: None) -> None:
            Empty method required by the Analytic abstract base class.
    """

    def __init__(self, conn: Connection) -> None:
        """
        Initialize the InTroubleCourses class with a database connection.

        Sets up the database connection which will be used to compute and
        visualize the courses with low enrollments.

        :param conn: A database connection object.
        :type conn: Connection
        """
        self.conn: Connection = conn

    def compute(self) -> DataFrameGroupBy:
        """
        Compute the course data and group by combined ID.

        Fetches the course schedule data from the database and filters the
        necessary fields. The data is then grouped by the combined ID of the
        courses.

        :return: A DataFrameGroupBy object containing the grouped course
            schedule data by combined ID.
        :rtype: DataFrameGroupBy
        """
        FILTER_FIELDS: List[str] = [
            "FQ CLASS SECTION",
            "CLASS TITLE",
            "INSTRUCTOR",
            "ENROLL TOTAL",
            "TRAD MEETING PATTERN",
            "CLASS START TIME",
            "CLASS END TIME",
            "WEIGHTED ENROLL TOTAL",
            "COMBINED ID",
        ]

        df: DataFrame = CourseSchedule(conn=self.conn).compute()
        df = df[FILTER_FIELDS]

        return df.groupby(by="FQ CLASS SECTION")

    def run(self) -> None:
        """
        Analyzes and displays courses with zero enrollment.

        This method performs the following actions:
        1. Clears the current content.
        2. Sets the analytic title and subtitle in the Streamlit session state.
        3. Computes the data for analysis.
        4. Filters the computed data to identify courses with zero student enrollment.
        5. Updates the Streamlit session state with the filtered data and their respective titles.

        :return: None
        """
        clearContent()

        streamlit.session_state["analyticTitle"] = "Courses with 0 enrollment"
        streamlit.session_state["analyticSubtitle"] = (
            "List of courses with no students enrolled in them"
        )

        dfList: List[DataFrame] = []
        dfListTitles: List[str] = []

        dfs: DataFrameGroupBy = self.compute()

        group: DataFrame
        for _, group in dfs:
            fq_class_section = group["FQ CLASS SECTION"].iloc[0]
            group_sum: int = ceil(group["WEIGHTED ENROLL TOTAL"].sum())
            if group_sum == 0:
                dfListTitles.append(f"COMP {fq_class_section}")
                dfList.append(group)

        streamlit.session_state["dfList"] = dfList
        streamlit.session_state["dfListTitles"] = dfListTitles

    def plot(self, data: None) -> None:
        """
        Empty function required by Analytic ABC
        :param data: Null
        :type data: None
        """
        pass

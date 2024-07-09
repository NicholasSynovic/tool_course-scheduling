from itertools import count
from math import ceil
from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame
from pandas.core.groupby import DataFrameGroupBy

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent
from src.utils.analytic import Analytic


class InTroubleCourses(Analytic):
    """
    InTroubleCourses class to identify and display courses with low
    enrollments.

    This class provides functionalities to compute the courses that are in
    trouble due to low enrollments and visualize these courses using
    Streamlit.
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

        return df.groupby(by="COMBINED ID")

    def run(self) -> None:
        """
        Execute the workflow to compute and display courses with low
        enrollments.

        Computes the courses that are in trouble due to low enrollments,
        clears existing content, and updates the Streamlit session state with
        the resulting data for visualization.

        :return: None
        :rtype: None
        """
        clearContent()

        streamlit.session_state["analyticTitle"] = "In Trouble Courses"
        streamlit.session_state["analyticSubtitle"] = "Courses in trouble"

        dfList: List[DataFrame] = []
        dfListTitles: List[str] = []

        troubleThreshold: int = 10
        inTroubleCount: count = count(start=1)

        dfs: DataFrameGroupBy = self.compute()

        group: DataFrame
        for _, group in dfs:
            group_sum: int = ceil(group["WEIGHTED ENROLL TOTAL"].sum())
            if group_sum < troubleThreshold:
                in_trouble_val = next(inTroubleCount)
                group_color = "green" if group_sum >= 12 else "red"  # for now
                dfListTitles.append(
                    f":{group_color}[Course {in_trouble_val} has {group_sum} enrollments]"  # noqa: E501
                )
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

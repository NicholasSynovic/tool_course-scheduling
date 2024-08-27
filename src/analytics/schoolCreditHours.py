from sqlite3 import Connection
from typing import List, Tuple

import matplotlib.pyplot as plt
import streamlit
from pandas import DataFrame

from src.analytics.courseSchedule import CourseSchedule
from src.utils.analytic import Analytic


class SchoolCreditHours(Analytic):

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
        # Fetch the course schedule data
        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        # Ensure the necessary columns are present
        if (
            "ENROLL TOTAL" not in df.columns
            or "WEIGHTED ENROLL TOTAL" not in df.columns
            or "CATALOG NUMBER" not in df.columns
        ):
            raise KeyError(
                "Necessary columns ('ENROLL TOTAL', 'WEIGHTED ENROLL TOTAL', 'CATALOG NUMBER') are missing from the data."  # noqa: E501
            )

        # Derive course level from 'CATALOG NUMBER'
        df["COURSE LEVEL"] = (
            df["CATALOG NUMBER"].astype(str).str[:3].astype(int) // 100 * 100
        )

        # Group by course level and sum the enrollments
        grouped_df = (
            df.groupby("COURSE LEVEL")
            .agg({"ENROLL TOTAL": "sum", "WEIGHTED ENROLL TOTAL": "sum"})
            .reset_index()
        )

        return grouped_df

    def run(self) -> None:
        data: DataFrame = self.compute()

        # Update the Streamlit session state for visualization
        streamlit.session_state["analyticTitle"] = "School Credit Hours"
        streamlit.session_state["analyticSubtitle"] = (
            "Sum of Course Enrollment and Weighted Enrollment"
        )
        streamlit.session_state["dfList"] = [data]
        streamlit.session_state["dfListTitles"] = [
            "Total Enrollment by Course Level"
        ]
        streamlit.session_state["dfListSubtitles"] = ["Enrollment Data"]

        # Optionally, trigger the plot function
        self.plot(data)

    def plot(self, data: None) -> None:

        data.plot(
            kind="bar",
            x="COURSE LEVEL",
            y=["ENROLL TOTAL", "WEIGHTED ENROLL TOTAL"],
        )
        plt.title("Enrollment by Course Level")
        plt.xlabel("Course Level")
        plt.ylabel("Enrollment")
        plt.xticks(rotation=0)
        plt.show()

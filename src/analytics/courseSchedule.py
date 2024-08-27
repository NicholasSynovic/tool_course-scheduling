from sqlite3 import Connection
from typing import List

import pandas
import streamlit
from pandas import DataFrame

from src.utils import clearContent


class CourseSchedule:
    """
    A class to manage and retrieve course schedules from a database based on
    predefined department filters.

    This class allows filtering and retrieving detailed information about
    course schedules, excluding certain catalog numbers and sections according
    to department-specific criteria.

    :param conn: A connection to the database containing the course schedules.
    :type conn: Connection
    """

    def __init__(self, conn: Connection) -> None:
        """
        Initialize the CourseEnrollmentHealth class with a database
        connection.

        This constructor sets up the database connection which will be used to
        compute and visualize the health of course enrollments. It also
        initializes department filters for querying specific departments'
        course data.

        :param conn: A database connection object.
        :type conn: Connection
        """

        self.conn: Connection = conn

        # NOTE: Other departments can be added by creating a
        # new key and SQL query per department
        self.departmentFilters: dict[str, str] = {
            "COMP": """SUBJECT = 'COMP' AND "CATALOG NUMBER" NOT IN ('391', '398', '490', '499', '605') AND "CATALOG NUMBER" NOT IN ('215', '231', '331', '431', '381', '386', '383', '483') AND SECTION NOT IN ('01L', '02L', '03L', '04L', '05L', '06L', '700N')"""  # noqa: E501
        }

    def compute(self) -> DataFrame:
        """
        Compute the course schedule data filtered by department and minimum
        enrollment.

        This method fetches the course schedule from the database, applies
        filters based on department, and filters out courses with enrollment
        below the specified minimum enrollment. If `filterZeroEnrollment` is
        True, courses with an "ENROLL TOTAL" of 0 will be excluded. The
        resulting data is returned as a DataFrame.

        :param minimumEnrollment: The minimum number of students enrolled to
            include a course, defaults to 0
        :type minimumEnrollment: int, optional
        :param filterZeroEnrollment: Whether to filter out courses with zero
            enrollment, defaults to False
        :type filterZeroEnrollment: bool, optional
        :return: A DataFrame containing the filtered course schedule data.
        :rtype: DataFrame
        """

        whereClauses: str = "WHERE " + " or ".join(
            [
                "(" + self.departmentFilters[filter] + ")"
                for filter in self.departmentFilters
            ]
        )

        query: str = (
            """SELECT SUBJECT, "WEIGHTED ENROLL TOTAL", "CATALOG NUMBER", "FQ CATALOG NUMBER", "FQ CLASS SECTION", "CLASS TITLE", INSTRUCTOR, "ENROLL TOTAL", "TRAD MEETING PATTERN", "CLASS START TIME", "CLASS END TIME", "UNIT CLASS DURATION", "INSTRUCTIONAL TIME", FACILITY, "COMBINED ID" FROM schedule """  # noqa: E501
        )

        query = query + whereClauses + ";"
        query = query.strip()

        df: DataFrame = pandas.read_sql_query(
            sql=query,  # nosec
            con=self.conn,
        )

        df.reset_index(drop=True, inplace=True)

        return df

    def run(self) -> None:
        """
        Execute the workflow to compute and display the course schedule.

        This method computes the course schedule data, clears any existing
        content, and updates the Streamlit session state with the resulting
        data for visualization.

        :return: None
        """

        clearContent()

        dfs: List[DataFrame] = [self.compute()]

        streamlit.session_state["analyticTitle"] = "Course Schedule"
        streamlit.session_state["analyticSubtitle"] = (
            "The current course \
        schedule"
        )

        streamlit.session_state["dfList"] = dfs

    def plot(self, data: None) -> None:
        """
        Empty function required by Analytic ABC
        :param data: Null
        :type data: None
        """
        pass

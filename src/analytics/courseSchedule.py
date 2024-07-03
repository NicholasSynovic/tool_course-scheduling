from sqlite3 import Connection
from typing import List

import pandas
import streamlit
from pandas import DataFrame

from src.utils import clearContent


class CourseSchedule:
    """
    A class to manage and retrieve course schedules from a database based on predefined department filters.

    This class allows filtering and retrieving detailed information about course schedules, excluding certain
    catalog numbers and sections according to department-specific criteria.

    :param conn: A connection to the database containing the course schedules.
    :type conn: Connection
    """  # noqa: E501

    def __init__(self, conn: Connection) -> None:
        """
        Initialize the class with a database connection and department filters.

        Parameters
        ----------
        conn : Connection
            A database connection object.

        Returns
        -------
        None

        Notes
        -----
        This constructor initializes the class instance with a database connection and pre-defined department filters
        for courses. Each filter corresponds to a specific department and excludes certain course numbers and sections
        from the query.

        Examples
        --------
        >>> import sqlite3
        >>> conn = sqlite3.connect(":memory:")
        >>> example_instance = MyClass(conn)
        [Initializes an instance of MyClass with a database connection]
        """  # noqa: E501

        self.conn: Connection = conn

        # NOTE: Other departments can be added by creating a
        # new key and SQL query per department
        self.departmentFilters: dict[str, str] = {
            "COMP": """SUBJECT = 'COMP' AND "CATALOG NUMBER" NOT IN ('391', '398', '490', '499', '605') AND "CATALOG NUMBER" NOT IN ('215', '231', '331', '431', '381', '386', '383', '483') AND SECTION NOT IN ('01L', '02L', '03L', '04L', '05L', '06L', '700N')"""  # noqa: E501
        }

    def compute(self, minimumEnrollment: int = 0) -> DataFrame:
        """
        Retrieve and filter course schedule data from the database.

        Parameters
        ----------
        minimumEnrollment : int, optional
            Minimum enrollment threshold for filtering courses. Default is 0.

        Returns
        -------
        pandas.DataFrame
            A DataFrame containing filtered course schedule information.

        Notes
        -----
        This method performs the following steps:
        1. Checks if the input `minimumEnrollment` is less than 0 and adjusts it to 0 if necessary.
        2. Constructs a SQL query combining department filters and retrieves course schedule data from the database.
        3. Drops duplicate entries based on 'FQ_CLASS_SECTION'.
        4. Fills missing values in 'COMBINED_ID' with '(UNKNOWN, N/A, N/A)'.
        5. Filters the DataFrame to include only courses with enrollment greater than or equal to `minimumEnrollment`.
        6. Resets the DataFrame index for consistency.
        7. Returns the filtered DataFrame.

        Examples
        --------
        >>> example_instance.get(minimumEnrollment=20)
        [Returns a DataFrame with course schedule information filtered by minimum enrollment]
        """  # noqa: E501

        if minimumEnrollment < 0:
            minimumEnrollment = 0

        whereClasues: str = "WHERE " + " or ".join(
            [
                "(" + self.departmentFilters[filter] + ")"
                for filter in self.departmentFilters
            ]
        )

        query: str = (
            """SELECT SUBJECT, WEIGHTED_ENROLL_TOTAL, "CATALOG NUMBER", SUBJECT || '-' || "CATALOG NUMBER" as FQ_CATALOG_NUMBER, "CATALOG NUMBER" || '-' || SECTION as FQ_CLASS_SECTION, "CLASS TITLE", INSTRUCTOR, "ENROLL TOTAL", "TRAD MEETING PATTERN", "CLASS START TIME", "CLASS END TIME", "UNIT CLASS DURATION", "INSTRUCTIONAL TIME", FACILITY, '(' || INSTRUCTOR || ',' || FACILITY || ',' || "MEETING PATTERN" || ',' || "CLASS START TIME" || ',' || "CLASS END TIME" || ')' as COMBINED_ID FROM schedule """  # noqa: E501
        )

        query = query + whereClasues + ";"
        query = query.strip()

        df: DataFrame = pandas.read_sql_query(
            sql=query,  # nosec
            con=self.conn,
        )

        df.drop_duplicates(
            subset=["FQ_CLASS_SECTION"],
            inplace=True,
            ignore_index=True,
        )

        df["COMBINED_ID"] = df["COMBINED_ID"].fillna(
            value="(UNKNOWN, N/A, N/A)",
        )

        df = df[df["ENROLL TOTAL"] >= minimumEnrollment]

        df.reset_index(drop=True, inplace=True)

        return df

    def run(self) -> None:
        """
        Fetch and store course schedule data in the session state.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Notes
        -----
        This method performs the following steps:
        1. Initializes `streamlit.session_state['df']` and `streamlit.session_state['fig']` to None.
        2. Calls the `get` method to retrieve course schedule data and assigns it to `df`.
        3. Stores the fetched DataFrame `df` in `streamlit.session_state['df']`.

        Examples
        --------
        >>> example_instance.run()
        [Fetches and stores course schedule data in the session state]
        """  # noqa: E501

        clearContent()

        dfs: List[DataFrame] = [self.compute()]

        streamlit.session_state["analyticTitle"] = "Course Schedule"
        streamlit.session_state["analyticSubtitle"] = (
            "The current course \
        schedule"
        )
        streamlit.session_state["dfList"] = dfs

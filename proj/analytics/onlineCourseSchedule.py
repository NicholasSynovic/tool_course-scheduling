from sqlite3 import Connection

import streamlit
from pandas import DataFrame

from proj.analytics.courseSchedule import CourseSchedule


class OnlineCourseSchedule:
    """
    Class to retrieve and manage online course schedule data.

    Attributes
    ----------
    conn : Connection
        A database connection object.

    Methods
    -------
    __init__(conn: Connection) -> None:
        Initialize the class with a database connection.

    get() -> pandas.DataFrame:
        Retrieve course schedule data filtered by 'ONLINE' facility and return as a DataFrame.

    run() -> None:
        Run the workflow to retrieve course schedule data and store it in Streamlit session state.
    """  # noqa: E501

    def __init__(self, conn: Connection) -> None:
        """
        Initialize the class with a database connection.

        Parameters
        ----------
        conn : Connection
            A database connection object.

        Returns
        -------
        None

        Notes
        -----
        This constructor initializes the class instance with a provided database connection object.

        Examples
        --------
        >>> import sqlite3
        >>> conn = sqlite3.connect(":memory:")
        >>> example_instance = MyClass(conn)
        [Initializes an instance of MyClass with a database connection]
        """  # noqa: E501

        self.conn: Connection = conn

    def get(self) -> DataFrame:
        """
        Retrieve course schedule data filtered by 'ONLINE' facility and return as a DataFrame.

        Parameters
        ----------
        None

        Returns
        -------
        pandas.DataFrame
                A DataFrame containing course schedule data filtered by 'ONLINE' facility.

        Notes
        -----
                This method performs the following steps:
                        1. Retrieves course schedule data using the `get` method from the `CourseSchedule` class with the stored connection object.
                        2. Filters rows where the 'FACILITY' column equals 'ONLINE'.
                        3. Resets the index of the resulting DataFrame for clarity.

        Examples
        --------
                >>> example_instance.get()
                [Returns a DataFrame with course schedule data filtered by 'ONLINE' facility]
        """  # noqa: E501

        df: DataFrame = CourseSchedule(conn=self.conn).get()

        df = df[df["FACILITY"] == "ONLINE"]

        df.reset_index(drop=True, inplace=True)

        return df

    def run(self) -> None:
        """
        Run the workflow to retrieve course schedule data and store it in Streamlit session state.

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
            2. Retrieves course schedule data using the `get` method and assigns the result to `df`.
            3. Stores the retrieved DataFrame `df` in `streamlit.session_state` for use in the Streamlit app.

        Examples
        --------
        >>> example_instance.run()
        [Runs the workflow to retrieve and store course schedule data in Streamlit session state.]
        """  # noqa: E501

        streamlit.session_state["df"] = None
        streamlit.session_state["fig"] = None

        df: DataFrame = self.get()

        streamlit.session_state["df"] = df

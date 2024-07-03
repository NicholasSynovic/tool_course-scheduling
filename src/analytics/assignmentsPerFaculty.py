from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame, Series
from plotly import express
from plotly.graph_objects import Figure
from proj.analytics.courseSchedule import CourseSchedule
from proj.utils import clearContent


class AssignmentsPerFaculty:
    """
    Class to compute and visualize assignments per faculty member.

    Attributes
    ----------
    conn : Connection
        A database connection object.

    Methods
    -------
    __init__(conn: Connection) -> None:
        Initialize the class with a database connection.

    compute() -> pandas.DataFrame:
        Compute and return a DataFrame with the number of courses taught by each instructor.

    plot(df: pandas.DataFrame) -> plotly.graph_objs.Figure:
        Plot a horizontal bar chart showing the number of courses taught by each instructor.

    run() -> None:
        Run the workflow to compute and plot assignments per instructor.
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

        self.conn = conn

    def compute(self) -> DataFrame:
        """
        Compute and return a DataFrame with the number of courses taught by each instructor.

        Parameters
        ----------
        None

        Returns
        -------
        pandas.DataFrame
            A DataFrame containing the count of courses taught by each instructor.

        Notes
        -----
        This method performs the following steps:
        1. Retrieves course schedule data using the `get` method from the `CourseSchedule` class and assigns it to `df`.
        2. Counts the occurrences of each unique instructor in the 'INSTRUCTOR' column of `df`.
        3. Creates a new DataFrame `dataDF` from the counted series, renaming columns to 'Instructor Name' and 'Number of Courses'.
        4. Filters out rows where the 'Instructor Name' is 'UNKNOWN'.
        5. Returns the filtered DataFrame.

        Examples
        --------
        >>> example_instance.compute()
        [Returns a DataFrame with the number of courses taught by each instructor]
        """  # noqa: E501

        df: DataFrame = CourseSchedule(conn=self.conn).compute()

        data: Series[int] = df["INSTRUCTOR"].value_counts(
            sort=True,
            ascending=False,
        )

        dataDF: DataFrame = data.reset_index()
        dataDF.columns = ["Instructor Name", "Number of Courses"]

        return dataDF[dataDF["Instructor Name"] != "UNKNOWN"]

    def plot(self, df: DataFrame) -> Figure:
        """
        Plot a horizontal bar chart showing the number of courses taught by each instructor.

        Parameters
        ----------
        df : pandas.DataFrame
            A DataFrame containing data with columns 'Instructor Name' and 'Number of Courses'.

        Returns
        -------
        plotly.graph_objs.Figure
            A Plotly figure object representing the horizontal bar chart.

        Notes
        -----
        This method uses Plotly Express to generate a horizontal bar chart with the following settings:
        - 'Instructor Name' on the y-axis and 'Number of Courses' on the x-axis.
        - The chart title is set to "Number of Assignments per Instructor".
        - Axes labels are customized to "Instructor Name" and "Number of Courses".
        - The y-axis category order is set to ascending based on the total number of courses.

        Examples
        --------
        >>> df = example_instance.compute()
        >>> fig = example_instance.plot(df)
        [Generates and returns a Plotly figure showing the number of courses taught by each instructor]
        """  # noqa: E501

        fig = express.bar(
            data_frame=df,
            y="Instructor Name",
            x="Number of Courses",
            orientation="h",
            title="Number of Assignments per Instructor",
            labels={
                "Instructor Name": "Instructor Name",
                "Number of Courses": "Number of Courses",
            },
        )

        fig.update_layout(
            xaxis_title="Number of Courses",
            yaxis_title="Instructor Name",
        )

        return fig

    def run(self) -> None:
        """
        Run the workflow to compute and plot assignments per instructor.

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
        2. Computes the number of courses taught by each instructor using the `compute` method and assigns the result to `df`.
        3. Generates a horizontal bar chart showing the number of courses per instructor using the `plot` method and assigns the figure to `fig`.
        4. Stores the computed DataFrame `df` and the generated figure `fig` in `streamlit.session_state` for use in the Streamlit app.

        Examples
        --------
        >>> example_instance.run()
        [Runs the workflow to compute and plot assignments per instructor]
        """  # noqa: E501

        clearContent()

        dfs: List[DataFrame] = [self.compute()]
        figs: List[Figure] = [self.plot(df=df) for df in dfs]

        streamlit.session_state["analyticTitle"] = (
            "Number of Assignments Per Faculty Member"
        )
        streamlit.session_state["analyticSubtitle"] = (
            "The number of courses that are assigned to each faculty member \
                for the current term"
        )
        streamlit.session_state["dfList"] = dfs
        streamlit.session_state["dfListTitles"] = ["Faculty Assignment Count"]

        streamlit.session_state["figList"] = figs
        streamlit.session_state["figListTitles"] = [
            "Faculty Assignment Count Plot"
        ]

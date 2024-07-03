from datetime import datetime
from sqlite3 import Connection
from typing import List

import pandas
import streamlit
from intervaltree import Interval, IntervalTree
from pandas import DataFrame, Series
from plotly import graph_objects
from plotly.graph_objects import Figure

from proj.analytics.courseSchedule import CourseSchedule
from proj.utils import clearContent, datetimeToMinutes


class ScheduleDensity:
    """
    Class to compute and visualize schedule density based on course schedule data.

    Attributes
    ----------
    conn : Connection
        A database connection object.

    Methods
    -------
    __init__(conn: Connection) -> None:
        Initialize the class with a database connection.

    compute(courseSchedule: DataFrame) -> dict[str, IntervalTree]:
        Compute and return a dictionary of IntervalTree objects for each day based on course schedule data.

    plot(its: dict[str, IntervalTree], overlapThreshold: int = 2) -> plotly.graph_objs.Figure:
        Plot a schedule density graph based on provided IntervalTree data for each day.

    run() -> None:
        Run the workflow to retrieve course schedule data, compute intervals, plot schedule density, and store results in Streamlit session state.
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

    def compute(
        self,
        courseSchedule: DataFrame,
    ) -> dict[str, IntervalTree]:
        """
        Compute and return a dictionary of IntervalTree objects for each day based on course schedule data.

        Parameters
        ----------
        courseSchedule : pandas.DataFrame
            DataFrame containing course schedule data with columns 'TRAD MEETING PATTERN', 'CLASS START TIME', and 'CLASS END TIME'.

        Returns
        -------
        dict[str, IntervalTree]
            A dictionary where keys are days ('M', 'T', 'W', 'R', 'F', 'S') and values are IntervalTree objects containing class time intervals.

        Notes
        -----
        This method iterates through rows of the provided DataFrame, extracts meeting patterns, start and end times, and constructs IntervalTree objects for each day based on class intervals.

        Examples
        --------
        >>> example_instance.compute(courseSchedule)
        [Returns a dictionary of IntervalTree objects representing class intervals for each day]
        """  # noqa: E501

        dayIntervalTree: dict[str, IntervalTree] = {
            day: IntervalTree()
            for day in [
                "M",
                "T",
                "W",
                "R",
                "F",
                "S",
            ]
        }

        row: Series
        for _, row in courseSchedule.iterrows():
            pattern: str = row["TRAD MEETING PATTERN"]

            startTime: datetime = pandas.to_datetime(
                arg=row["CLASS START TIME"],
                format="%H:%M:%S",
            )
            endTime: datetime = pandas.to_datetime(
                arg=row["CLASS END TIME"],
                format="%H:%M:%S",
            )

            if startTime == endTime:
                continue

            startMinutes: int = datetimeToMinutes(dt=startTime)
            endMinutes: int = datetimeToMinutes(dt=endTime)

            day: str
            for day in pattern:
                interval: Interval = Interval(
                    begin=startMinutes,
                    end=endMinutes,
                )

                dayIntervalTree[day].add(interval)

        return dayIntervalTree

    def plot(
        self,
        its: dict[str, IntervalTree],
        overlapThreshold: int = 2,
    ) -> Figure:
        """
        Plot a schedule density graph based on provided IntervalTree data for each day.

        Parameters
        ----------
        its : dict[str, Interval
        streamlit.session_state["df"] = None
        streamlit.session_state["fig"] = Noneree]
            A dictionary where keys are days ('M', 'T', 'W', 'R', 'F', 'S') and values are IntervalTree objects containing class time intervals.
        overlapThreshold : int, optional
            Minimum number of overlapping intervals to consider for color coding (default is 2).

        Returns
        -------
        plotly.graph_objs.Figure
            A Plotly figure object representing the schedule density graph.

        Notes
        -----
        This method generates a schedule density graph based on the provided IntervalTree data, showing markers for class overlaps across days and times.

        Examples
        --------
        >>> example_instance.plot(its, overlapThreshold=3)
        [Generates and returns a Plotly figure object representing the schedule density graph]
        """  # noqa: E501

        days: List[str] = ["M", "T", "W", "R", "F", "S"]
        days.reverse()

        times: List[datetime] = [
            datetime(2023, 1, 1, hour, minute)
            for hour in range(8, 19)
            for minute in range(0, 60, 5)
        ]

        timeLabels: List[str] = [t.strftime("%H:%M") for t in times]

        markers: List[dict[str, str | int]] = []

        day: str
        time: datetime
        for day in days:
            for time in times:
                color: str = "green"

                minutes: int = datetimeToMinutes(dt=time)
                overlaps: set[Interval] = its[day][minutes]

                overlapCount: int = len(overlaps)

                if overlapCount >= overlapThreshold:
                    color = "red"

                elif overlaps:
                    color = "orange"

                size = 5 + 4 * overlapCount

                markers.append(
                    {
                        "x": minutes,
                        "y": days.index(day),
                        "color": color,
                        "size": size,
                        "overlaps": overlapCount,
                    }
                )

        streamlit.session_state["df"] = None
        streamlit.session_state["fig"] = None
        fig: Figure = Figure()

        marker: dict[str, str | int]
        for marker in markers:
            fig.add_trace(
                graph_objects.Scatter(
                    x=[marker["x"]],
                    y=[marker["y"]],
                    mode="markers",
                    marker=dict(color=marker["color"], size=marker["size"]),
                    text=f"Overlaps: {marker['overlaps']}",
                )
            )

        fig.update_layout(
            title=f"Schedule Density <br><sup>Overlap Interval = {overlapThreshold}</sup>",  # noqa: E501
            xaxis=dict(
                tickvals=[datetimeToMinutes(dt=t) for t in times][
                    ::12
                ],  # Every hour
                ticktext=timeLabels[::12],
                title="Time",
            ),
            yaxis=dict(
                tickvals=list(range(len(days))),
                ticktext=days,
                title="Day of the Week",
            ),
            showlegend=False,
        )

        return fig

    def run(self) -> None:
        """
        Run the workflow to retrieve course schedule data, compute intervals, plot schedule density, and store results in Streamlit session state.

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
        2. Retrieves course schedule data using the `get` method from the `CourseSchedule` class with optional parameters.
        3. Computes day-based IntervalTree objects using the `compute` method based on retrieved course schedule data.
        4. Generates a schedule density plot using the `plot` method with computed IntervalTree objects.
        5. Stores the retrieved DataFrame `df` and generated figure `fig` in `streamlit.session_state` for use in the Streamlit app.

        Examples
        --------
        >>> example_instance.run()
        [Runs the workflow to retrieve, compute, plot, and store course schedule data in Streamlit session state.]
        """  # noqa: E501

        clearContent()

        df: DataFrame = CourseSchedule(conn=self.conn).compute(
            minimumEnrollment=1,
        )

        dayIntervalTrees: dict[str, IntervalTree] = self.compute(
            courseSchedule=df,
        )

        figs: List[Figure] = [self.plot(its=dayIntervalTrees)]

        streamlit.session_state["analyticTitle"] = "Schedule Density"
        streamlit.session_state["analyticSubtitle"] = (
            "Display the density of courses within the schedule"
        )

        streamlit.session_state["figList"] = figs
        streamlit.session_state["figListTitles"] = ["Schedule Density Plot"]

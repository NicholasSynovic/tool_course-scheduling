from datetime import datetime
from sqlite3 import Connection
from typing import List

import pandas
import streamlit
from intervaltree import Interval, IntervalTree
from pandas import DataFrame, Series
from plotly import graph_objects
from plotly.graph_objects import Figure

from src.analytics.courseSchedule import CourseSchedule
from src.utils import clearContent, datetimeToMinutes
from src.utils.analytic import Analytic


class ScheduleDensity(Analytic):
    """
    ScheduleDensity class to compute and visualize the density of course
    schedules.

    This class provides functionalities to compute intervals and visualize the
    density of courses within the schedule using interval trees and Plotly for
    plotting.
    """

    def __init__(self, conn: Connection) -> None:
        """
        Initialize the ScheduleDensity class with a database connection.

        This constructor sets up the database connection which will be used to
        compute and visualize the schedule density data.

        :param conn: A database connection object.
        :type conn: Connection
        """
        self.conn: Connection = conn

    def compute(
        self,
        courseSchedule: DataFrame,
    ) -> dict[str, IntervalTree]:
        """
        Compute interval trees for course schedules.

        This method processes the course schedule data to create interval
        trees for each day of the week, indicating the start and end times of
        courses.

        :param courseSchedule: A DataFrame containing course schedule data.
        :type courseSchedule: DataFrame
        :return: A dictionary mapping days of the week to their respective
            interval trees.
        :rtype: dict[str, IntervalTree]
        """

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
        Plot the schedule density based on interval trees.

        This method creates a plotly figure to visualize the density of course
        schedules, indicating the number of overlapping courses at different
        times of the day.

        :param its: A dictionary mapping days of the week to their respective
            interval trees.
        :type its: dict[str, IntervalTree]
        :param overlapThreshold: The threshold for highlighting overlapping
            courses, defaults to 2.
        :type overlapThreshold: int, optional
        :return: A Plotly figure representing the schedule density.
        :rtype: Figure
        """

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
        Run the workflow to compute and visualize the schedule density.

        This method performs the following steps:
        1. Clears existing content.
        2. Retrieves course schedule data.
        3. Computes interval trees based on the course schedule data.
        4. Plots the schedule density using the computed interval trees.
        5. Updates the Streamlit session state with the resulting figure for
            visualization.

        :return: None
        :rtype: None
        """

        clearContent()

        df: DataFrame = CourseSchedule(conn=self.conn).compute(
            # minimumEnrollment=1,
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

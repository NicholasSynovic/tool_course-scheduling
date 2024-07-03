from datetime import datetime
from sqlite3 import Connection
from typing import List

import pandas
import streamlit
from intervaltree import Interval, IntervalTree
from pandas import DataFrame, Series
from plotly import graph_objects
from plotly.graph_objects import Figure

from proj.utils import datetimeToMinutes


class ScheduleDensity:
    def __init__(self, conn: Connection) -> None:
        self.conn: Connection = conn

        self.departmentFilters: dict[str, str] = {
            "COMP": """SUBJECT = 'COMP' AND "CATALOG NUMBER" NOT IN ('391', '398', '490', '499', '605') AND "CATALOG NUMBER" NOT IN ('215', '231', '331', '431', '381', '386', '383', '483') AND SECTION NOT IN ('01L', '02L', '03L', '04L', '05L', '06L', '700N')"""  # noqa: E501
        }

    def runQuery(self) -> DataFrame:
        whereClasues: str = "WHERE " + " or ".join(
            [
                "(" + self.departmentFilters[filter] + ")"
                for filter in self.departmentFilters
            ]
        )

        query: str = (
            """SELECT SUBJECT, "CATALOG NUMBER", SUBJECT || '-' || "CATALOG NUMBER" as FQ_CATALOG_NUMBER, "CATALOG NUMBER" || '-' || SECTION as FQ_CLASS_SECTION, "CLASS TITLE", INSTRUCTOR, "ENROLL TOTAL", "TRAD MEETING PATTERN", "CLASS START TIME", "CLASS END TIME", "UNIT CLASS DURATION", "INSTRUCTIONAL TIME", FACILITY, '(' || INSTRUCTOR || ',' || FACILITY || ',' || "MEETING PATTERN" || ',' || "CLASS START TIME" || ',' || "CLASS END TIME" || ')' as COMBINED_ID FROM schedule """  # noqa: E501
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

        df = df[df["ENROLL TOTAL"] >= 0]

        return df

    def computeIntervalTrees(
        self,
        df: DataFrame,
    ) -> dict[str, IntervalTree]:
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
        for _, row in df.iterrows():
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

    def generatePlot(
        self,
        its: dict[str, IntervalTree],
        overlapThreshold: int = 2,
    ) -> Figure:
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
            title=f"Schedule Density <br><sup>Overlap Interval = \
                {overlapThreshold}</sup>",
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
        df: DataFrame = self.runQuery()

        dayIntervalTrees: dict[str, IntervalTree] = self.computeIntervalTrees(
            df=df,
        )

        fig: Figure = self.generatePlot(its=dayIntervalTrees)

        streamlit.dataframe(data=df)
        streamlit.plotly_chart(
            figure_or_data=fig,
            use_container_width=True,
        )

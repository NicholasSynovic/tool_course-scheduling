import sqlite3
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from intervaltree import Interval, IntervalTree
from streamlit.runtime.uploaded_file_manager import UploadedFile

st.title("Excel File Uploader")

uploaded_file: UploadedFile = st.file_uploader(
    "Choose an Excel file", type=["xlsx"]
)


# Uses plotly to plot schedule density
def plotDensity(dbPath, df):
    """
    Plot the density of schedule overlaps based on schedule data.

    Parameters
    ----------
    scheduleDf : pandas.DataFrame
        A DataFrame containing schedule information.
    overlap_threshold : int, optional
        Threshold value for determining overlap severity (default is 2).

    Returns
    -------
    None

    Notes
    -----
    This function creates a plot using Plotly to visualize schedule overlaps for each day of the week
    and different times throughout the day. It relies on the `createIntervalTrees` and `timeToMinutes` functions
    to process schedule data and convert time information, respectively.

    Examples
    --------
    >>> import pandas as pd
    >>> schedule_df = pd.DataFrame({
    ...     "SUBJECT": ["COMP", "COMP", "MATH"],
    ...     "CATALOG NUMBER": [101, 102, 201],
    ...     "SECTION": ["001", "002", "001"],
    ...     "CLASS TITLE": ["Introduction to Programming", "Data Structures", "Calculus"],
    ...     "INSTRUCTOR": ["Alan Turing", "Grace Hopper", "Ada Lovelace"],
    ...     "ENROLL TOTAL": [30, 25, 20],
    ...     "MEETING PATTERN": ["MWF", "TTH", "MWF"],
    ...     "CLASS START TIME": ["09:00:00", "13:00:00", "10:00:00"],
    ...     "CLASS END TIME": ["10:30:00", "14:45:00", "11:30:00"],
    ...     "FACILITY": ["Main Building", "Science Building", "Math Building"]
    ... })
    >>> plotScheduleWithOverlap(schedule_df)
    [Generates a plot displaying schedule density and overlap]
    """

    conn = sqlite3.connect(dbPath)

    table = "schedule"
    df.to_sql(table, conn, if_exists="replace", index=False)

    depts = ["COMP"]

    # You can add other departments to the report by creating a department-specific filter.
    # Make sure you create a filter for each department (e.g. musc_filter) and add this filter to the dictionary of dept_filters.

    comp_filter = """
        SUBJECT = 'COMP'
            and
        "CATALOG NUMBER" not in ('391', '398', '490', '499', '605')
            and
        "CATALOG NUMBER" not in ('215', '231', '331', '431', '381', '386', '383', '483')
            and
        "SECTION" not in ('01L', '02L', '03L', '04L', '05L', '06L', '700N')
    """

    dept_filters = {"COMP": comp_filter}

    where_clause = "\n  WHERE " + " or ".join(
        ["(" + dept_filters[filter] + ")" for filter in dept_filters]
    )

    query = (
        """
    SELECT
        SUBJECT,
        "CATALOG NUMBER",
        SUBJECT || "-" || "CATALOG NUMBER" as FQ_CATALOG_NUMBER,
        "CATALOG NUMBER" || '-' || SECTION as FQ_CLASS_SECTION,
        "CLASS TITLE",
        INSTRUCTOR,
        "ENROLL TOTAL",
        "MEETING PATTERN",
        "CLASS START TIME",
        "CLASS END TIME",
        FACILITY,
        '(' || INSTRUCTOR || ',' || FACILITY || ',' || "MEETING PATTERN" || ',' ||"CLASS START TIME" || ',' || "CLASS END TIME" || ')' as COMBINED_ID
    FROM
        schedule """
        + where_clause
    )

    query = query.strip()
    # print(query)

    df = pd.read_sql_query(query, conn)
    conn.close()

    pd.options.display.max_rows = 999

    df2 = df.drop_duplicates(subset=["FQ_CLASS_SECTION"])

    df2 = df2.copy()

    unknown_instructor_name = "Turing, Alan"  # This has long been our "default" for unassigned courses. I don't expect anyone with this name to be on faculty.
    df2["INSTRUCTOR"].fillna(unknown_instructor_name)

    unknown_combined_id = "(Doyle Center, No Start Time, No End Time)"
    df2["COMBINED_ID"].fillna(unknown_combined_id)

    def traditional_meeting_pattern(row):
        meeting_pattern = row["MEETING PATTERN"]
        if meeting_pattern:
            return (
                meeting_pattern.replace("TR", "R")
                .replace("SA", "S")
                .replace("SU", "X")
            )  # Remove all 2-letter codes and follow MTWRFSX format.
        else:
            return ""

    def time_to_minutes(t):
        return t.hour * 60 + t.minute

    def unit_class_duration(row):
        start = row["CLASS START TIME"]
        end = row["CLASS END TIME"]

        if not start or not end:
            return 0
        start_time = datetime.strptime(start, "%H:%M:%S")
        end_time = datetime.strptime(end, "%H:%M:%S")
        start_minutes = time_to_minutes(start_time)
        end_minutes = time_to_minutes(end_time)
        total_minutes = end_minutes - start_minutes
        return total_minutes

    def instructional_time(row):
        meeting_pattern = row["TRAD MEETING PATTERN"]
        return len(meeting_pattern) * row["UNIT CLASS DURATION"]

    # df2 = df2.copy()
    # Really bad LOCUS thing: M,T,W,TR,F,SA
    # I'm using M,T,W,T,F. If we ever use SU it would become X to denote why we shouldn't do it.

    df2["TRAD MEETING PATTERN"] = df2.apply(
        traditional_meeting_pattern, axis=1
    )

    # A bit of data cleansing just to remove the unwanted time information from the Excel to SQLLite3 conversion.

    df2["CLASS START TIME"] = df["CLASS START TIME"].str.split(" ").str[1]
    df2["CLASS END TIME"] = df["CLASS END TIME"].str.split(" ").str[1]
    df2["COMBINED_ID"] = df["COMBINED_ID"].str.replace("1900-01-01", "")

    df2["UNIT CLASS DURATION"] = df2.apply(unit_class_duration, axis=1)
    df2["INSTRUCTIONAL TIME"] = df2.apply(instructional_time, axis=1)

    # key_fields_of_interest = ['SUBJECT','CATALOG_NUMBER','FQ_CATALOG_NUMBER','FQ_CLASS_SECTION', 'CLASS TITLE', 'INSTRUCTOR', 'ENROLL TOTAL', 'MEETING_PATTERN','CLASS_START_TIME','CLASS_END_TIME', 'FACILITY','COMBINED_ID']
    FILTER_FIELDS = [
        "FQ_CLASS_SECTION",
        "CLASS TITLE",
        "INSTRUCTOR",
        "ENROLL TOTAL",
        "TRAD MEETING PATTERN",
        "INSTRUCTIONAL TIME",
        "MEETING PATTERN",
        "UNIT CLASS DURATION",
        "CLASS START TIME",
        "CLASS END TIME",
        "FACILITY",
        "COMBINED_ID",
    ]

    # Now 'df' holds the contents of 'your_table' as a Pandas DataFrame
    # Filter out any sectinos with 0. If enrollment is 0, likely to be cancelled anyway.
    group = df2[df2["ENROLL TOTAL"] >= 0]

    df2 = group
    print(df2[FILTER_FIELDS])

    schedule_df = group

    def time_to_minutes(t):
        return t.hour * 60 + t.minute

    # One of the most important data structures (hope we're teaching it)
    def create_interval_trees(schedule):
        day_trees = {
            day: IntervalTree() for day in ["M", "T", "W", "R", "F", "S"]
        }
        # print(day_trees)
        for index, row in schedule_df.iterrows():
            pattern = row["TRAD MEETING PATTERN"]
            start = row["CLASS START TIME"]
            end = row["CLASS END TIME"]
            if start == end:
                continue
            start_time = datetime.strptime(start, "%H:%M:%S")
            end_time = datetime.strptime(end, "%H:%M:%S")
            start_minutes = time_to_minutes(start_time)
            end_minutes = time_to_minutes(end_time)
            total_minutes = 0
            for day in pattern:  # e.g. ('M', 'W', 'F') iterates as 'M','W','F'
                interval = Interval(start_minutes, end_minutes)
                try:
                    day_trees[day].add(interval)
                    total_minutes += end_minutes - start_minutes
                except:
                    print(interval, start_time, end_time, pattern)
            if (
                total_minutes != 150
            ):  # TODO: We need # credits to know the correct answer but this catches MOST
                print(
                    "Checking for duraton != 150 minutes (possibly ok): ",
                    row["FQ_CLASS_SECTION"],
                    row["TRAD MEETING PATTERN"],
                    row["CLASS START TIME"],
                    row["CLASS END TIME"],
                )
        return day_trees

    # Assume create_interval_trees and time_to_minutes are defined elsewhere

    def plot_schedule_with_overlap(schedule, overlap_threshold=2):
        days = ["M", "T", "W", "R", "F", "S"]
        days.reverse()  # For more natural appearance on the chart.
        times = [
            datetime(2023, 1, 1, hour, minute)
            for hour in range(8, 19)
            for minute in range(0, 60, 5)
        ]  # todo remove hard-coding of year/1/1 (safe though)
        time_labels = [t.strftime("%H:%M") for t in times]
        day_trees = create_interval_trees(schedule)

        max_overlap = 0
        markers = []

        for day_index, day in enumerate(days):
            for t in times:
                minutes = time_to_minutes(t)
                overlaps = day_trees[day][minutes]
                color = "green"
                if len(overlaps) >= overlap_threshold:
                    color = "red"
                elif overlaps:
                    color = "orange"
                if len(overlaps) > max_overlap:
                    max_overlap = len(overlaps)
                size = 5 + 4 * len(
                    overlaps
                )  # Base size + additional size for each overlap

                markers.append(
                    {
                        "x": minutes,
                        "y": day_index,
                        "color": color,
                        "size": size,
                        "overlaps": len(overlaps),
                    }
                )

        fig = go.Figure()

        for marker in markers:
            fig.add_trace(
                go.Scatter(
                    x=[marker["x"]],
                    y=[marker["y"]],
                    mode="markers",
                    marker=dict(color=marker["color"], size=marker["size"]),
                    text=f"Overlaps: {marker['overlaps']}",
                )
            )

        fig.update_layout(
            title=f"Schedule Density [Maximum course overlap in any interval = {max_overlap}]",
            xaxis=dict(
                tickvals=[time_to_minutes(t) for t in times][
                    ::12
                ],  # Every hour
                ticktext=time_labels[::12],
                title="Time",
            ),
            yaxis=dict(
                tickvals=list(range(len(days))),
                ticktext=days,
                title="Day of the Week",
            ),
            showlegend=False,
        )

        fig.show()

    # Plot the schedule with varying marker size based on overlap
    plot_schedule_with_overlap(schedule_df)

    conn.close()


# runs if file has been uploaded
if uploaded_file is not None:
    # saves file to backend
    # save_path = os.path.join("src/", "excelcoursedb.xlsx")
    # with open(save_path, "wb") as f:
    #     f.write(uploaded_file.getbuffer())
    df = pd.read_excel(io=uploaded_file)

    # converts excel to .db file (and saves?)
    conn = sqlite3.connect(database=":memory:")

    table = "schedule"
    df.to_sql(table, conn, if_exists="replace", index=False)
    # Plots Schedule Density

    depts = ["COMP"]

    # button
    if st.button("Schedule Density"):
        plotDensity("coursedb.db", df)

import itertools
import sqlite3
from datetime import datetime

import matplotlib as plt
import matplotlib.colors as mcolors
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from intervaltree import Interval, IntervalTree
from streamlit.runtime.uploaded_file_manager import UploadedFile


def traditionalMeetingPattern(row):
    """
    Convert meeting patterns in a given row to a traditional format.

    This function takes a dictionary representing a row, extracts the "MEETING PATTERN" field,
    and replaces certain abbreviations with more traditional ones. Specifically:

    - "TR" is replaced with "R"
    - "SA" is replaced with "S"
    - "SU" is replaced with "X"

    If the "MEETING PATTERN" field is empty or not present, the function returns an empty string.

    Parameters
    ----------
    row : dict
        A dictionary containing a "MEETING PATTERN" key with its associated value being the pattern to be converted.

    Returns
    -------
    str
        The converted meeting pattern as a string, or an empty string if the input pattern is empty or not present.

    Examples
    --------
    >>> row = {"MEETING PATTERN": "MWF TR"}
    >>> traditionalMeetingPattern(row)
    'MWF R'

    >>> row = {"MEETING PATTERN": "SA SU"}
    >>> traditionalMeetingPattern(row)
    'S X'

    >>> row = {"MEETING PATTERN": ""}
    >>> traditionalMeetingPattern(row)
    ''
    """
    meeting_pattern = row["MEETING PATTERN"]
    if meeting_pattern:
        return (
            meeting_pattern.replace("TR", "R")
            .replace("SA", "S")
            .replace("SU", "X")
        )
    else:
        return ""


def timeToMinutes(t):
    """
    Convert a time object to minutes past midnight.

    Parameters
    ----------
    t : datetime.time
        A datetime.time object representing a specific time.

    Returns
    -------
    int
        The total number of minutes past midnight represented by the given time object `t`.

    Examples
    --------
    >>> import datetime
    >>> time = datetime.time(9, 30)
    >>> timeToMinutes(time)
    570

    >>> time = datetime.time(13, 15)
    >>> timeToMinutes(time)
    795
    """
    return t.hour * 60 + t.minute


def unitClassDuration(row):
    """
    Calculate the duration of a class session in minutes based on start and end times.

    Parameters
    ----------
    row : dict
        A dictionary containing "CLASS START TIME" and "CLASS END TIME" keys with values
        representing the start and end times of the class in format "%H:%M:%S".

    Returns
    -------
    int
        The duration of the class session in minutes, or 0 if either start or end time is missing.

    Notes
    -----
    This function relies on the `timeToMinutes` function to convert time strings to minutes past midnight.

    Examples
    --------
    >>> row = {"CLASS START TIME": "09:00:00", "CLASS END TIME": "10:30:00"}
    >>> unitClassDuration(row)
    90

    >>> row = {"CLASS START TIME": "14:00:00", "CLASS END TIME": "15:45:00"}
    >>> unitClassDuration(row)
    105

    >>> row = {"CLASS START TIME": "", "CLASS END TIME": "12:00:00"}
    >>> unitClassDuration(row)
    0
    """

    start = row["CLASS START TIME"]
    end = row["CLASS END TIME"]

    if not start or not end:
        return 0
    start_time = datetime.strptime(start, "%H:%M:%S")
    end_time = datetime.strptime(end, "%H:%M:%S")
    start_minutes = timeToMinutes(start_time)
    end_minutes = timeToMinutes(end_time)
    total_minutes = end_minutes - start_minutes
    return total_minutes


def instructionalTime(row):
    """
    Calculate the total instructional time based on meeting pattern length and unit class duration.

    Parameters
    ----------
    row : dict
        A dictionary containing a "TRAD MEETING PATTERN" key with a string value representing
        the traditional meeting pattern, and a "UNIT CLASS DURATION" key with an integer value
        representing the duration of the class in minutes.

    Returns
    -------
    int
        The total instructional time calculated as the product of the length of the meeting pattern
        and the unit class duration.

    Examples
    --------
    >>> row = {"TRAD MEETING PATTERN": "MWF", "UNIT CLASS DURATION": 90}
    >>> instructionalTime(row)
    270

    >>> row = {"TRAD MEETING PATTERN": "TTH", "UNIT CLASS DURATION": 105}
    >>> instructionalTime(row)
    210

    >>> row = {"TRAD MEETING PATTERN": "", "UNIT CLASS DURATION": 120}
    >>> instructionalTime(row)
    0
    """
    meeting_pattern = row["TRAD MEETING PATTERN"]
    return len(meeting_pattern) * row["UNIT CLASS DURATION"]


def createIntervalTrees(schedule_df):
    """
    Create interval trees for each day of the week based on schedule data.

    Parameters
    ----------
    schedule_df : pandas.DataFrame
        A DataFrame containing schedule information with columns:
        - "TRAD MEETING PATTERN": Traditional meeting pattern string for each class.
        - "CLASS START TIME": Start time of the class in format "%H:%M:%S".
        - "CLASS END TIME": End time of the class in format "%H:%M:%S".

    Returns
    -------
    dict
        A dictionary where keys are days of the week ("M", "T", "W", "R", "F", "S") and values
        are IntervalTree objects containing class intervals for each day.

    Notes
    -----
    This function relies on the `timeToMinutes` function to convert time strings to minutes past midnight.
    It iterates through the rows of the provided DataFrame to create interval trees based on class schedules.

    Examples
    --------
    >>> import pandas as pd
    >>> schedule_df = pd.DataFrame({
    ...     "TRAD MEETING PATTERN": ["MWF", "TTH", "MWF"],
    ...     "CLASS START TIME": ["09:00:00", "13:00:00", "10:00:00"],
    ...     "CLASS END TIME": ["10:30:00", "14:15:00", "11:30:00"]
    ... })
    >>> createIntervalTrees(schedule_df)
    {
        'M': IntervalTree([Interval(540, 630), Interval(600, 690)]),
        'T': IntervalTree([Interval(780, 855)]),
        'W': IntervalTree([Interval(540, 630), Interval(600, 690)]),
        'R': IntervalTree([Interval(780, 855)]),
        'F': IntervalTree([Interval(540, 630), Interval(600, 690)]),
        'S': IntervalTree([])
    }
    """
    day_trees = {day: IntervalTree() for day in ["M", "T", "W", "R", "F", "S"]}
    for index, row in schedule_df.iterrows():
        pattern = row["TRAD MEETING PATTERN"]
        start = row["CLASS START TIME"]
        end = row["CLASS END TIME"]
        if start == end:
            continue
        start_time = datetime.strptime(start, "%H:%M:%S")
        end_time = datetime.strptime(end, "%H:%M:%S")
        start_minutes = timeToMinutes(start_time)
        end_minutes = timeToMinutes(end_time)
        total_minutes = 0
        for day in pattern:
            interval = Interval(start_minutes, end_minutes)
            try:
                day_trees[day].add(interval)
                total_minutes += end_minutes - start_minutes
            except Exception as e:
                print(f"Error: {e}")
                print(interval, start_time, end_time, pattern)
        if total_minutes != 150:
            print(
                "Checking for duration != 150 minutes (possibly ok): ",
                row["FQ_CLASS_SECTION"],
                row["TRAD MEETING PATTERN"],
                row["CLASS START TIME"],
                row["CLASS END TIME"],
            )
    return day_trees


def scheduleReport(dbPath, df) -> pd.DataFrame:
    """
    Generate a schedule report from a DataFrame and store it in a SQLite database.

    Parameters
    ----------
    dbPath : str
        The file path to the SQLite database where the schedule report will be stored or replaced.
    df : pandas.DataFrame
        The DataFrame containing schedule information to be stored in the database.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the schedule report with the following columns:
        - 'SUBJECT'
        - 'CATALOG NUMBER'
        - 'FQ_CATALOG_NUMBER': Combined SUBJECT and CATALOG NUMBER.
        - 'FQ_CLASS_SECTION': Combined CATALOG NUMBER and SECTION.
        - 'CLASS TITLE'
        - 'INSTRUCTOR'
        - 'ENROLL TOTAL'
        - 'MEETING PATTERN'
        - 'CLASS START TIME'
        - 'CLASS END TIME'
        - 'FACILITY'
        - 'COMBINED_ID': Combined string of INSTRUCTOR, FACILITY, MEETING PATTERN, CLASS START TIME, and CLASS END TIME.
        - 'TRAD MEETING PATTERN': Traditional meeting pattern converted using `traditionalMeetingPattern` function.
        - 'UNIT CLASS DURATION': Duration of each class unit in minutes using `unitClassDuration` function.
        - 'INSTRUCTIONAL TIME': Total instructional time calculated using `instructionalTime` function.

    Notes
    -----
    This function relies on several helper functions (`traditionalMeetingPattern`, `unitClassDuration`, `instructionalTime`)
    to process and transform schedule data.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     "SUBJECT": ["COMP", "COMP"],
    ...     "CATALOG NUMBER": [101, 102],
    ...     "SECTION": ["001", "002"],
    ...     "CLASS TITLE": ["Introduction to Programming", "Data Structures"],
    ...     "INSTRUCTOR": ["Alan Turing", "Grace Hopper"],
    ...     "ENROLL TOTAL": [30, 25],
    ...     "MEETING PATTERN": ["MWF", "TTH"],
    ...     "CLASS START TIME": ["09:00:00", "13:00:00"],
    ...     "CLASS END TIME": ["10:30:00", "14:45:00"],
    ...     "FACILITY": ["Main Building", "Science Building"]
    ... })
    >>> dbPath = "schedule_database.db"
    >>> scheduleReport(dbPath, df)
    [Output DataFrame]
    """

    conn = sqlite3.connect(dbPath)
    table = "schedule"
    df.to_sql(table, conn, if_exists="replace", index=False)

    depts = ["COMP"]

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

    df = pd.read_sql_query(query, conn)
    conn.close()

    pd.options.display.max_rows = 999

    dfSr = df.drop_duplicates(subset=["FQ_CLASS_SECTION"])
    dfSr = dfSr.copy()

    unknown_instructor_name = "Turing, Alan"
    dfSr["INSTRUCTOR"].fillna(unknown_instructor_name)

    unknown_combined_id = "(Doyle Center, No Start Time, No End Time)"
    dfSr["COMBINED_ID"].fillna(unknown_combined_id)

    dfSr["TRAD MEETING PATTERN"] = dfSr.apply(
        traditionalMeetingPattern, axis=1
    )
    dfSr["CLASS START TIME"] = df["CLASS START TIME"].str.split(" ").str[1]
    dfSr["CLASS END TIME"] = df["CLASS END TIME"].str.split(" ").str[1]
    dfSr["COMBINED_ID"] = df["COMBINED_ID"].str.replace("1900-01-01", "")

    dfSr["UNIT CLASS DURATION"] = dfSr.apply(unitClassDuration, axis=1)
    dfSr["INSTRUCTIONAL TIME"] = dfSr.apply(instructionalTime, axis=1)

    group = dfSr[dfSr["ENROLL TOTAL"] >= 0]
    dfSr = group

    return dfSr


def plotDensity(dbPath, df):
    """
    Generate a density plot for schedule data stored in a SQLite database.

    Parameters
    ----------
    dbPath : str
        The file path to the SQLite database containing schedule data.
    df : pandas.DataFrame
        The DataFrame containing schedule information to generate the plot.

    Returns
    -------
    None

    Notes
    -----
    This function relies on the `scheduleReport` function to generate a DataFrame with schedule information
    stored in an in-memory SQLite database.
    It further uses the `plotScheduleWithOverlap` function to plot the density of schedules with overlaps.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     "SUBJECT": ["COMP", "COMP"],
    ...     "CATALOG NUMBER": [101, 102],
    ...     "SECTION": ["001", "002"],
    ...     "CLASS TITLE": ["Introduction to Programming", "Data Structures"],
    ...     "INSTRUCTOR": ["Alan Turing", "Grace Hopper"],
    ...     "ENROLL TOTAL": [30, 25],
    ...     "MEETING PATTERN": ["MWF", "TTH"],
    ...     "CLASS START TIME": ["09:00:00", "13:00:00"],
    ...     "CLASS END TIME": ["10:30:00", "14:45:00"],
    ...     "FACILITY": ["Main Building", "Science Building"]
    ... })
    >>> dbPath = ":memory:"
    >>> plotDensity(dbPath, df)
    [Generates a density plot]
    """

    scheduleDf: pd.DataFrame = scheduleReport(":memory:", df)
    plotScheduleWithOverlap(scheduleDf)


def plotScheduleWithOverlap(scheduleDf, overlap_threshold=2):
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
    This function creates a Plotly figure to visualize schedule overlaps for each day of the week
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

    days = ["M", "T", "W", "R", "F", "S"]
    days.reverse()  # For more natural appearance on the chart.
    times = [
        datetime(2023, 1, 1, hour, minute)
        for hour in range(8, 19)
        for minute in range(0, 60, 5)
    ]  # todo remove hard-coding of year/1/1 (safe though)
    time_labels = [t.strftime("%H:%M") for t in times]
    day_trees = createIntervalTrees(scheduleDf)

    max_overlap = 0
    markers = []

    for day_index, day in enumerate(days):
        for t in times:
            minutes = timeToMinutes(t)
            overlaps = day_trees[day][minutes]
            color = "green"
            if len(overlaps) >= overlap_threshold:
                color = "red"
            elif overlaps:
                color = "orange"
            if len(overlaps) > max_overlap:
                max_overlap = len(overlaps)
            size = 5 + 4 * len(overlaps)

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
            tickvals=[timeToMinutes(t) for t in times][::12],  # Every hour
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


def weightedEnrollment(row):
    """
    Calculate weighted enrollment based on catalog number ranges.

    Parameters
    ----------
    row : dict
        A dictionary containing schedule information with keys:
        - 'CATALOG NUMBER': Catalog number of the course.
        - 'ENROLL TOTAL': Total enrollment for the course.

    Returns
    -------
    float
        The weighted enrollment calculated based on the catalog number range:
        - Courses with catalog numbers between '300' and '399' (inclusive) are weighted by 1.0.
        - Courses with catalog numbers '400' and above are weighted by 5/3 (approximately 1.67).
        - All other courses retain their original enrollment value.

    Examples
    --------
    >>> row1 = {"CATALOG NUMBER": "350", "ENROLL TOTAL": 50}
    >>> weightedEnrollment(row1)
    50.0

    >>> row2 = {"CATALOG NUMBER": "410", "ENROLL TOTAL": 40}
    >>> weightedEnrollment(row2)
    66.66666666666667

    >>> row3 = {"CATALOG NUMBER": "200", "ENROLL TOTAL": 30}
    >>> weightedEnrollment(row3)
    30
    """

    if "300" <= row["CATALOG NUMBER"] < "400":
        return row["ENROLL TOTAL"] * 1.0
    elif "400" <= row["CATALOG NUMBER"]:
        return row["ENROLL TOTAL"] * 5 / 3
    else:
        return row["ENROLL TOTAL"]


def schWeighted(row):
    """
    Calculate the weighted schedule based on catalog number and weighted enrollment total.

    Parameters
    ----------
    row : dict
        A dictionary containing schedule information with keys:
        - 'CATALOG NUMBER': Catalog number of the course.
        - 'WEIGHTED ENROLL TOTAL': Weighted enrollment total for the course.

    Returns
    -------
    int
        The weighted schedule calculated as the product of credits and weighted enrollment total.

    Notes
    -----
    This function assumes a default credit value of 3, except for courses with catalog number '395' which are assigned 1 credit.

    Examples
    --------
    >>> row1 = {"CATALOG NUMBER": "395", "WEIGHTED ENROLL TOTAL": 50}
    >>> schWeighted(row1)
    50

    >>> row2 = {"CATALOG NUMBER": "350", "WEIGHTED ENROLL TOTAL": 40}
    >>> schWeighted(row2)
    120

    >>> row3 = {"CATALOG NUMBER": "410", "WEIGHTED ENROLL TOTAL": 30}
    >>> schWeighted(row3)
    90
    """
    credits = 3
    if row["CATALOG NUMBER"] in set(["395"]):
        credits = 1
    return int(credits * row["WEIGHTED ENROLL TOTAL"])


def enrollmentHealth(df):
    """
    Generate an enrollment health report based on schedule data.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing schedule information.

    Returns
    -------
    None

    Notes
    -----
    This function performs the following steps:
    1. Generates a schedule report using `scheduleReport` function and stores it in an in-memory SQLite database.
    2. Calculates weighted enrollments and weighted schedule totals using `weightedEnrollment` and `schWeighted` functions, respectively.
    3. Groups the data by 'COMBINED_ID' and sorts the report based on weighted enrollments.
    4. Displays an interactive report using Streamlit with information such as class section, title, instructor, enroll total, meeting pattern, start time, and end time.
    5. Colors the displayed information based on the total weighted enrollments:
    - Red for totals less than 12.
    - Green for totals between 12 and 32.
    - Blue for totals greater than or equal to 32.

    Examples
    --------
    >>> import pandas as pd
    >>> schedule_df = pd.DataFrame({
    ...     "SUBJECT": ["COMP", "COMP", "MATH"],
    ...     "CATALOG NUMBER": [101, 395, 201],
    ...     "SECTION": ["001", "002", "001"],
    ...     "CLASS TITLE": ["Introduction to Programming", "Data Structures", "Calculus"],
    ...     "INSTRUCTOR": ["Alan Turing", "Grace Hopper", "Ada Lovelace"],
    ...     "ENROLL TOTAL": [30, 25, 20],
    ...     "MEETING PATTERN": ["MWF", "TTH", "MWF"],
    ...     "CLASS START TIME": ["09:00:00", "13:00:00", "10:00:00"],
    ...     "CLASS END TIME": ["10:30:00", "14:45:00", "11:30:00"],
    ...     "FACILITY": ["Main Building", "Science Building", "Math Building"]
    ... })
    >>> enrollmentHealth(schedule_df)
    [Generates an interactive enrollment health report using Streamlit]
    """

    dfEh = scheduleReport(":memory:", df)
    dfEh["WEIGHTED ENROLL TOTAL"] = dfEh.apply(weightedEnrollment, axis=1)
    dfEh["WEIGHTED SCH TOTAL"] = dfEh.apply(schWeighted, axis=1)
    combinedGroups = dfEh.groupby("COMBINED_ID")
    report = []
    for name, group in combinedGroups:
        report.append((group["WEIGHTED ENROLL TOTAL"].sum(), name, group))
    report.sort(reverse=False)
    FILTER_FIELDS = [
        "FQ_CLASS_SECTION",
        "CLASS TITLE",
        "INSTRUCTOR",
        "ENROLL TOTAL",
        "MEETING PATTERN",
        "CLASS START TIME",
        "CLASS END TIME",
    ]
    st.title("Enrollment Health Report")

    for group_sum, name, group in report:
        st.markdown(f"<h3>{name}</h3>", unsafe_allow_html=True)

        if group_sum < 12:
            group_color = "red"
        elif group_sum < 32:
            group_color = "green"
        else:
            group_color = "blue"

        st.markdown(
            f"<p style='color:{group_color}'>Weighted Enrollments = {int(group_sum)}</p>",
            unsafe_allow_html=True,
        )

        inner_group = group[FILTER_FIELDS]
        st.dataframe(inner_group)

        st.markdown("---")


def instructorAssignments(df):
    """
    Generate instructor assignments report based on schedule data.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing schedule information.

    Returns
    -------
    dict
        A dictionary mapping each instructor's name to the number of assignments.

    Notes
    -----
    This function performs the following steps:
    1. Groups the input DataFrame `df` by 'INSTRUCTOR'.
    2. Iterates over each group and displays instructor names as headers using Streamlit.
    3. For each instructor, retrieves and displays unique courses grouped by 'COMBINED_ID'.
    4. Counts and assigns the number of unique assignments (didactic courses) for each instructor.
    5. Returns a dictionary where keys are instructor names and values are the number of assignments.

    Examples
    --------
    >>> import pandas as pd
    >>> schedule_df = pd.DataFrame({
    ...     "SUBJECT": ["COMP", "COMP", "MATH"],
    ...     "CATALOG NUMBER": [101, 395, 201],
    ...     "SECTION": ["001", "002", "001"],
    ...     "CLASS TITLE": ["Introduction to Programming", "Data Structures", "Calculus"],
    ...     "INSTRUCTOR": ["Alan Turing", "Grace Hopper", "Ada Lovelace"],
    ...     "ENROLL TOTAL": [30, 25, 20],
    ...     "MEETING PATTERN": ["MWF", "TTH", "MWF"],
    ...     "CLASS START TIME": ["09:00:00", "13:00:00", "10:00:00"],
    ...     "CLASS END TIME": ["10:30:00", "14:45:00", "11:30:00"],
    ...     "FACILITY": ["Main Building", "Science Building", "Math Building"]
    ... })
    >>> instructorAssignments(schedule_df)
    {'Alan Turing': 1, 'Grace Hopper': 1, 'Ada Lovelace': 1}
    """

    combinedGroups = df.groupby("INSTRUCTOR")

    assignments = {}

    for name, group in combinedGroups:
        st.markdown(f"<h3>{name}</h3><br/>", unsafe_allow_html=True)
        inner_group = group[
            ["FQ_CLASS_SECTION", "CLASS TITLE", "ENROLL TOTAL"]
        ]

        uniqueCoursesForInstr = group.groupby("COMBINED_ID", dropna=False)
        didacticCourseCount = itertools.count(start=1)
        for inner_name, inner_group in uniqueCoursesForInstr:
            st.write(f"Assignment {next(didacticCourseCount)}")
            st.dataframe(
                inner_group[
                    ["FQ_CLASS_SECTION", "CLASS TITLE", "ENROLL TOTAL"]
                ]
            )

        assignments[name] = next(didacticCourseCount) - 1
        st.markdown("<hr/>", unsafe_allow_html=True)
    return assignments


def plotAssignmentsPerFaculty(assignments):
    """
    Plot the number of courses assigned to each instructor.

    Parameters
    ----------
    assignments : dict
        A dictionary mapping instructor names to the number of courses assigned.

    Returns
    -------
    None

    Notes
    -----
    This function generates a horizontal bar plot using Plotly to visualize the distribution of course assignments
    among instructors based on the input dictionary `assignments`.

    Examples
    --------
    >>> assignments = {'Alan Turing': 1, 'Grace Hopper': 1, 'Ada Lovelace': 1}
    >>> plotAssignmentsPerFaculty(assignments)
    [Generates a horizontal bar plot displaying the number of courses per instructor]
    """

    assignmentsDf = pd.DataFrame.from_dict(
        assignments, orient="index", columns=["Number of Courses"]
    )
    assignmentsDf.reset_index(inplace=True)
    assignmentsDf.rename(columns={"index": "Instructor Name"}, inplace=True)
    assignmentsDf.sort_values(
        by=["Instructor Name"], ascending=[False], inplace=True
    )

    fig = go.Figure(
        go.Bar(
            y=assignmentsDf["Instructor Name"],
            x=assignmentsDf["Number of Courses"],
            orientation="h",
        )
    )

    fig.update_layout(
        title="Number of Courses per Instructor",
        xaxis_title="Number of Courses",
        yaxis_title="Instructor Name",
    )

    st.plotly_chart(fig)


def teachingDistr(df):
    """
    Generate a distribution plot of total weighted enrollment per instructor.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing schedule information.

    Returns
    -------
    None

    Notes
    -----
    This function performs the following steps:
    1. Generates a schedule report using `scheduleReport` function and stores it in an in-memory SQLite database.
    2. Calculates weighted enrollments for each course using the `weightedEnrollment` function.
    3. Groups the data by 'INSTRUCTOR' and computes the total weighted enrollment per instructor.
    4. Sorts the data for better visualization by descending total weighted enrollment.
    5. Creates a horizontal bar plot using Plotly to visualize the distribution of total weighted enrollments among instructors.

    Examples
    --------
    >>> import pandas as pd
    >>> schedule_df = pd.DataFrame({
    ...     "SUBJECT": ["COMP", "COMP", "MATH"],
    ...     "CATALOG NUMBER": [101, 395, 201],
    ...     "SECTION": ["001", "002", "001"],
    ...     "CLASS TITLE": ["Introduction to Programming", "Data Structures", "Calculus"],
    ...     "INSTRUCTOR": ["Alan Turing", "Grace Hopper", "Ada Lovelace"],
    ...     "ENROLL TOTAL": [30, 25, 20],
    ...     "MEETING PATTERN": ["MWF", "TTH", "MWF"],
    ...     "CLASS START TIME": ["09:00:00", "13:00:00", "10:00:00"],
    ...     "CLASS END TIME": ["10:30:00", "14:45:00", "11:30:00"],
    ...     "FACILITY": ["Main Building", "Science Building", "Math Building"]
    ... })
    >>> teachingDistr(schedule_df)
    [Generates a horizontal bar plot displaying total weighted enrollment per instructor]
    """

    dfTd = scheduleReport(":memory:", df)
    dfTd["WEIGHTED ENROLL TOTAL"] = dfTd.apply(weightedEnrollment, axis=1)
    totalEnrollment = (
        dfTd.groupby("INSTRUCTOR")["WEIGHTED ENROLL TOTAL"].sum().reset_index()
    )
    # Sort data for better visualization (optional)
    totalEnrollment = totalEnrollment.sort_values(
        by="WEIGHTED ENROLL TOTAL", ascending=False
    )
    fig = go.Figure(
        go.Bar(
            x=totalEnrollment["WEIGHTED ENROLL TOTAL"],
            y=totalEnrollment["INSTRUCTOR"],
            orientation="h",
            marker_color="teal",
        )
    )
    fig.update_layout(
        title="Total Weighted Enrollment per Instructor",
        xaxis_title="Total Weighted Enrollment (courses, not SCH)",
        yaxis_title="Instructor",
    )
    st.plotly_chart(fig)


def plotEnrollmentsByCourseLevel(df):
    """
    Plot enrollment distribution for courses grouped by catalog number levels.

    Parameters
    ----------
    df : pandas.DataFrame
        A DataFrame containing schedule information.

    Returns
    -------
    None

    Notes
    -----
    This function iterates over specified course level ranges and performs the following steps for each range:
    1. Filters the input DataFrame `df` to select courses within the current level range.
    2. Groups the filtered data by 'FQ_CATALOG_NUMBER' and computes the total weighted enrollment for each course.
    3. Sorts the grouped data by descending total weighted enrollment.
    4. Creates a horizontal bar plot using Plotly to visualize the distribution of enrollment among courses within the current level range.
    5. Adds a dashed red line representing the average enrollment across all courses within the range.

    Examples
    --------
    >>> import pandas as pd
    >>> schedule_df = pd.DataFrame({
    ...     "SUBJECT": ["COMP", "COMP", "MATH"],
    ...     "CATALOG NUMBER": [101, 395, 201],
    ...     "SECTION": ["001", "002", "001"],
    ...     "CLASS TITLE": ["Introduction to Programming", "Data Structures", "Calculus"],
    ...     "INSTRUCTOR": ["Alan Turing", "Grace Hopper", "Ada Lovelace"],
    ...     "ENROLL TOTAL": [30, 25, 20],
    ...     "MEETING PATTERN": ["MWF", "TTH", "MWF"],
    ...     "CLASS START TIME": ["09:00:00", "13:00:00", "10:00:00"],
    ...     "CLASS END TIME": ["10:30:00", "14:45:00", "11:30:00"],
    ...     "FACILITY": ["Main Building", "Science Building", "Math Building"]
    ... })
    >>> plotEnrollmentsByCourseLevel(schedule_df)
    [Generates bar plots displaying enrollment distribution for different course levels]
    """

    for level in range(0, 500, 100):
        this_level = str(level + 100)
        df_level = df[
            (df["CATALOG NUMBER"] >= this_level)
            & (df["CATALOG NUMBER"] < str(level + 200))
        ]

        if len(df_level) == 0:
            break

        courseEnrollment = (
            df_level.groupby("FQ_CATALOG_NUMBER")["WEIGHTED ENROLL TOTAL"]
            .sum()
            .reset_index()
        )
        courseEnrollment = courseEnrollment.sort_values(
            by="WEIGHTED ENROLL TOTAL", ascending=False
        )

        fig = go.Figure()

        # fix colors
        norm = mcolors.Normalize(
            vmin=courseEnrollment["WEIGHTED ENROLL TOTAL"].min(),
            vmax=courseEnrollment["WEIGHTED ENROLL TOTAL"].max(),
        )
        colors = [
            plt.cm.viridis(norm(val))
            for val in courseEnrollment["WEIGHTED ENROLL TOTAL"]
        ]

        fig.add_trace(
            go.Bar(
                x=courseEnrollment["WEIGHTED ENROLL TOTAL"],
                y=courseEnrollment["FQ_CATALOG_NUMBER"],
                orientation="h",
                marker=dict(color=colors),
            )
        )

        averageEnrollment = courseEnrollment["WEIGHTED ENROLL TOTAL"].mean()
        fig.add_shape(
            type="line",
            x0=averageEnrollment,
            y0=courseEnrollment["FQ_CATALOG_NUMBER"].iloc[0],
            x1=averageEnrollment,
            y1=courseEnrollment["FQ_CATALOG_NUMBER"].iloc[-1],
            line=dict(color="red", width=2, dash="dash"),
        )

        fig.update_layout(
            title=f"Enrollment at {this_level}-level",
            xaxis_title="Enrollment",
            yaxis_title="Course",
            legend_title="Legend",
        )

        st.plotly_chart(fig)


def main() -> None:
    st.title("Excel File Uploader")
    uploaded_file: UploadedFile = st.file_uploader(
        "Choose an Excel file", type=["xlsx"]
    )

    if uploaded_file is not None:
        df = pd.read_excel(io=uploaded_file)

        conn = sqlite3.connect(database=":memory:")

        table = "schedule"
        df.to_sql(table, conn, if_exists="replace", index=False)

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

        if st.button("Show Course Schedule"):
            resultDf: pd.DataFrame = scheduleReport(":memory:", df)
            courseScheduleDf: pd.DataFrame = resultDf[FILTER_FIELDS]
            st.dataframe(courseScheduleDf)

        if st.button("Schedule Density"):
            plotDensity(":memory:", df)

        if st.button("Enrollment Health"):
            enrollmentHealth(df)

        if st.button("Instructor Assignments"):
            resultDf = scheduleReport(":memory:", df)
            instructorAssignmentsDf: pd.DataFrame = resultDf[FILTER_FIELDS]
            instructorAssignments(instructorAssignmentsDf)

        if st.button("Number of Assignments per Faculty"):
            resultDf: pd.DataFrame = scheduleReport(":memory:", df)
            numAssignmentsDf: pd.DataFrame = resultDf[FILTER_FIELDS]
            assignments = instructorAssignments(numAssignmentsDf)
            plotAssignmentsPerFaculty(assignments)

        if st.button("Number of Assignments per Faculty by Course Number"):
            resultDf: pd.DataFrame = scheduleReport(":memory:", df)
            combinedGroups = resultDf.groupby("FQ_CATALOG_NUMBER")
            for name, group in combinedGroups:
                st.markdown(f"### {name}")
                st.write(group[FILTER_FIELDS])
                st.markdown("---")

        if st.button("Teaching Distribution by Weighted Enrollment"):
            teachingDistr(df)

        # work on graph coloring
        if st.button("Enrollments by Course Level"):
            resultDf: pd.DataFrame = scheduleReport(":memory:", df)
            resultDf["WEIGHTED ENROLL TOTAL"] = resultDf.apply(
                weightedEnrollment, axis=1
            )
            plotEnrollmentsByCourseLevel(resultDf)


if __name__ == "__main__":
    main()

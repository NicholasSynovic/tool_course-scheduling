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
    return t.hour * 60 + t.minute


def unitClassDuration(row):
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
    meeting_pattern = row["TRAD MEETING PATTERN"]
    return len(meeting_pattern) * row["UNIT CLASS DURATION"]


def createIntervalTrees(schedule_df):
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
    scheduleDf: pd.DataFrame = scheduleReport(":memory:", df)
    plotScheduleWithOverlap(scheduleDf)


def plotScheduleWithOverlap(scheduleDf, overlap_threshold=2):
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
    if "300" <= row["CATALOG NUMBER"] < "400":
        return row["ENROLL TOTAL"] * 1.0
    elif "400" <= row["CATALOG NUMBER"]:
        return row["ENROLL TOTAL"] * 5 / 3
    else:
        return row["ENROLL TOTAL"]


def schWeighted(row):
    credits = 3
    if row["CATALOG NUMBER"] in set(["395"]):
        credits = 1
    return int(credits * row["WEIGHTED ENROLL TOTAL"])


def enrollmentHealth(df):
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

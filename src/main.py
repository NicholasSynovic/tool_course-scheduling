from sqlite3 import Connection

import streamlit
from pandas import DataFrame
from plotly.graph_objects import Figure
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.uploaded_file_manager import UploadedFile

from src.analytics.assignmentsPerFaculty import AssignmentsPerFaculty
from src.analytics.courseEnrollmentHealth import CourseEnrollmentHealth
from src.analytics.courseSchedule import CourseSchedule
from src.analytics.enrollmentByCourseLevel import EnrollmentByCourseLevel
from src.analytics.instructorAssignments import InstructorAssignments
from src.analytics.inTroubleCourses import InTroubleCourses
from src.analytics.onlineCourseSchedule import OnlineCourseSchedule
from src.analytics.parameterizedCourseSchedule import FilterCourseSchedule
from src.analytics.scheduleDensity import ScheduleDensity
from src.analytics.showCoursesByNumber import ShowCoursesByNumber
from src.analytics.teachingDistributionByWeightedEnrollment import (
    TeachingDistributionByWeightedEnrollment,
)
from src.analytics.zeroEnrollment import zeroEnrollment
from src.excel2db import readExcelToDB
from src.utils import initialState, resetState


def main() -> None:
    """
    Main function to run the CS Dept. Course Scheduler Utility.

    This function initializes the Streamlit session state, sets up the UI for
    uploading an Excel file, processes the file to populate the database, and
    provides various buttons to execute different analytics on the course
    schedule data.

    :return: None
    :rtype: None
    """
    print(AssignmentsPerFaculty)

    initialState()

    streamlit.title(body="CS Dept. Course Scheduler Utility")

    excelFile: UploadedFile = streamlit.file_uploader(
        label="Upload a Locus Course Schedule Export (.xlsx) file",
        type=["xlsx"],
        accept_multiple_files=False,
    )

    if excelFile is not None:
        conn: Connection = readExcelToDB(uf=excelFile)
        streamlit.session_state["dbConn"] = conn
        streamlit.session_state["showAnalyticButtons"] = True
    else:
        resetState()

    if streamlit.session_state["showAnalyticButtons"]:
        column1: DeltaGenerator
        column2: DeltaGenerator
        column1, column2 = streamlit.columns(
            spec=2,
            gap="small",
            vertical_alignment="center",
        )

        with column1:
            streamlit.button(
                label="Show Course Schedule",
                use_container_width=True,
                on_click=CourseSchedule(
                    conn=streamlit.session_state["dbConn"]
                ).run,
            )
            streamlit.button(
                label="Online Only Courses",
                use_container_width=True,
                on_click=OnlineCourseSchedule(
                    conn=streamlit.session_state["dbConn"]
                ).run,
            )
            streamlit.button(
                label="Schedule Density",
                use_container_width=True,
                on_click=ScheduleDensity(
                    conn=streamlit.session_state["dbConn"]
                ).run,
            )
            # TODO: Implement viz for this
            streamlit.button(
                label="Course Enrollment Health",
                use_container_width=True,
                on_click=CourseEnrollmentHealth(
                    conn=streamlit.session_state["dbConn"]
                ).run,
            )
            streamlit.button(
                label="Instructor Assignments",
                use_container_width=True,
                on_click=InstructorAssignments(
                    conn=streamlit.session_state["dbConn"]
                ).run,
            )
            streamlit.button(
                label="Courses with No Enrollments",
                use_container_width=True,
                on_click=zeroEnrollment(
                    conn=streamlit.session_state["dbConn"]
                ).run,
            )

        with column2:
            streamlit.button(
                label="Number of Assignments Per Faculty Member",
                use_container_width=True,
                on_click=AssignmentsPerFaculty(
                    conn=streamlit.session_state["dbConn"],
                ).run,
            )
            streamlit.button(
                label="Course by Number",
                use_container_width=True,
                on_click=ShowCoursesByNumber(
                    conn=streamlit.session_state["dbConn"],
                ).run,
            )
            streamlit.button(
                label="Teaching Distribution by Weighted Enrollment",
                use_container_width=True,
                on_click=TeachingDistributionByWeightedEnrollment(
                    conn=streamlit.session_state["dbConn"],
                ).run,
            )
            streamlit.button(
                label="Enrollments by Course Level",
                use_container_width=True,
                on_click=EnrollmentByCourseLevel(
                    conn=streamlit.session_state["dbConn"],
                ).run,
            )
            streamlit.button(
                label="In Trouble Courses",
                use_container_width=True,
                on_click=InTroubleCourses(
                    conn=streamlit.session_state["dbConn"],
                ).run,
            )
            streamlit.button(
                label="Filter Course Schedule",
                use_container_width=True,
                on_click=lambda: streamlit.session_state.update(
                    {"current_page": "filter"}
                ),
            )

        streamlit.divider()

        if streamlit.session_state["analyticTitle"] is not None:
            streamlit.markdown(
                body=f"## {streamlit.session_state['analyticTitle']}"
            )

        if streamlit.session_state["analyticSubtitle"] is not None:
            streamlit.markdown(
                body=f"> {streamlit.session_state['analyticSubtitle']}"
            )

        try:
            fig: Figure
            for fig in streamlit.session_state["figList"]:

                if streamlit.session_state["figListTitles"] is not None:
                    streamlit.markdown(
                        body=f"### \
                        {streamlit.session_state['figListTitles'].pop(0)}"
                    )

                streamlit.plotly_chart(
                    figure_or_data=fig,
                    use_container_width=True,
                )
        except TypeError:
            pass

        try:
            df: DataFrame
            for df in streamlit.session_state["dfList"]:

                if streamlit.session_state["dfListTitles"] is not None:
                    streamlit.markdown(
                        body=f"##### \
                        {streamlit.session_state['dfListTitles'].pop(0)}"
                    )

                if streamlit.session_state["dfListSubtitles"] is not None:
                    streamlit.markdown(
                        body=f"> {streamlit.session_state['dfListSubtitles'].pop(0)}"  # noqa: E501
                    )

                streamlit.dataframe(
                    data=df,
                    use_container_width=True,
                )
        except TypeError:
            pass
    if streamlit.session_state.get("current_page") == "filter":
        if "dbConn" in streamlit.session_state:
            FilterCourseSchedule(conn=streamlit.session_state["dbConn"]).run()
        else:
            streamlit.error("Please upload a file to continue.")


if __name__ == "__main__":
    main()

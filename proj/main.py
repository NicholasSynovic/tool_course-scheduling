from sqlite3 import Connection

import streamlit
from pandas import DataFrame
from streamlit.delta_generator import DeltaGenerator
from streamlit.runtime.uploaded_file_manager import UploadedFile

from proj.analytics.scheduleDensity import ScheduleDensity
from proj.excel2db import readExcelToDB


def initalState() -> None:
    if "dbConn" not in streamlit.session_state:
        streamlit.session_state["dbConn"] = None

    if "showAnalyticButtons" not in streamlit.session_state:
        streamlit.session_state["showAnalyticButtons"] = False


def main() -> None:
    initalState()

    streamlit.title(body="Excel File Uploader")

    excelFile: UploadedFile = streamlit.file_uploader(
        label="Choose an Excel file",
        type=["xlsx"],
    )

    if excelFile is not None:
        conn: Connection = readExcelToDB(uf=excelFile)
        streamlit.session_state["dbConn"] = conn
        streamlit.session_state["showAnalyticButtons"] = True
    else:
        streamlit.session_state["dbConn"] = None
        streamlit.session_state["showAnalyticButtons"] = False

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
                help="Hello world",
                use_container_width=True,
            )
            streamlit.button(
                label="Online Only Courses",
                help="Hello world",
                use_container_width=True,
            )
            streamlit.button(
                label="Schedule Density",
                help="Hello world",
                use_container_width=True,
                on_click=ScheduleDensity(
                    conn=streamlit.session_state["dbConn"]
                ).run,
            )
            streamlit.button(
                label="Course Enrollment Health",
                help="Hello world",
                use_container_width=True,
            )
            streamlit.button(
                label="Instructor Assignments",
                help="Hello world",
                use_container_width=True,
            )

        with column2:
            streamlit.button(
                label="Number of Assignments Per Faculty",
                help="Hello world",
                use_container_width=True,
            )
            streamlit.button(
                label="Course by Number",
                help="Hello world",
                use_container_width=True,
            )
            streamlit.button(
                label="Teaching Distribution by Weighted Enrollment",
                help="Hello world",
                use_container_width=True,
            )
            streamlit.button(
                label="Enrollments by Course Level",
                help="Hello world",
                use_container_width=True,
            )
            streamlit.button(
                label="In Trouble Courses",
                help="Hello world",
                use_container_width=True,
            )


if __name__ == "__main__":
    main()

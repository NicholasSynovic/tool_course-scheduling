import sqlite3

import pandas as pd
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

st.title("Excel File Uploader")

uploaded_file: UploadedFile = st.file_uploader(
    "Choose an Excel file", type=["xlsx"]
)

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

    print(df)

    conn.close()

    st.markdown("Hello world")

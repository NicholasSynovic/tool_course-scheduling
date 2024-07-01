import streamlit as st
import pandas as pd
import os

st.title("Excel File Uploader")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

#confirms file has been uploaded
if uploaded_file is not None:
    st.write(":sob:")
    save_path = os.path.join("src/", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
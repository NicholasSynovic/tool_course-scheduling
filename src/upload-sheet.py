import streamlit as st
import pandas as pd

st.title("Excel File Uploader")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

#confirms file has been uploaded
if uploaded_file is not None:
    st.write(":sob:")
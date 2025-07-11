import pandas as pd
import streamlit as st

from cs.analytics.courseSchedule import CourseSchedule


class FilterCourseSchedule(CourseSchedule):
    """
    A class to provide an interactive UI for filtering and displaying
    the course schedule based on various criteria.
    """

    def __init__(self, conn):
        super().__init__(conn)
        self.filters = {}

    def run(self):
        """
        Run the filtering UI and display the filtered course schedule.
        """
        st.title("Filter Course Schedule")

        # Generate dropdowns and input bars for filtering
        self.generate_filters()

        if st.button("Search"):
            df = self.apply_filters()
            self.display_dataframe(df)
            st.session_state["filtered_df"] = df

    def generate_filters(self):
        """
        Generate dropdowns and input bars for filtering the DataFrame.
        """
        df = self.compute()

        for column in df.columns:
            if column in ["COMBINED ID", "INSTRUCTIONAL TIME", "CATALOG NUMBER"]:
                continue  # Skip the filters for these columns

            elif pd.api.types.is_numeric_dtype(df[column]):
                min_val = df[column].min()
                max_val = df[column].max()
                if min_val != max_val:  # Ensure valid range for slider
                    self.filters[column] = st.slider(
                        f"Filter by {column}",
                        min_val,
                        max_val,
                        value=st.session_state.get(
                            f"filter_{column}", (min_val, max_val)
                        ),
                    )
                    st.session_state[f"filter_{column}"] = self.filters[column]
                else:
                    st.write(
                        f"Column {column} has the same min and max value: {min_val}. Slider is not applicable."
                    )
            else:
                unique_values = df[column].unique().tolist()
                self.filters[column] = st.multiselect(
                    f"Filter by {column}",
                    unique_values,
                    default=st.session_state.get(f"filter_{column}", []),
                )
                st.session_state[f"filter_{column}"] = self.filters[column]

    def apply_filters(self):
        """
        Apply the selected filters to the DataFrame.
        """
        df = self.compute()

        for column, filter_value in self.filters.items():
            if isinstance(filter_value, tuple):  # Slider filter
                df = df[
                    (df[column] >= filter_value[0]) & (df[column] <= filter_value[1])
                ]
            elif isinstance(filter_value, list) and filter_value:  # Multiselect filter
                df = df[df[column].isin(filter_value)]

        return df

    def display_dataframe(self, df):
        """
        Display the filtered DataFrame in Streamlit.
        """
        st.dataframe(df)

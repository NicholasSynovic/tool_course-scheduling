from datetime import datetime
from typing import List

import streamlit

SESSION_STATE_KEYS: List[str] = [
    "dbConn",
    "showAnalyticButtons",
    "analyticTitle",
    "analyticSubtitle",
    "dfList",
    "dfListTitles",
    "dfListSubtitles",
    "figList",
    "figListTitles",
]


def datetimeToMinutes(dt: datetime) -> int:
    """
    Convert a datetime object to the total number of minutes since midnight.

    This function takes a datetime object and converts it into the total
    number of minutes since midnight.

    :param dt: The datetime object to be converted.
    :type dt: datetime
    :return: The total number of minutes since midnight.
    :rtype: int
    """
    return dt.hour * 60 + dt.minute


def initialState() -> None:
    """
    Initialize the session state keys to None if they do not exist.

    This function checks if the keys defined in SESSION_STATE_KEYS exist in
    the Streamlit session state. If they do not exist, it initializes them to
    None.

    :return: None
    :rtype: None
    """
    key: str
    for key in SESSION_STATE_KEYS:
        if key not in streamlit.session_state:
            streamlit.session_state[key] = None


def resetState() -> None:
    """
    Reset the session state keys to None.

    This function sets all the keys defined in SESSION_STATE_KEYS to None in
    the Streamlit session state.

    :return: None
    :rtype: None
    """
    key: str
    for key in SESSION_STATE_KEYS:
        streamlit.session_state[key] = None


def clearContent() -> None:
    """
    Clear the content-related session state keys.

    This function sets the content-related keys (from the third key onwards in
    SESSION_STATE_KEYS) to None in the Streamlit session state.

    :return: None
    :rtype: None
    """
    key: str
    for key in SESSION_STATE_KEYS[2::]:
        streamlit.session_state[key] = None

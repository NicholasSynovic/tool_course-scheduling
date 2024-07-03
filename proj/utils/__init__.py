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
    "figList",
    "figListTitles",
]


def datetimeToMinutes(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def initialState() -> None:
    key: str
    for key in SESSION_STATE_KEYS:
        if key not in streamlit.session_state:
            streamlit.session_state[key] = None


def resetState() -> None:
    key: str
    for key in SESSION_STATE_KEYS:
        streamlit.session_state[key] = None


def clearContent() -> None:
    key: str
    for key in SESSION_STATE_KEYS[2::]:
        streamlit.session_state[key] = None

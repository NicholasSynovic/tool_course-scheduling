from datetime import datetime
from typing import List

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
    """
    Converts a datetime object to the total number of minutes since midnight.

    Parameters:
    ----------
    dt : datetime
        A datetime object representing the time of day.

    Returns:
    -------
    int
        The total number of minutes since midnight represented by the datetime object.

    """  # noqa: E501

    return dt.hour * 60 + dt.minute

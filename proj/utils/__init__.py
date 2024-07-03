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
    return dt.hour * 60 + dt.minute

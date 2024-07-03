from datetime import datetime
from sqlite3 import Connection
from typing import List

import streamlit
from pandas import DataFrame
from plotly.graph_objects import Figure
from streamlit.runtime.state.session_state_proxy import SessionStateProxy


def datetimeToMinutes(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


class State:
    def __init__(self) -> None:
        self.keys: List[str] = [
            "dbConn",
            "showAnalyticButtons",
            "analyticTitle",
            "analyticSubtitle",
            "dfList",
            "dfListTitles",
            "figList",
            "figListTitles",
        ]

        self.data: SessionStateProxy = streamlit.session_state

        key: str
        for key in self.keys:
            if key not in self.data:
                self.data[key] = None

    def update(
        self,
        dbConn: Connection | None = None,
        showAnalyticButtons: bool | None = None,
        analyticTitle: str | None = None,
        analyticSubtitle: str | None = None,
        dfList: List[DataFrame] | None = None,
        dfListTitles: List[str] | None = None,
        figList: List[Figure] | None = None,
        figListTitles: List[str] | None = None,
    ) -> None:
        self.data["dbConn"] = dbConn
        self.data["showAnalyticButtons"] = showAnalyticButtons
        self.data["analyticTitle"] = analyticTitle
        self.data["analyticSubtitle"] = analyticSubtitle
        self.data["dfList"] = dfList
        self.data["dfListTitles"] = dfListTitles
        self.data["figList"] = figList
        self.data["figListTitles"] = figListTitles

    def reset(
        self,
        keepDBConnection: bool = True,
        keepButtons: bool = True,
    ) -> None:
        key: str
        for key in self.keys:
            if key == "dbConn":
                if keepDBConnection:
                    continue
                else:
                    try:
                        self.data["dbConn"].close()
                    except AttributeError:
                        pass

            if key == "showAnalyticButtons" and keepButtons:
                continue

            self.data[key] = None

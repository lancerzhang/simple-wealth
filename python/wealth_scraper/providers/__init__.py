from __future__ import annotations

from .bocomm import fetch as fetch_bocomm
from .cibwm import fetch as fetch_cibwm
from .chinawealth import fetch as fetch_chinawealth
from .cmb import fetch as fetch_cmb
from .spdb import fetch as fetch_spdb
from .wealthccb import fetch as fetch_wealthccb

__all__ = [
    "fetch_bocomm",
    "fetch_cibwm",
    "fetch_chinawealth",
    "fetch_cmb",
    "fetch_spdb",
    "fetch_wealthccb",
]

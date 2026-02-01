from __future__ import annotations

import datetime as dt
import re
from typing import Dict, List, Optional, Tuple


def parse_date(value: str | int | float) -> Optional[dt.date]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.split(" ")[0]
    if re.fullmatch(r"\d{8}", s):
        return dt.date(int(s[0:4]), int(s[4:6]), int(s[6:8]))
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return dt.date.fromisoformat(s)
    if re.fullmatch(r"\d{4}/\d{2}/\d{2}", s):
        return dt.date(int(s[0:4]), int(s[5:7]), int(s[8:10]))
    return None


def annualized_return(
    start_value: float,
    end_value: float,
    start_date: dt.date,
    end_date: dt.date,
) -> Optional[float]:
    if start_value <= 0 or end_value <= 0:
        return None
    days = (end_date - start_date).days
    if days <= 0:
        return None
    total_return = end_value / start_value - 1
    try:
        annualized = (1 + total_return) ** (365 / days) - 1
    except ValueError:
        return None
    return annualized * 100


def compute_return_from_series(series: List[Tuple[dt.date, float]]) -> Optional[float]:
    if len(series) < 2:
        return None
    series_sorted = sorted(series, key=lambda x: x[0])
    start_date, start_value = series_sorted[0]
    end_date, end_value = series_sorted[-1]
    return annualized_return(start_value, end_value, start_date, end_date)


def compute_window_return(series: List[Tuple[dt.date, float]], window_days: int) -> Optional[float]:
    if len(series) < 2:
        return None
    series_sorted = sorted(series, key=lambda x: x[0])
    end_date, end_value = series_sorted[-1]
    target_date = end_date - dt.timedelta(days=window_days)
    start_date, start_value = series_sorted[0]
    for date_value, nav_value in series_sorted:
        if date_value <= target_date:
            start_date, start_value = date_value, nav_value
        else:
            break
    return annualized_return(start_value, end_value, start_date, end_date)


def compute_window_return_with_details(
    series: List[Tuple[dt.date, float]], window_days: int
) -> Tuple[Optional[float], Optional[dt.date], Optional[float], Optional[dt.date], Optional[float]]:
    if len(series) < 2:
        return None, None, None, None, None
    series_sorted = sorted(series, key=lambda x: x[0])
    end_date, end_value = series_sorted[-1]
    target_date = end_date - dt.timedelta(days=window_days)
    start_date, start_value = series_sorted[0]
    for date_value, nav_value in series_sorted:
        if date_value <= target_date:
            start_date, start_value = date_value, nav_value
        else:
            break
    return (
        annualized_return(start_value, end_value, start_date, end_date),
        start_date,
        start_value,
        end_date,
        end_value,
    )


def normalize_returns(returns: Dict[str, Optional[float]]) -> Dict[str, float]:
    normalized: Dict[str, float] = {}
    for key in ("1m", "3m", "6m"):
        value = returns.get(key)
        if value is None:
            normalized[key] = 0.0
        else:
            normalized[key] = round(float(value), 4)
    return normalized


def parse_min_hold_days(text: str) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"(最低持有|最短持有期|持有期|持有)(\d+)(天|日)", text)
    if match:
        return int(match.group(2))
    match = re.search(r"(\d+)天", text)
    if match:
        return int(match.group(1))
    return None


def strip_company_suffix(name: str) -> str:
    return re.sub(r"(有限责任公司|有限公司)$", "", name or "").strip()

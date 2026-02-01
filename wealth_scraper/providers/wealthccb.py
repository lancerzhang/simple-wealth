from __future__ import annotations

import re
from typing import Dict, List, Tuple

from ..config import WEALTHCCB_BANKS, WEALTHCCB_ISSUER
from ..http import http_fetch
from ..utils import compute_return_from_series, normalize_returns, parse_date, parse_min_hold_days


def _extract_series(html: str, time_key: str) -> List[Tuple]:
    block_match = re.search(
        rf"if\(time\s*==\s*'{time_key}'\)([\s\S]*?)(?=if\(time\s*==\s*'|$)",
        html,
    )
    if not block_match:
        return []
    block = block_match.group(1)
    x_candidates = re.findall(r"xData\s*=\s*\[([\s\S]*?)\]", block)
    s_candidates = re.findall(r"sData\s*=\s*\[([\s\S]*?)\]", block)
    if not x_candidates or not s_candidates:
        return []

    def pick_values(candidates: List[str], pattern: str) -> List[str]:
        best: List[str] = []
        best_count = 0
        for candidate in candidates:
            values = re.findall(pattern, candidate)
            if len(values) > best_count:
                best = values
                best_count = len(values)
        return best

    dates_raw = pick_values(x_candidates, r"\d{8}")
    values_raw = pick_values(s_candidates, r"-?\d+(?:\.\d+)?")
    if not dates_raw or not values_raw:
        return []

    series = []
    for date_str, value_str in zip(dates_raw, values_raw):
        date_value = parse_date(date_str)
        if not date_value:
            continue
        series.append((date_value, float(value_str)))
    return series


def parse_html(html: str, url: str) -> Dict:
    title_match = re.search(r'<h4[^>]*class="cp-title"[^>]*>([\s\S]*?)</h4>', html)
    title_html = title_match.group(1) if title_match else ""
    code_match = re.search(r"\(([^)]+)\)", title_html)
    code = code_match.group(1).strip() if code_match else ""
    name = re.sub(r"<[^>]+>", "", title_html)
    if code:
        name = name.replace(f"({code})", "")
    name = re.sub(r"\s+", " ", name).strip()

    risk_match = re.search(
        r'<p class="firtst">\s*([^<]*R\d[^<]*)</p>\s*<p class="second">\s*风险等级',
        html,
    )
    risk_text = risk_match.group(1).strip() if risk_match else ""
    risk_level_match = re.search(r"R\d", risk_text)
    risk_level = risk_level_match.group(0) if risk_level_match else ""

    series_1m = _extract_series(html, "week")
    series_3m = _extract_series(html, "month")
    series_6m = _extract_series(html, "byear")

    returns = {
        "1m": compute_return_from_series(series_1m),
        "3m": compute_return_from_series(series_3m),
        "6m": compute_return_from_series(series_6m),
    }

    return {
        "name": name,
        "code": code,
        "issuer": WEALTHCCB_ISSUER,
        "banks": WEALTHCCB_BANKS,
        "currency": "人民币",
        "minHoldDays": parse_min_hold_days(name),
        "riskLevel": risk_level,
        "returns": normalize_returns(returns),
        "url": url,
        "type": "wealth",
    }


def fetch(url: str) -> Dict:
    html = http_fetch(url).text
    parsed = parse_html(html, url)
    return parsed

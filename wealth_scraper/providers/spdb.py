from __future__ import annotations

import json
from typing import Dict, List, Tuple
from urllib.parse import parse_qs, urlparse

from ..config import SPDB_BANKS, SPDB_ISSUER, SPDB_MIN_HOLD_DAYS
from ..http import fetch_json
from ..logger import debug_log
from ..utils import compute_window_return_with_details, normalize_returns, parse_date


def _search(chlid: int, searchword: str, page: int = 1, maxline: int = 200) -> Dict:
    url = "https://www.spdb-wm.com/api/search"
    payload = {
        "page": page,
        "channel": 0,
        "sort_type": 0,
        "maxline": maxline,
        "chlid": chlid,
        "pageflag": "true",
        "searchword": searchword,
    }
    return fetch_json(
        url,
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )


def fetch(url: str) -> Dict:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    real_code = query.get("REAL_PRD_CODE", [""])[0]
    if not real_code:
        raise RuntimeError(f"Missing REAL_PRD_CODE in {url}")

    detail = _search(1002, f"(PRDC_CD = '{real_code}')")
    detail_content = (detail.get("data") or {}).get("content") or []
    detail_item = detail_content[0] if detail_content else {}

    nav_items: List[Dict] = []
    page = 1
    while True:
        nav_resp = _search(1003, f"(REAL_PRD_CODE = '{real_code}')", page=page, maxline=200)
        data = nav_resp.get("data") or {}
        content = data.get("content") or []
        nav_items.extend(content)
        if page >= data.get("totalPages", 1):
            break
        page += 1
        if len(nav_items) >= 800:
            break

    series: List[Tuple] = []
    for item in nav_items:
        date_value = parse_date(item.get("ISS_DATE"))
        nav_value = item.get("NAV") or item.get("TOT_NAV")
        if date_value and nav_value:
            series.append((date_value, float(nav_value)))

    return_1m, start_1m, start_val_1m, end_1m, end_val_1m = compute_window_return_with_details(series, 30)
    return_3m, start_3m, start_val_3m, end_3m, end_val_3m = compute_window_return_with_details(series, 90)
    return_6m, start_6m, start_val_6m, end_6m, end_val_6m = compute_window_return_with_details(series, 180)

    debug_log(
        f"[calc][spdb] {real_code} 1m from NAV "
        f"start={start_1m} nav={start_val_1m} end={end_1m} nav={end_val_1m} -> {return_1m}"
    )
    debug_log(
        f"[calc][spdb] {real_code} 3m from NAV "
        f"start={start_3m} nav={start_val_3m} end={end_3m} nav={end_val_3m} -> {return_3m}"
    )
    debug_log(
        f"[calc][spdb] {real_code} 6m from NAV "
        f"start={start_6m} nav={start_val_6m} end={end_6m} nav={end_val_6m} -> {return_6m}"
    )

    returns = {
        "1m": return_1m,
        "3m": return_3m,
        "6m": return_6m,
    }

    risk_text = detail_item.get("RISK_GRADE") or ""
    if "较低" in risk_text:
        risk_level = "R2"
    elif "低" in risk_text:
        risk_level = "R1"
    elif "中" in risk_text:
        risk_level = "R3"
    elif "较高" in risk_text:
        risk_level = "R4"
    else:
        risk_level = ""

    return {
        "name": detail_item.get("PRDC_NM") or "",
        "code": detail_item.get("PRDC_RGST_CD") or "",
        "realProductCode": real_code,
        "issuer": SPDB_ISSUER,
        "banks": SPDB_BANKS,
        "currency": detail_item.get("RS_CRRN") or "人民币",
        "minHoldDays": SPDB_MIN_HOLD_DAYS,
        "riskLevel": risk_level,
        "returns": normalize_returns(returns),
        "url": url,
        "type": "wealth",
    }

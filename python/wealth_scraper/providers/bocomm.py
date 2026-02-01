from __future__ import annotations

import json
import re
from typing import Dict, Optional, Tuple, List
from urllib.parse import parse_qs, quote, urlparse

from ..config import BOCOMM_BANK_OVERRIDES, BOCOMM_CODE_OVERRIDES, BOCOMM_MIN_HOLD_OVERRIDES
from ..http import fetch_json
from ..logger import debug_log
from ..utils import compute_window_return_with_details, normalize_returns, parse_date, parse_min_hold_days


def _post(endpoint: str, body: Dict) -> Dict:
    url = f"https://www.bocommwm.cn/SITE/{endpoint}"
    payload = {"REQ_HEAD": {"TRAN_PROCESS": "", "TRAN_ID": ""}, "REQ_BODY": body}
    encoded = "REQ_MESSAGE=" + quote(json.dumps(payload, ensure_ascii=False))
    return fetch_json(
        url,
        method="POST",
        data=encoded.encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
    )


def fetch(url: str) -> Dict:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    fund_code = query.get("c_fundcode", [""])[0]
    if not fund_code:
        fund_code = "5811225495"

    detail = _post("queryJylcProductDetail.do", {"c_fundcode": fund_code})
    detail_data = detail.get("RSP_BODY", {}).get("result", {})
    product = detail_data.get("jylcProductBo", {}) if isinstance(detail_data, dict) else {}

    yield_data = _post("queryAllHistoricalYieldByFundcode.do", {"c_fundcode": fund_code})
    yield_list = yield_data.get("RSP_BODY", {}).get("result", []) or []
    returns: Dict[str, Optional[float]] = {"1m": None, "3m": None, "6m": None}
    for item in yield_list:
        time_key = item.get("yieldtimeinterval")
        ratio = item.get("yieldratio") or ""
        if not ratio:
            continue
        value = float(str(ratio).replace("%", ""))
        if time_key == "3":
            returns["1m"] = value
            debug_log(
                f"[calc][bocomm] {fund_code} 1m from yield "
                f"yieldratio={value} start={item.get('yieldstartdate')} end={item.get('yieldexpiredate')}"
            )
        elif time_key == "4":
            returns["3m"] = value
            debug_log(
                f"[calc][bocomm] {fund_code} 3m from yield "
                f"yieldratio={value} start={item.get('yieldstartdate')} end={item.get('yieldexpiredate')}"
            )

    break_data = _post(
        "queryJylcBreakDetail.do",
        {"c_fundcode": fund_code, "c_interestway": product.get("c_interestway", "0"), "type": "max"},
    )
    profit_list = break_data.get("RSP_BODY", {}).get("result", {}).get("profitList", []) or []
    series: List[Tuple] = []
    for item in profit_list:
        date_value = parse_date(item.get("d_cdate"))
        nav_value = item.get("f_netvalue") or item.get("f_totalnetvalue")
        if date_value and nav_value:
            series.append((date_value, float(nav_value)))

    if returns["6m"] is None:
        value, start_date, start_value, end_date, end_value = compute_window_return_with_details(series, 180)
        returns["6m"] = value
        debug_log(
            f"[calc][bocomm] {fund_code} 6m from NAV "
            f"start={start_date} nav={start_value} end={end_date} nav={end_value} -> {value}"
        )

    if returns["1m"] is None:
        value, start_date, start_value, end_date, end_value = compute_window_return_with_details(series, 30)
        returns["1m"] = value
        debug_log(
            f"[calc][bocomm] {fund_code} 1m from NAV "
            f"start={start_date} nav={start_value} end={end_date} nav={end_value} -> {value}"
        )
    if returns["3m"] is None:
        value, start_date, start_value, end_date, end_value = compute_window_return_with_details(series, 90)
        returns["3m"] = value
        debug_log(
            f"[calc][bocomm] {fund_code} 3m from NAV "
            f"start={start_date} nav={start_value} end={end_date} nav={end_value} -> {value}"
        )

    banks = BOCOMM_BANK_OVERRIDES.get(fund_code) or [product.get("c_agencyno") or "交通银行"]
    min_hold_days = BOCOMM_MIN_HOLD_OVERRIDES.get(fund_code) or parse_min_hold_days(product.get("c_fundname") or "")

    c_level = product.get("c_level") or ""
    risk_level_match = re.search(r"R\d", c_level)
    if risk_level_match:
        risk_level = risk_level_match.group(0)
    elif "较低" in c_level:
        risk_level = "R2"
    elif "低" in c_level:
        risk_level = "R1"
    elif "中" in c_level:
        risk_level = "R3"
    elif "较高" in c_level:
        risk_level = "R4"
    else:
        risk_level = ""

    code = BOCOMM_CODE_OVERRIDES.get(fund_code) or product.get("c_productcode") or fund_code

    return {
        "name": product.get("c_fundname") or "",
        "code": code,
        "fundCode": fund_code,
        "issuer": "交银理财",
        "banks": banks,
        "currency": product.get("c_moneytype") or "人民币",
        "minHoldDays": min_hold_days,
        "riskLevel": risk_level,
        "returns": normalize_returns(returns),
        "url": url,
        "type": "wealth",
        "registrationCode": product.get("c_productcode") or "",
    }

from __future__ import annotations

import json
from typing import Dict, Optional, Tuple, List

from ..http import fetch_json
from ..logger import debug_log
from ..utils import (
    compute_window_return_with_details,
    normalize_returns,
    parse_date,
    parse_min_hold_days,
    strip_company_suffix,
)


def _fetch_detail(product_id: str) -> Dict:
    url = f"https://www.cibwm.com.cn/api/public/pc/productInfo/getProductDetailByProductId/{product_id}"
    return fetch_json(url)


def _fetch_price_change(product_code: str) -> Dict:
    url = "https://www.cibwm.com.cn/api/public/pc/productInfoPriceChange/productPriceChange"
    payload = {"intervalType": "阶段", "productCode": product_code}
    return fetch_json(
        url,
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )


def _fetch_nav(product_id: str, product_code: str, page_size: int = 200) -> Dict:
    url = "https://www.cibwm.com.cn/api/public/pc/productVal/page"
    payload = {"productId": product_id, "productCode": product_code, "pageNum": 1, "pageSize": page_size}
    return fetch_json(
        url,
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )


def fetch(url: str) -> Dict:
    product_id = url.rstrip("/").split("/")[-1]
    detail = _fetch_detail(product_id)
    data = detail.get("data") or {}
    product_code = data.get("productCode", "")
    price_change = _fetch_price_change(product_code)

    returns: Dict[str, Optional[float]] = {"1m": None, "3m": None, "6m": None}
    for item in price_change.get("data", []) or []:
        time_range = item.get("timeRange")
        value = item.get("yarOfIncAndDcr")
        if time_range == "近1月":
            returns["1m"] = value
            debug_log(
                f"[calc][cibwm] {product_code} 1m from priceChange "
                f"yarOfIncAndDcr={value} baseDt={item.get('baseDt')} effectDt={item.get('effectDt')}"
            )
        elif time_range == "近3月":
            returns["3m"] = value
            debug_log(
                f"[calc][cibwm] {product_code} 3m from priceChange "
                f"yarOfIncAndDcr={value} baseDt={item.get('baseDt')} effectDt={item.get('effectDt')}"
            )
        elif time_range == "近6月":
            returns["6m"] = value
            debug_log(
                f"[calc][cibwm] {product_code} 6m from priceChange "
                f"yarOfIncAndDcr={value} baseDt={item.get('baseDt')} effectDt={item.get('effectDt')}"
            )

    if any(value is None for value in returns.values()):
        nav_data = _fetch_nav(product_id, product_code)
        nav_list = nav_data.get("data", {}).get("list", []) or []
        series: List[Tuple] = []
        for item in nav_list:
            date_value = parse_date(item.get("netvalDt") or item.get("dataDt"))
            nav_value = item.get("effIopv") or item.get("effTotNetVal") or item.get("adjustedValue")
            if date_value and nav_value:
                series.append((date_value, float(nav_value)))
        if returns["1m"] is None:
            value, start_date, start_value, end_date, end_value = compute_window_return_with_details(series, 30)
            returns["1m"] = value
            debug_log(
                f"[calc][cibwm] {product_code} 1m from NAV "
                f"start={start_date} nav={start_value} end={end_date} nav={end_value} -> {value}"
            )
        if returns["3m"] is None:
            value, start_date, start_value, end_date, end_value = compute_window_return_with_details(series, 90)
            returns["3m"] = value
            debug_log(
                f"[calc][cibwm] {product_code} 3m from NAV "
                f"start={start_date} nav={start_value} end={end_date} nav={end_value} -> {value}"
            )
        if returns["6m"] is None:
            value, start_date, start_value, end_date, end_value = compute_window_return_with_details(series, 180)
            returns["6m"] = value
            debug_log(
                f"[calc][cibwm] {product_code} 6m from NAV "
                f"start={start_date} nav={start_value} end={end_date} nav={end_value} -> {value}"
            )

    channels = [c.strip() for c in (data.get("distributionChannel") or "").split(",") if c.strip()]
    banks = [c for c in channels if "银行" in c]
    if "兴业银行" in banks:
        banks = ["兴业银行"]
    if not banks:
        banks = ["兴业银行"]

    min_hold_days = parse_min_hold_days(data.get("productDate") or "")
    issuer = strip_company_suffix(data.get("issuer") or "") or "兴银理财"
    risk_level = data.get("riskLevelOri") or data.get("riskLevel") or ""

    return {
        "name": data.get("productName") or "",
        "code": product_code,
        "issuer": issuer,
        "banks": banks,
        "currency": data.get("saleCurrency") or "",
        "minHoldDays": min_hold_days,
        "riskLevel": risk_level,
        "returns": normalize_returns(returns),
        "url": url,
        "type": "wealth",
    }

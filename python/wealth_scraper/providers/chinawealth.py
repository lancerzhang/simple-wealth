from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from ..config import CHINAWEALTH_BANK_OVERRIDES
from ..http import fetch_json
from ..logger import debug_log
from ..utils import (
    compute_window_return_with_details,
    normalize_returns,
    parse_date,
    parse_min_hold_days,
    strip_company_suffix,
)

_BASE_URL = "https://xinxipilu.chinawealth.com.cn/lcxp-platService"
_JSON_HEADERS = {"Content-Type": "application/json;charset=UTF-8"}


def _to_json_bytes(payload: Dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _to_pem_key(raw_key: str) -> str:
    if not raw_key:
        raise RuntimeError("chinawealth init key missing")
    match = re.search(
        r"-----BEGIN PRIVATE KEY-----\s*(.*?)\s*-----END PRIVATE KEY-----",
        raw_key,
        flags=re.S,
    )
    if not match:
        raise RuntimeError("chinawealth private key format invalid")
    key_body = re.sub(r"\s+", "", match.group(1))
    lines = [key_body[i : i + 64] for i in range(0, len(key_body), 64)]
    return "-----BEGIN PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END PRIVATE KEY-----\n"


def _sign_sha256_rsa_base64(payload: bytes, pem_key: str) -> str:
    key_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as key_file:
            key_file.write(pem_key)
            key_path = key_file.name

        digest = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", key_path],
            input=payload,
            capture_output=True,
            check=True,
        )
        b64 = subprocess.run(
            ["openssl", "base64", "-A"],
            input=digest.stdout,
            capture_output=True,
            check=True,
        )
        signature = b64.stdout.decode("utf-8").strip()
        if not signature:
            raise RuntimeError("chinawealth signature empty")
        return signature
    except FileNotFoundError as exc:
        raise RuntimeError("openssl not found; required for chinawealth signing") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"chinawealth signing failed: {exc.stderr.decode('utf-8', errors='ignore')}") from exc
    finally:
        if key_path:
            try:
                os.remove(key_path)
            except OSError:
                pass


def _signed_post(endpoint: str, payload: Dict) -> Dict:
    init_resp = fetch_json(
        f"{_BASE_URL}/product/getInitData",
        method="POST",
        data=b"{}",
        headers=_JSON_HEADERS,
    )
    pem_key = _to_pem_key((init_resp.get("data") or "").strip())
    body = _to_json_bytes(payload)
    signature = _sign_sha256_rsa_base64(body, pem_key)
    headers = dict(_JSON_HEADERS)
    headers["signature"] = signature
    return fetch_json(f"{_BASE_URL}{endpoint}", method="POST", data=body, headers=headers)


def _parse_risk_level(text: str) -> str:
    if not text:
        return ""
    direct = re.search(r"R\d", text, flags=re.I)
    if direct:
        return direct.group(0).upper()
    if "一级" in text or "低" in text:
        return "R1"
    if "二级" in text or "中低" in text:
        return "R2"
    if "三级" in text or "中" in text:
        return "R3"
    if "四级" in text or "中高" in text:
        return "R4"
    if "五级" in text or "高" in text:
        return "R5"
    return ""


def fetch(url: str) -> Dict:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    reg_code = query.get("prodRegCode", [""])[0].strip()
    if not reg_code:
        raise RuntimeError(f"Missing prodRegCode in {url}")

    list_resp = _signed_post(
        "/product/getProductList",
        {
            "orgName": "",
            "prodName": "",
            "prodRegCode": reg_code,
            "pageNum": 1,
            "pageSize": 1,
        },
    )
    list_items = (list_resp.get("data") or {}).get("list") or []
    list_item = list_items[0] if list_items else {}
    prod_id = str(list_item.get("prodId") or "").strip()

    detail_payload: Dict[str, object] = {
        "prodRegCode": reg_code,
        "pageNum": 1,
        "pageSize": 200,
    }
    if prod_id:
        detail_payload["prodId"] = prod_id

    detail_resp = _signed_post("/product/getProductDetail", detail_payload)
    detail_data = detail_resp.get("data") or {}
    basic = detail_data.get("prodBasicInfoVo") or {}
    net = detail_data.get("productTypeNetValueVo") or {}
    net_line = net.get("netValueLine") or []

    series: List[Tuple] = []
    for item in net_line:
        date_value = parse_date(item.get("netValueDate"))
        nav_value = (
            item.get("acumltNetVal")
            or item.get("shareNetVal")
            or item.get("priceBuy")
            or item.get("priceRedeem")
        )
        if date_value and nav_value:
            series.append((date_value, float(nav_value)))

    return_1m, start_1m, start_val_1m, end_1m, end_val_1m = compute_window_return_with_details(series, 30)
    return_3m, start_3m, start_val_3m, end_3m, end_val_3m = compute_window_return_with_details(series, 90)
    return_6m, start_6m, start_val_6m, end_6m, end_val_6m = compute_window_return_with_details(series, 180)

    debug_log(
        f"[calc][chinawealth] {reg_code} 1m from NAV "
        f"start={start_1m} nav={start_val_1m} end={end_1m} nav={end_val_1m} -> {return_1m}"
    )
    debug_log(
        f"[calc][chinawealth] {reg_code} 3m from NAV "
        f"start={start_3m} nav={start_val_3m} end={end_3m} nav={end_val_3m} -> {return_3m}"
    )
    debug_log(
        f"[calc][chinawealth] {reg_code} 6m from NAV "
        f"start={start_6m} nav={start_val_6m} end={end_6m} nav={end_val_6m} -> {return_6m}"
    )

    name = basic.get("prodName") or list_item.get("prodName") or ""
    issuer = strip_company_suffix(basic.get("orgName") or list_item.get("orgName") or "")
    risk_text = basic.get("prodRiskLevelName") or list_item.get("prodRiskLevelName") or ""
    banks = CHINAWEALTH_BANK_OVERRIDES.get(reg_code) or ["工商银行"]
    default_sub_share = net.get("defaultSubShareCode") or ""

    return {
        "name": name,
        "code": reg_code,
        "registrationCode": reg_code,
        "subShareCode": default_sub_share,
        "issuer": issuer,
        "banks": banks,
        "currency": basic.get("collCcyName") or "",
        "minHoldDays": parse_min_hold_days(name),
        "riskLevel": _parse_risk_level(risk_text),
        "returns": normalize_returns(
            {
                "1m": return_1m,
                "3m": return_3m,
                "6m": return_6m,
            }
        ),
        "url": url,
        "type": "wealth",
    }

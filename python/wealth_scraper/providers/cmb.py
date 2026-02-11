from __future__ import annotations

import base64
import json
import re
import subprocess
import time
import uuid
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from ..config import CMB_SA_BANK_OVERRIDES
from ..http import fetch_json
from ..logger import debug_log
from ..utils import (
    compute_window_return_with_details,
    normalize_returns,
    parse_date,
    parse_min_hold_days,
    strip_company_suffix,
)

_BASE_URL = "https://cfweb.paas.cmbchina.com/api"
_APP_ID = "LB50.22_CFWebUI"
_AUTH_SN_B64 = "NXF3QkdqdTczSkFYaWQ0RA=="
_AUTH_SN_HEX = base64.b64decode(_AUTH_SN_B64).hex()


def _to_json_bytes(payload: Dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sm4_ecb_signature(plaintext: str) -> str:
    try:
        output = subprocess.run(
            ["openssl", "enc", "-sm4-ecb", "-K", _AUTH_SN_HEX, "-nosalt", "-base64", "-A"],
            input=plaintext.encode("utf-8"),
            capture_output=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("openssl not found; required for cmb signing") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"cmb signing failed: {exc.stderr.decode('utf-8', errors='ignore')}") from exc
    signature = output.stdout.decode("utf-8").strip()
    if not signature:
        raise RuntimeError("cmb signature empty")
    return signature


def _build_headers() -> Dict[str, str]:
    ts = str(int(time.time() * 1000))
    signature = _sm4_ecb_signature(f"{_APP_ID}|{ts}")
    return {
        "Content-Type": "application/json",
        "appId": _APP_ID,
        "timespan": ts,
        "signature": signature,
        "X-B3-BusinessId": uuid.uuid4().hex,
    }


def _post(endpoint: str, payload: Dict) -> Dict:
    return fetch_json(
        f"{_BASE_URL}/{endpoint}",
        method="POST",
        data=_to_json_bytes(payload),
        headers=_build_headers(),
    )


def _parse_risk_level(text: str) -> str:
    if not text:
        return ""
    direct = re.search(r"R\d", text, flags=re.I)
    if direct:
        return direct.group(0).upper()
    if "低" in text:
        return "R1"
    if "中低" in text:
        return "R2"
    if "中高" in text:
        return "R4"
    if "中" in text:
        return "R3"
    if "高" in text:
        return "R5"
    return ""


def fetch(url: str) -> Dict:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    saa_cod = query.get("saaCod", [""])[0].strip()
    fun_cod = query.get("funCod", [""])[0].strip()
    if not saa_cod or not fun_cod:
        raise RuntimeError(f"Missing saaCod/funCod in {url}")

    detail = _post(f"ProductInfo/getSAProductDetail?funCod={fun_cod}&saaCod={saa_cod}", {})
    detail_info = _post(f"ProductInfo/getSAProductDetailInfo?saaCod={saa_cod}&funCod={fun_cod}", {})
    value = _post(
        "ProductValue/getSAValueByPage",
        {"funCod": fun_cod, "saaCod": saa_cod, "pageNum": 1, "pageSize": 200},
    )

    detail_body = detail.get("body") or {}
    detail_info_body = detail_info.get("body") or {}
    value_body = value.get("body") or {}
    rows = value_body.get("data") or []
    total_record = int(value_body.get("totalRecord") or len(rows) or 0)

    page_num = 2
    while len(rows) < total_record:
        page_resp = _post(
            "ProductValue/getSAValueByPage",
            {"funCod": fun_cod, "saaCod": saa_cod, "pageNum": page_num, "pageSize": 200},
        )
        page_rows = (page_resp.get("body") or {}).get("data") or []
        if not page_rows:
            break
        rows.extend(page_rows)
        page_num += 1
        if page_num > 20:
            break

    series: List[Tuple] = []
    for item in rows:
        date_value = parse_date(item.get("znavDat"))
        nav_value = item.get("znavVal") or item.get("znavCtl")
        if date_value and nav_value:
            series.append((date_value, float(nav_value)))

    return_1m, start_1m, start_val_1m, end_1m, end_val_1m = compute_window_return_with_details(series, 30)
    return_3m, start_3m, start_val_3m, end_3m, end_val_3m = compute_window_return_with_details(series, 90)
    return_6m, start_6m, start_val_6m, end_6m, end_val_6m = compute_window_return_with_details(series, 180)

    debug_log(
        f"[calc][cmb] {fun_cod}/{saa_cod} 1m from NAV "
        f"start={start_1m} nav={start_val_1m} end={end_1m} nav={end_val_1m} -> {return_1m}"
    )
    debug_log(
        f"[calc][cmb] {fun_cod}/{saa_cod} 3m from NAV "
        f"start={start_3m} nav={start_val_3m} end={end_3m} nav={end_val_3m} -> {return_3m}"
    )
    debug_log(
        f"[calc][cmb] {fun_cod}/{saa_cod} 6m from NAV "
        f"start={start_6m} nav={start_val_6m} end={end_6m} nav={end_val_6m} -> {return_6m}"
    )

    banks = CMB_SA_BANK_OVERRIDES.get(f"{saa_cod}|{fun_cod}") or ["招商银行"]
    name = detail_info_body.get("prdName") or detail_body.get("prdBrief") or ""
    issuer = strip_company_suffix(detail_info_body.get("comNam") or detail_body.get("defMaaCod") or "")
    risk_text = detail_info_body.get("risk") or ""
    reg_code = detail_info_body.get("regCode") or detail_body.get("regcode") or ""

    return {
        "name": name,
        "code": reg_code or detail_body.get("prdCode") or fun_cod,
        "registrationCode": reg_code,
        "realProductCode": detail_body.get("prdCode") or fun_cod,
        "issuer": issuer,
        "banks": banks,
        "currency": detail_info_body.get("currency") or "",
        "minHoldDays": parse_min_hold_days(detail_info_body.get("term") or name),
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
        "saaCode": saa_cod,
        "funCode": fun_cod,
    }

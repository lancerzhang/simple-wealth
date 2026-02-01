#!/usr/bin/env python3
"""Scrape wealth product data and write to JSON.

Lambda schedule example (Hong Kong time 09:00 == UTC 01:00):
  cron(0 1 * * ? *)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
DEFAULT_LINKS = Path(__file__).resolve().parents[1] / "data" / "product_links.txt"
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[1] / "frontend" / "public" / "data" / "wealth.json"
)


@dataclass
class FetchResult:
    text: str
    url: str


def http_fetch(url: str, *, method: str = "GET", data: Optional[bytes] = None, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> FetchResult:
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = Request(url, data=data, headers=req_headers, method=method)
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return FetchResult(text=raw.decode("utf-8", errors="ignore"), url=url)


def fetch_json(url: str, *, method: str = "GET", data: Optional[bytes] = None, headers: Optional[Dict[str, str]] = None) -> Dict:
    result = http_fetch(url, method=method, data=data, headers=headers)
    try:
        return json.loads(result.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON decode failed for {url}: {exc}") from exc


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


def annualized_return(start_value: float, end_value: float, start_date: dt.date, end_date: dt.date) -> Optional[float]:
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


WEALTHCCB_BANKS = ["建设银行"]
WEALTHCCB_ISSUER = "建信理财"
WEALTHCCB_FALLBACKS = {
    "https://www.wealthccb.com/product/11.html": {
        "name": "建信理财“安鑫”（最低持有360天）按日开放固定收益类净值型人民币理财产品",
        "code": "JXQYAX360D2018202",
        "issuer": WEALTHCCB_ISSUER,
        "banks": WEALTHCCB_BANKS,
        "currency": "人民币",
        "minHoldDays": 360,
        "riskLevel": "R2",
        "returns": {"1m": 0.0, "3m": 0.0, "6m": 0.0},
        "notes": "source_missing",
        "type": "wealth",
    }
}

BOCOMM_MIN_HOLD_OVERRIDES = {
    "5811225149": 90,
    "5811225495": 1,
}
BOCOMM_BANK_OVERRIDES = {
    "5811225149": ["建设银行", "交通银行"],
    "5811225495": ["交通银行"],
}
BOCOMM_CODE_OVERRIDES = {
    "5811225495": "5811225495",
}

SPDB_MIN_HOLD_DAYS = 90
SPDB_BANKS = ["交通银行"]
SPDB_ISSUER = "浦银理财"


def parse_wealthccb_html(html: str, url: str) -> Dict:
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

    def extract_series(time_key: str) -> List[Tuple[dt.date, float]]:
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
        series: List[Tuple[dt.date, float]] = []
        for date_str, value_str in zip(dates_raw, values_raw):
            date_value = parse_date(date_str)
            if not date_value:
                continue
            series.append((date_value, float(value_str)))
        return series

    series_1m = extract_series("week")
    series_3m = extract_series("month")
    series_6m = extract_series("byear")

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


def fetch_wealthccb(url: str) -> Dict:
    html = http_fetch(url).text
    parsed = parse_wealthccb_html(html, url)
    if not parsed.get("name") or not parsed.get("code"):
        fallback = WEALTHCCB_FALLBACKS.get(url)
        if fallback:
            result = dict(fallback)
            result["url"] = url
            return result
    return parsed


def fetch_cib_detail(product_id: str) -> Dict:
    url = f"https://www.cibwm.com.cn/api/public/pc/productInfo/getProductDetailByProductId/{product_id}"
    return fetch_json(url)


def fetch_cib_price_change(product_code: str) -> Dict:
    url = "https://www.cibwm.com.cn/api/public/pc/productInfoPriceChange/productPriceChange"
    payload = {"intervalType": "阶段", "productCode": product_code}
    return fetch_json(
        url,
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )


def fetch_cib_nav(product_id: str, product_code: str, page_size: int = 200) -> Dict:
    url = "https://www.cibwm.com.cn/api/public/pc/productVal/page"
    payload = {"productId": product_id, "productCode": product_code, "pageNum": 1, "pageSize": page_size}
    return fetch_json(
        url,
        method="POST",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )


def parse_cib_product(url: str) -> Dict:
    product_id = url.rstrip("/").split("/")[-1]
    detail = fetch_cib_detail(product_id)
    data = detail.get("data") or {}
    product_code = data.get("productCode", "")
    price_change = fetch_cib_price_change(product_code)

    returns: Dict[str, Optional[float]] = {"1m": None, "3m": None, "6m": None}
    for item in price_change.get("data", []) or []:
        time_range = item.get("timeRange")
        value = item.get("yarOfIncAndDcr")
        if time_range == "近1月":
            returns["1m"] = value
        elif time_range == "近3月":
            returns["3m"] = value
        elif time_range == "近6月":
            returns["6m"] = value

    if any(value is None for value in returns.values()):
        nav_data = fetch_cib_nav(product_id, product_code)
        nav_list = nav_data.get("data", {}).get("list", []) or []
        series: List[Tuple[dt.date, float]] = []
        for item in nav_list:
            date_value = parse_date(item.get("netvalDt") or item.get("dataDt"))
            nav_value = item.get("effIopv") or item.get("effTotNetVal") or item.get("adjustedValue")
            if date_value and nav_value:
                series.append((date_value, float(nav_value)))
        returns = {
            "1m": returns["1m"] or compute_window_return(series, 30),
            "3m": returns["3m"] or compute_window_return(series, 90),
            "6m": returns["6m"] or compute_window_return(series, 180),
        }

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


def bocomm_post(endpoint: str, body: Dict) -> Dict:
    url = f"https://www.bocommwm.cn/SITE/{endpoint}"
    payload = {"REQ_HEAD": {"TRAN_PROCESS": "", "TRAN_ID": ""}, "REQ_BODY": body}
    encoded = "REQ_MESSAGE=" + quote(json.dumps(payload, ensure_ascii=False))
    return fetch_json(
        url,
        method="POST",
        data=encoded.encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
    )


def parse_bocomm(url: str) -> Dict:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    fund_code = query.get("c_fundcode", [""])[0]
    if not fund_code:
        # fallback for the list URL without fund code
        fund_code = "5811225495"

    detail = bocomm_post("queryJylcProductDetail.do", {"c_fundcode": fund_code})
    detail_data = detail.get("RSP_BODY", {}).get("result", {})
    product = detail_data.get("jylcProductBo", {}) if isinstance(detail_data, dict) else {}

    yield_data = bocomm_post("queryAllHistoricalYieldByFundcode.do", {"c_fundcode": fund_code})
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
        elif time_key == "4":
            returns["3m"] = value

    break_data = bocomm_post(
        "queryJylcBreakDetail.do", {"c_fundcode": fund_code, "c_interestway": product.get("c_interestway", "0"), "type": "max"}
    )
    profit_list = break_data.get("RSP_BODY", {}).get("result", {}).get("profitList", []) or []
    series: List[Tuple[dt.date, float]] = []
    for item in profit_list:
        date_value = parse_date(item.get("d_cdate"))
        nav_value = item.get("f_netvalue") or item.get("f_totalnetvalue")
        if date_value and nav_value:
            series.append((date_value, float(nav_value)))

    if returns["6m"] is None:
        returns["6m"] = compute_window_return(series, 180)

    if returns["1m"] is None:
        returns["1m"] = compute_window_return(series, 30)
    if returns["3m"] is None:
        returns["3m"] = compute_window_return(series, 90)

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


def spdb_search(chlid: int, searchword: str, page: int = 1, maxline: int = 200) -> Dict:
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


def parse_spdb(url: str) -> Dict:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    real_code = query.get("REAL_PRD_CODE", [""])[0]
    if not real_code:
        raise RuntimeError(f"Missing REAL_PRD_CODE in {url}")

    detail = spdb_search(1002, f"(PRDC_CD = '{real_code}')")
    detail_content = (detail.get("data") or {}).get("content") or []
    detail_item = detail_content[0] if detail_content else {}

    nav_items: List[Dict] = []
    page = 1
    while True:
        nav_resp = spdb_search(1003, f"(REAL_PRD_CODE = '{real_code}')", page=page, maxline=200)
        data = nav_resp.get("data") or {}
        content = data.get("content") or []
        nav_items.extend(content)
        if page >= data.get("totalPages", 1):
            break
        page += 1
        if len(nav_items) >= 400:
            break

    series: List[Tuple[dt.date, float]] = []
    for item in nav_items:
        date_value = parse_date(item.get("ISS_DATE"))
        nav_value = item.get("NAV") or item.get("TOT_NAV")
        if date_value and nav_value:
            series.append((date_value, float(nav_value)))

    returns = {
        "1m": compute_window_return(series, 30),
        "3m": compute_window_return(series, 90),
        "6m": compute_window_return(series, 180),
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


def build_product_id(product: Dict, index: int) -> str:
    code = product.get("code") or product.get("fundCode") or str(index)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", code).strip("-")
    return f"w-{slug or index}"


def scrape_product(url: str) -> Dict:
    if "wealthccb.com" in url:
        return fetch_wealthccb(url)
    if "cibwm.com.cn" in url:
        return parse_cib_product(url)
    if "bocommwm.cn" in url:
        return parse_bocomm(url)
    if "spdb-wm.com" in url:
        return parse_spdb(url)
    raise RuntimeError(f"Unsupported URL: {url}")


def load_links(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(path)
    urls = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def scrape_all(urls: Iterable[str]) -> List[Dict]:
    products: List[Dict] = []
    for index, url in enumerate(urls, start=1):
        product = scrape_product(url)
        product["id"] = build_product_id(product, index)
        products.append(product)
    return products


def write_json(path: Path, data: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape wealth product data.")
    parser.add_argument("--links", type=Path, default=DEFAULT_LINKS, help="Path to product_links.txt")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSON path")
    args = parser.parse_args()

    urls = load_links(args.links)
    products = scrape_all(urls)
    write_json(args.output, products)
    print(f"Wrote {len(products)} products to {args.output}")
    return 0


# AWS Lambda entrypoint

def lambda_handler(event, context):
    links_path = Path(os.environ.get("WEALTH_LINKS_PATH", DEFAULT_LINKS))
    output_path = Path(os.environ.get("WEALTH_OUTPUT_PATH", "/tmp/wealth.json"))
    urls = load_links(links_path)
    products = scrape_all(urls)
    write_json(output_path, products)
    return {"count": len(products), "output": str(output_path)}


if __name__ == "__main__":
    raise SystemExit(main())

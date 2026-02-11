from __future__ import annotations

import json
import re
import sys
import datetime as dt
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .providers import (
    fetch_bocomm,
    fetch_cibwm,
    fetch_chinawealth,
    fetch_cmb,
    fetch_spdb,
    fetch_wealthccb,
)


def build_product_id(product: Dict, index: int) -> str:
    code = product.get("code") or product.get("fundCode") or str(index)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", str(code)).strip("-")
    return f"w-{slug or index}"


def scrape_product(url: str) -> Dict:
    if "wealthccb.com" in url:
        return fetch_wealthccb(url)
    if "cibwm.com.cn" in url:
        return fetch_cibwm(url)
    if "bocommwm.cn" in url:
        return fetch_bocomm(url)
    if "spdb-wm.com" in url:
        return fetch_spdb(url)
    if "xinxipilu.chinawealth.com.cn" in url:
        return fetch_chinawealth(url)
    if "cfweb.paas.cmbchina.com" in url:
        return fetch_cmb(url)
    raise RuntimeError(f"Unsupported URL: {url}")


def load_links(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(path)
    urls: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def scrape_all(urls: Iterable[str]) -> Tuple[List[Dict], List[Tuple[str, str]]]:
    products: List[Dict] = []
    failures: List[Tuple[str, str]] = []
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    for index, url in enumerate(urls, start=1):
        try:
            product = scrape_product(url)
            product["id"] = build_product_id(product, index)
            product.setdefault("updatedAt", timestamp)
            products.append(product)
        except Exception as exc:
            failures.append((url, str(exc)))
            print(f"[scrape] failed for {url}: {exc}", file=sys.stderr, flush=True)
            continue
    return products, failures


def write_json(path: Path, data: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

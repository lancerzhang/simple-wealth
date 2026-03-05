from __future__ import annotations

import os
import json
import re
import sys
import datetime as dt
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from .providers import (
    fetch_bocomm,
    fetch_cibwm,
    fetch_chinawealth,
    fetch_cmb,
    fetch_spdb,
    fetch_wealthccb,
)

_FETCHERS: Dict[str, Callable[[str], Dict]] = {
    "wealthccb": fetch_wealthccb,
    "cibwm": fetch_cibwm,
    "bocomm": fetch_bocomm,
    "spdb": fetch_spdb,
    "chinawealth": fetch_chinawealth,
    "cmb": fetch_cmb,
}


def build_product_id(product: Dict, index: int) -> str:
    code = product.get("code") or product.get("fundCode") or str(index)
    slug = re.sub(r"[^A-Za-z0-9]+", "-", str(code)).strip("-")
    return f"w-{slug or index}"


def _normalize_channels(value: Any, context: str) -> Optional[List[str]]:
    if value is None:
        return None
    if isinstance(value, str):
        channel = value.strip()
        return [channel] if channel else None
    if not isinstance(value, list):
        raise ValueError(f"{context}: salesChannels/banks must be string or list")

    channels: List[str] = []
    for idx, item in enumerate(value, start=1):
        channel = str(item).strip()
        if not channel:
            raise ValueError(f"{context}: empty channel at index {idx}")
        if channel not in channels:
            channels.append(channel)
    return channels or None


def _normalize_retries(value: Any, context: str) -> Optional[int]:
    if value is None or value == "":
        return None
    retries = int(value)
    if retries < 0:
        raise ValueError(f"{context}: retries must be >= 0")
    return retries


def _normalize_target(
    raw: Any,
    *,
    context: str,
    default_scraper: str | None = None,
    default_retries: int | None = None,
    default_channels: List[str] | None = None,
) -> Dict[str, Any]:
    if isinstance(raw, str):
        url = raw.strip()
        if not url:
            raise ValueError(f"{context}: empty url")
        return {
            "url": url,
            "scraper": default_scraper,
            "retries": default_retries,
            "salesChannels": default_channels,
        }
    if not isinstance(raw, dict):
        raise ValueError(f"{context}: item must be string or object")

    url = str(raw.get("url") or "").strip()
    if not url:
        raise ValueError(f"{context}: missing url")

    scraper = raw.get("scraper")
    if scraper is None:
        scraper = default_scraper
    else:
        scraper = str(scraper).strip().lower() or None

    retries = _normalize_retries(raw.get("retries"), context)
    if retries is None:
        retries = default_retries

    channels = _normalize_channels(raw.get("salesChannels"), context)
    if channels is None:
        channels = _normalize_channels(raw.get("banks"), context)
    if channels is None:
        channels = default_channels

    return {
        "url": url,
        "scraper": scraper,
        "retries": retries,
        "salesChannels": channels,
    }


def load_targets(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() != ".json":
        return [_normalize_target(url, context=f"{path}") for url in load_links(path)]

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    targets: List[Dict[str, Any]] = []
    if isinstance(raw, list):
        for idx, item in enumerate(raw, start=1):
            targets.append(_normalize_target(item, context=f"{path}:items[{idx}]"))
        return targets

    if not isinstance(raw, dict):
        raise ValueError(f"{path}: root must be object or list")

    if "sites" in raw:
        sites = raw.get("sites") or []
        if not isinstance(sites, list):
            raise ValueError(f"{path}: sites must be an array")
        for site_idx, site in enumerate(sites, start=1):
            context = f"{path}:sites[{site_idx}]"
            if not isinstance(site, dict):
                raise ValueError(f"{context}: site must be object")

            site_scraper_raw = site.get("scraper")
            site_scraper = str(site_scraper_raw).strip().lower() if site_scraper_raw else None
            site_retries = _normalize_retries(site.get("retries"), context)
            site_channels = _normalize_channels(site.get("salesChannels"), context)
            if site_channels is None:
                site_channels = _normalize_channels(site.get("banks"), context)

            products = site.get("products") or []
            if not isinstance(products, list):
                raise ValueError(f"{context}: products must be an array")

            for prod_idx, product in enumerate(products, start=1):
                prod_context = f"{context}:products[{prod_idx}]"
                targets.append(
                    _normalize_target(
                        product,
                        context=prod_context,
                        default_scraper=site_scraper,
                        default_retries=site_retries,
                        default_channels=site_channels,
                    )
                )
        return targets

    products = raw.get("products")
    if isinstance(products, list):
        for idx, item in enumerate(products, start=1):
            targets.append(_normalize_target(item, context=f"{path}:products[{idx}]"))
        return targets

    raise ValueError(f"{path}: expected sites[] or products[]")


def _detect_scraper(url: str) -> str:
    if "wealthccb.com" in url:
        return "wealthccb"
    if "cibwm.com.cn" in url:
        return "cibwm"
    if "bocommwm.cn" in url or "bocommwm.com" in url:
        return "bocomm"
    if "spdb-wm.com" in url:
        return "spdb"
    if "xinxipilu.chinawealth.com.cn" in url:
        return "chinawealth"
    if "cfweb.paas.cmbchina.com" in url:
        return "cmb"
    raise RuntimeError(f"Unsupported URL: {url}")


def scrape_product(url: str, scraper: str | None = None) -> Dict:
    selected_scraper = scraper or _detect_scraper(url)
    fetcher = _FETCHERS.get(selected_scraper)
    if fetcher is None:
        raise RuntimeError(f"Unsupported scraper: {selected_scraper} (url={url})")
    return fetcher(url)


def load_links(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".json":
        return [target["url"] for target in load_targets(path)]

    urls: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


@contextmanager
def _override_http_retries(retries: int | None):
    if retries is None:
        yield
        return
    old_value = os.environ.get("WEALTH_HTTP_RETRIES")
    os.environ["WEALTH_HTTP_RETRIES"] = str(retries)
    try:
        yield
    finally:
        if old_value is None:
            os.environ.pop("WEALTH_HTTP_RETRIES", None)
        else:
            os.environ["WEALTH_HTTP_RETRIES"] = old_value


def scrape_all(items: Iterable[str | Dict[str, Any]]) -> Tuple[List[Dict], List[Tuple[str, str]]]:
    products: List[Dict] = []
    failures: List[Tuple[str, str]] = []
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    for index, item in enumerate(items, start=1):
        target = _normalize_target(item, context=f"item[{index}]")
        url = target["url"]
        try:
            with _override_http_retries(target.get("retries")):
                product = scrape_product(url, scraper=target.get("scraper"))
            if target.get("salesChannels"):
                product["banks"] = target["salesChannels"]
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

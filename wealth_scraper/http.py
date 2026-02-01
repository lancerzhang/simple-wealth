from __future__ import annotations

import json
import os
import ssl
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.request import Request, urlopen

from .config import USER_AGENT


@dataclass
class FetchResult:
    text: str
    url: str


def _build_ssl_context() -> ssl.SSLContext:
    if os.environ.get("WEALTH_SSL_NO_VERIFY") == "1":
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    ca_bundle = os.environ.get("WEALTH_CA_BUNDLE")
    if ca_bundle:
        return ssl.create_default_context(cafile=ca_bundle)

    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


_SSL_CONTEXT = _build_ssl_context()


def http_fetch(
    url: str,
    *,
    method: str = "GET",
    data: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
) -> FetchResult:
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = Request(url, data=data, headers=req_headers, method=method)
    with urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
        raw = resp.read()
    return FetchResult(text=raw.decode("utf-8", errors="ignore"), url=url)


def fetch_json(
    url: str,
    *,
    method: str = "GET",
    data: Optional[bytes] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict:
    result = http_fetch(url, method=method, data=data, headers=headers)
    try:
        return json.loads(result.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"JSON decode failed for {url}: {exc}") from exc

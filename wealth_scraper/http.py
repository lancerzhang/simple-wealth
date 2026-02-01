from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.request import Request, urlopen

from .config import USER_AGENT


@dataclass
class FetchResult:
    text: str
    url: str


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
    with urlopen(req, timeout=timeout) as resp:
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

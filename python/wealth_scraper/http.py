from __future__ import annotations

import json
import os
import ssl
import time
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import USER_AGENT
from .logger import debug_log


@dataclass
class FetchResult:
    text: str
    url: str


def _build_ssl_context(allow_legacy: bool) -> ssl.SSLContext:
    if os.environ.get("WEALTH_SSL_NO_VERIFY") == "1":
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    else:
        ca_bundle = os.environ.get("WEALTH_CA_BUNDLE")
        if ca_bundle:
            context = ssl.create_default_context(cafile=ca_bundle)
        else:
            try:
                import certifi

                context = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                context = ssl.create_default_context()

    if allow_legacy:
        legacy_flag = getattr(ssl, "OP_LEGACY_SERVER_CONNECT", 0)
        if legacy_flag:
            context.options |= legacy_flag
    return context


_SSL_CONTEXT = _build_ssl_context(allow_legacy=False)
_SSL_CONTEXT_LEGACY = _build_ssl_context(allow_legacy=True)


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
    prefer_legacy = os.environ.get("WEALTH_SSL_ALLOW_LEGACY") == "1"
    context = _SSL_CONTEXT_LEGACY if prefer_legacy else _SSL_CONTEXT
    retries = int(os.environ.get("WEALTH_HTTP_RETRIES", "3"))
    backoff = float(os.environ.get("WEALTH_HTTP_RETRY_BACKOFF", "0.8"))
    retry_statuses = {404, 408, 429, 500, 502, 503, 504}

    for attempt in range(retries + 1):
        debug_log(f"[http] {method} {url} attempt {attempt + 1}/{retries + 1} legacy={prefer_legacy}")
        try:
            with urlopen(req, timeout=timeout, context=context) as resp:
                raw = resp.read()
            return FetchResult(text=raw.decode("utf-8", errors="ignore"), url=url)
        except ssl.SSLError as exc:
            if not prefer_legacy and "UNSAFE_LEGACY_RENEGOTIATION_DISABLED" in str(exc):
                prefer_legacy = True
                context = _SSL_CONTEXT_LEGACY
                debug_log(f"[http] legacy renegotiation enabled for {url}")
                if attempt < retries:
                    continue
            raise
        except HTTPError as exc:
            debug_log(f"[http] HTTP {exc.code} {exc.reason} for {url}")
            if exc.code in retry_statuses and attempt < retries:
                time.sleep(backoff * (2 ** attempt))
                continue
            raise
        except URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, ssl.SSLError) and "UNSAFE_LEGACY_RENEGOTIATION_DISABLED" in str(reason):
                if not prefer_legacy:
                    prefer_legacy = True
                    context = _SSL_CONTEXT_LEGACY
                    debug_log(f"[http] legacy renegotiation enabled for {url} via URLError")
                    if attempt < retries:
                        continue
            debug_log(f"[http] URLError for {url}: {reason}")
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
                continue
            raise


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

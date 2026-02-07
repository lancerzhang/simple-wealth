"""Backward-compatible Lambda entry point (uses env paths)."""

from __future__ import annotations

import os
from .config import (
    DEFAULT_FUND_LINKS,
    DEFAULT_FUND_OUTPUT,
    DEFAULT_WEALTH_LINKS,
    DEFAULT_WEALTH_OUTPUT,
)
from .run import run_scrape


def lambda_handler(event, context):
    evt = event or {}
    wealth_links = evt.get("wealth_links") or os.environ.get("WEALTH_LINKS_PATH") or DEFAULT_WEALTH_LINKS
    fund_links = evt.get("fund_links") or os.environ.get("FUND_LINKS_PATH") or DEFAULT_FUND_LINKS
    wealth_output = evt.get("wealth_output") or os.environ.get("WEALTH_OUTPUT_PATH") or DEFAULT_WEALTH_OUTPUT
    fund_output = evt.get("fund_output") or os.environ.get("FUND_OUTPUT_PATH") or DEFAULT_FUND_OUTPUT

    return run_scrape(
        wealth_links=wealth_links,
        fund_links=fund_links,
        wealth_output=wealth_output,
        fund_output=fund_output,
    )

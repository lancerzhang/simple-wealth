from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

from .config import (
    DEFAULT_FUND_LINKS,
    DEFAULT_FUND_OUTPUT,
    DEFAULT_WEALTH_LINKS,
    DEFAULT_WEALTH_OUTPUT,
)
from .scraper import load_links, scrape_all, write_json
from .storage import publish_outputs


def _build_paths(
    wealth_links: Path | str | None = None,
    fund_links: Path | str | None = None,
    wealth_output: Path | str | None = None,
    fund_output: Path | str | None = None,
):
    return {
        "wealth_links": Path(wealth_links or DEFAULT_WEALTH_LINKS),
        "fund_links": Path(fund_links or DEFAULT_FUND_LINKS),
        "wealth_output": Path(wealth_output or DEFAULT_WEALTH_OUTPUT),
        "fund_output": Path(fund_output or DEFAULT_FUND_OUTPUT),
    }


def run_scrape(
    *,
    wealth_links: Path | str | None = None,
    fund_links: Path | str | None = None,
    wealth_output: Path | str | None = None,
    fund_output: Path | str | None = None,
) -> Dict:
    paths = _build_paths(wealth_links, fund_links, wealth_output, fund_output)

    wealth_urls = load_links(paths["wealth_links"])
    fund_urls = load_links(paths["fund_links"])

    wealth_products, wealth_failures = scrape_all(wealth_urls)
    fund_products, fund_failures = scrape_all(fund_urls)

    write_json(paths["wealth_output"], wealth_products)
    write_json(paths["fund_output"], fund_products)

    summary = {
        "wealth": {
            "count": len(wealth_products),
            "failed": len(wealth_failures),
            "failures": wealth_failures,
            "output": str(paths["wealth_output"]),
        },
        "fund": {
            "count": len(fund_products),
            "failed": len(fund_failures),
            "failures": fund_failures,
            "output": str(paths["fund_output"]),
        },
    }

    publish_outputs(paths)
    return summary


def to_json(obj: Dict) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)

from __future__ import annotations

import os
from pathlib import Path

from .config import (
    DEFAULT_FUND_LINKS,
    DEFAULT_FUND_OUTPUT,
    DEFAULT_WEALTH_LINKS,
    DEFAULT_WEALTH_OUTPUT,
)
from .scraper import load_links, scrape_all, write_json


def lambda_handler(event, context):
    wealth_links_path = Path(os.environ.get("WEALTH_LINKS_PATH", DEFAULT_WEALTH_LINKS))
    wealth_output_path = Path(os.environ.get("WEALTH_OUTPUT_PATH", "/tmp/wealth.json"))
    fund_links_path = Path(os.environ.get("FUND_LINKS_PATH", DEFAULT_FUND_LINKS))
    fund_output_path = Path(os.environ.get("FUND_OUTPUT_PATH", "/tmp/fund.json"))

    wealth_urls = load_links(wealth_links_path)
    wealth_products, wealth_failures = scrape_all(wealth_urls)
    write_json(wealth_output_path, wealth_products)

    fund_urls = load_links(fund_links_path)
    fund_products, fund_failures = scrape_all(fund_urls)
    write_json(fund_output_path, fund_products)

    return {
        "wealth": {
            "count": len(wealth_products),
            "failed": len(wealth_failures),
            "failures": [{"url": url, "error": err} for url, err in wealth_failures],
            "output": str(wealth_output_path),
        },
        "fund": {
            "count": len(fund_products),
            "failed": len(fund_failures),
            "failures": [{"url": url, "error": err} for url, err in fund_failures],
            "output": str(fund_output_path),
        },
    }

from __future__ import annotations

import argparse
from pathlib import Path

from .config import (
    DEFAULT_FUND_LINKS,
    DEFAULT_FUND_OUTPUT,
    DEFAULT_WEALTH_LINKS,
    DEFAULT_WEALTH_OUTPUT,
)
from .scraper import load_links, scrape_all, write_json


def _scrape_one(label: str, links_path: Path, output_path: Path) -> None:
    urls = load_links(links_path)
    if not urls:
        print(f"[{label}] no urls in {links_path}, skip")
        return
    products, failures = scrape_all(urls)
    write_json(output_path, products)
    total = len(urls)
    success = len(products)
    failed = len(failures)
    print(f"[{label}] wrote {success} products to {output_path}")
    print(f"[{label}] summary: {success}/{total} succeeded, {failed} failed")
    if failures:
        for url, reason in failures:
            print(f"- FAIL {url} :: {reason}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape wealth/fund product data.")

    parser.add_argument("--wealth-links", type=Path, default=DEFAULT_WEALTH_LINKS, help="Path to wealth_links.txt")
    parser.add_argument("--wealth-output", type=Path, default=DEFAULT_WEALTH_OUTPUT, help="Output JSON path for wealth products")
    parser.add_argument("--fund-links", type=Path, default=DEFAULT_FUND_LINKS, help="Path to fund_links.txt")
    parser.add_argument("--fund-output", type=Path, default=DEFAULT_FUND_OUTPUT, help="Output JSON path for fund products")

    args = parser.parse_args()

    _scrape_one("wealth", args.wealth_links, args.wealth_output)
    _scrape_one("fund", args.fund_links, args.fund_output)
    return 0

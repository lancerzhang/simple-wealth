from __future__ import annotations

import argparse
from pathlib import Path

from .config import DEFAULT_LINKS, DEFAULT_OUTPUT
from .scraper import load_links, scrape_all, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape wealth product data.")
    parser.add_argument("--links", type=Path, default=DEFAULT_LINKS, help="Path to product_links.txt")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output JSON path")
    args = parser.parse_args()

    urls = load_links(args.links)
    products, failures = scrape_all(urls)
    write_json(args.output, products)
    total = len(urls)
    success = len(products)
    failed = len(failures)
    print(f"Wrote {success} products to {args.output}")
    print(f"Summary: {success}/{total} succeeded, {failed} failed")
    if failures:
        for url, reason in failures:
            print(f"- FAIL {url} :: {reason}")
    return 0

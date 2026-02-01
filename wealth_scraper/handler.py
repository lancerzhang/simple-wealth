from __future__ import annotations

import os
from pathlib import Path

from .config import DEFAULT_LINKS
from .scraper import load_links, scrape_all, write_json


def lambda_handler(event, context):
    links_path = Path(os.environ.get("WEALTH_LINKS_PATH", DEFAULT_LINKS))
    output_path = Path(os.environ.get("WEALTH_OUTPUT_PATH", "/tmp/wealth.json"))
    urls = load_links(links_path)
    products, failures = scrape_all(urls)
    write_json(output_path, products)
    return {
        "count": len(products),
        "failed": len(failures),
        "failures": [{"url": url, "error": err} for url, err in failures],
        "output": str(output_path),
    }

#!/usr/bin/env python3
"""CLI entry that also serves cloud handlers (Aliyun FC / AWS Lambda)."""

from __future__ import annotations

import argparse
import json
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from wealth_scraper.config import (
    DEFAULT_FUND_LINKS,
    DEFAULT_FUND_OUTPUT,
    DEFAULT_WEALTH_LINKS,
    DEFAULT_WEALTH_OUTPUT,
)
from wealth_scraper.run import run_scrape, to_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape wealth/fund products and write JSON outputs.")
    parser.add_argument("--wealth-links", type=Path, default=DEFAULT_WEALTH_LINKS, help="Path to wealth_links.txt")
    parser.add_argument("--fund-links", type=Path, default=DEFAULT_FUND_LINKS, help="Path to fund_links.txt")
    parser.add_argument("--wealth-output", type=Path, default=DEFAULT_WEALTH_OUTPUT, help="Output JSON path for wealth products")
    parser.add_argument("--fund-output", type=Path, default=DEFAULT_FUND_OUTPUT, help="Output JSON path for fund products")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    summary = run_scrape(
        wealth_links=args.wealth_links,
        fund_links=args.fund_links,
        wealth_output=args.wealth_output,
        fund_output=args.fund_output,
    )
    print(to_json(summary))
    return 0


# Aliyun FC handler
def handler(event, context):  # noqa: N802 - FC expects this name
    # event may be JSON string or dict
    try:
        if isinstance(event, str):
            event_obj = json.loads(event) if event else {}
        else:
            event_obj = event or {}
    except Exception:
        event_obj = {}

    wealth_links = event_obj.get("wealth_links") or os.environ.get("WEALTH_LINKS_PATH") or DEFAULT_WEALTH_LINKS
    fund_links = event_obj.get("fund_links") or os.environ.get("FUND_LINKS_PATH") or DEFAULT_FUND_LINKS
    wealth_output = event_obj.get("wealth_output") or os.environ.get("WEALTH_OUTPUT_PATH") or DEFAULT_WEALTH_OUTPUT
    fund_output = event_obj.get("fund_output") or os.environ.get("FUND_OUTPUT_PATH") or DEFAULT_FUND_OUTPUT

    summary = run_scrape(
        wealth_links=wealth_links,
        fund_links=fund_links,
        wealth_output=wealth_output,
        fund_output=fund_output,
    )
    return summary


# AWS Lambda handler (keep separate name)
def lambda_handler(event, context):
    evt = event or {}
    wealth_links = evt.get("wealth_links") or os.environ.get("WEALTH_LINKS_PATH") or DEFAULT_WEALTH_LINKS
    fund_links = evt.get("fund_links") or os.environ.get("FUND_LINKS_PATH") or DEFAULT_FUND_LINKS
    wealth_output = evt.get("wealth_output") or os.environ.get("WEALTH_OUTPUT_PATH") or DEFAULT_WEALTH_OUTPUT
    fund_output = evt.get("fund_output") or os.environ.get("FUND_OUTPUT_PATH") or DEFAULT_FUND_OUTPUT

    summary = run_scrape(
        wealth_links=wealth_links,
        fund_links=fund_links,
        wealth_output=wealth_output,
        fund_output=fund_output,
    )
    return summary


if __name__ == "__main__":
    raise SystemExit(main())

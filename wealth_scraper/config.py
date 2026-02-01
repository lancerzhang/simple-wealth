from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_LINKS = ROOT_DIR / "data" / "product_links.txt"
DEFAULT_OUTPUT = ROOT_DIR / "frontend" / "public" / "data" / "wealth.json"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

WEALTHCCB_BANKS = ["建设银行"]
WEALTHCCB_ISSUER = "建信理财"

BOCOMM_MIN_HOLD_OVERRIDES = {
    "5811225149": 90,
    "5811225495": 1,
}
BOCOMM_BANK_OVERRIDES = {
    "5811225149": ["建设银行", "交通银行"],
    "5811225495": ["交通银行"],
}
BOCOMM_CODE_OVERRIDES = {
    "5811225495": "5811225495",
}

SPDB_MIN_HOLD_DAYS = 90
SPDB_BANKS = ["交通银行"]
SPDB_ISSUER = "浦银理财"

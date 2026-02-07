from __future__ import annotations

from pathlib import Path

PYTHON_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[2]

# Data files
DEFAULT_WEALTH_LINKS = PYTHON_DIR / "data" / "wealth_links.txt"
DEFAULT_FUND_LINKS = PYTHON_DIR / "data" / "fund_links.txt"

# Outputs
DEFAULT_WEALTH_OUTPUT = REPO_ROOT / "frontend" / "public" / "data" / "wealth.json"
DEFAULT_FUND_OUTPUT = REPO_ROOT / "frontend" / "public" / "data" / "fund.json"

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

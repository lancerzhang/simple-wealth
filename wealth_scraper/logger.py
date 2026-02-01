from __future__ import annotations

import os
import sys


def debug_log(message: str) -> None:
    if os.environ.get("WEALTH_DEBUG") == "1":
        print(message, file=sys.stderr, flush=True)

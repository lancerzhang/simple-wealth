from __future__ import annotations

import datetime as dt
import unittest

from python.wealth_scraper.providers.chinawealth import _build_nav_series, _parse_risk_level
from python.wealth_scraper.utils import compute_window_return_with_details


class ChinawealthProviderTests(unittest.TestCase):
    def test_parse_risk_level_prefers_specific_mid_low_match(self) -> None:
        self.assertEqual(_parse_risk_level("二级(中低)"), "R2")

    def test_build_nav_series_ignores_pre_inception_stale_points(self) -> None:
        net_items = [
            {
                "subShareCode": "FBAE60132N",
                "netValueDate": "2023-03-02",
                "shareNetVal": "1.0356",
            },
            {
                "subShareCode": "FBAE60132N",
                "netValueDate": "2026-02-10",
                "shareNetVal": "1.0343",
            },
            {
                "subShareCode": "FBAE60132N",
                "netValueDate": "2026-03-06",
                "shareNetVal": "1.0360",
            },
            {
                "subShareCode": "FBAE60132F",
                "netValueDate": "2026-03-06",
                "shareNetVal": "9.9999",
            },
        ]

        series = _build_nav_series(
            net_items,
            sub_share_code="FBAE60132N",
            min_date=dt.date(2025, 3, 20),
        )

        self.assertEqual(
            series,
            [
                (dt.date(2026, 2, 10), 1.0343),
                (dt.date(2026, 3, 6), 1.0360),
            ],
        )

        annualized, start_date, _, end_date, _ = compute_window_return_with_details(series, 30)

        self.assertEqual(start_date, dt.date(2026, 2, 10))
        self.assertEqual(end_date, dt.date(2026, 3, 6))
        self.assertIsNotNone(annualized)
        self.assertGreater(annualized, 2.0)
        self.assertLess(annualized, 3.0)


if __name__ == "__main__":
    unittest.main()

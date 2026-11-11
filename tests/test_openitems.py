import datetime as dt
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
import openitems  # noqa: E402

D = dt.date


def L(d, v, amt):
    return {"date": d, "voucher": v, "amount": amt, "description": v}


class FifoTest(unittest.TestCase):
    def test_partial_clear_oldest_first(self):
        q, un = openitems.fifo_open_items(
            [L(D(2026, 1, 1), "A", 100), L(D(2026, 2, 1), "B", 50), L(D(2026, 3, 1), "C", 30),
             L(D(2026, 3, 5), "X", -120)], "debit")
        self.assertEqual([(i["voucher"], i["open"]) for i in q], [("B", 30), ("C", 30)])
        self.assertEqual(un, 0)

    def test_credit_side(self):
        q, _ = openitems.fifo_open_items([L(D(2026, 1, 1), "R1", -500), L(D(2026, 1, 9), "M", 200)], "credit")
        self.assertEqual([(i["voucher"], i["open"]) for i in q], [("R1", 300)])

    def test_over_clear_carries(self):
        q, un = openitems.fifo_open_items([L(D(2026, 1, 1), "A", 10), L(D(2026, 1, 2), "X", -15),
                                           L(D(2026, 1, 3), "B", 20)], "debit")
        self.assertEqual([(i["voucher"], i["open"]) for i in q], [("B", 15)])
        self.assertEqual(un, 0)

    def test_levels(self):
        r = {"warn_days": 120, "crit_days": 150, "hard_limit_days": 180}
        self.assertEqual([openitems.level(a, r) for a in (119, 120, 149, 150, 179, 180)],
                         ["ok", "warn", "warn", "crit", "crit", "over"])


class SampleTieTest(unittest.TestCase):
    def test_sample_ties_to_gl(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        res = openitems.build(os.path.join(root, "data", "ledger_sample.csv"),
                              os.path.join(root, "config", "openitems_rules.json"))
        self.assertEqual(res["errors"], [])
        self.assertTrue(all(a["tie"] for a in res["accounts"]))


if __name__ == "__main__":
    unittest.main()

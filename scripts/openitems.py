"""คำนวณรายการค้าง (open items) แบบ FIFO ต่อบัญชี ตามกฎใน config/openitems_rules.json

    python scripts/openitems.py                       # → docs/data/openitems.json
    python scripts/openitems.py --ledger x.csv --asof 2026-11-11 --out out.json

ledger CSV ต้องมีคอลัมน์: date (YYYY-MM-DD) · voucher · account · amount (+ = เดบิต, − = เครดิต) · description
ใช้ Python มาตรฐานอย่างเดียว ไม่ต้องติดตั้งอะไรเพิ่ม
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUCKETS = [("0-30", 0, 30), ("31-90", 31, 90), ("91-180", 91, 180), ("181+", 181, 10 ** 6)]


def load_ledger(path):
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["date"] = dt.date.fromisoformat(r["date"])
        r["amount"] = round(float(r["amount"]), 2)
        r["account"] = str(r["account"]).strip()
    return rows


def fifo_open_items(lines, side):
    """lines: รายการของบัญชีเดียว · side: 'debit' หรือ 'credit' (ฝั่งที่ทำให้ยอดเพิ่ม)
    คืนรายการตั้งที่ยังค้าง: [{date, voucher, description, orig, open}] — เคลียร์เก่าสุดก่อน"""
    sign = 1 if side == "debit" else -1
    queue = []        # รายการตั้งที่ยังค้าง เรียงตามวันที่
    unapplied = 0.0   # เคลียร์เกินกว่ายอดตั้ง (ยอดกลับข้าง) — เก็บไว้ตัดรายการตั้งถัดไป
    for ln in sorted(lines, key=lambda x: (x["date"], x["voucher"])):
        amt = round(ln["amount"] * sign, 2)
        if amt > 0:
            item = {"date": ln["date"], "voucher": ln["voucher"], "description": ln["description"],
                    "orig": amt, "open": amt}
            if unapplied > 0:
                use = min(unapplied, item["open"])
                item["open"] = round(item["open"] - use, 2)
                unapplied = round(unapplied - use, 2)
            if item["open"] > 0:
                queue.append(item)
        elif amt < 0:
            clear = -amt
            while clear > 0 and queue:
                use = min(clear, queue[0]["open"])
                queue[0]["open"] = round(queue[0]["open"] - use, 2)
                clear = round(clear - use, 2)
                if queue[0]["open"] <= 0:
                    queue.pop(0)
            unapplied = round(unapplied + clear, 2)
    return queue, unapplied


def level(age, rule):
    if rule.get("hard_limit_days") and age >= rule["hard_limit_days"]:
        return "over"
    if age >= rule["crit_days"]:
        return "crit"
    if age >= rule["warn_days"]:
        return "warn"
    return "ok"


def build(ledger_path, rules_path, asof=None):
    with open(rules_path, encoding="utf-8") as f:
        rules = json.load(f)
    ledger = load_ledger(ledger_path)
    asof = asof or max(r["date"] for r in ledger)
    by_acct = defaultdict(list)
    for r in ledger:
        if r["date"] <= asof:
            by_acct[r["account"]].append(r)

    accounts, items, errors = [], [], []
    for rule in rules["rules"]:
        lines = by_acct.get(rule["acct"], [])
        sign = 1 if rule["side"] == "debit" else -1
        gl = round(sum(l["amount"] for l in lines), 2)
        queue, unapplied = fifo_open_items(lines, rule["side"])
        open_total = round(sum(q["open"] for q in queue) - unapplied, 2)
        tie = abs(open_total - gl * sign) < 0.01            # gate: ยอดค้างรวม = ยอด GL
        if not tie:
            errors.append(f"{rule['acct']}: open {open_total:,.2f} ≠ GL {gl * sign:,.2f}")
        bucket = {b[0]: 0.0 for b in BUCKETS}
        counts = defaultdict(int)
        for q in queue:
            age = (asof - q["date"]).days
            for name, lo, hi in BUCKETS:
                if lo <= age <= hi:
                    bucket[name] = round(bucket[name] + q["open"], 2)
            lv = level(age, rule)
            if q["open"] >= rules.get("min_amount", 0):
                counts[lv] += 1
                items.append({"acct": rule["acct"], "voucher": q["voucher"], "date": q["date"].isoformat(),
                              "ageDays": age, "orig": q["orig"], "open": q["open"],
                              "desc": q["description"], "level": lv})
        accounts.append({"acct": rule["acct"], "name": rule["name"], "side": rule["side"],
                         "glBalance": gl, "openTotal": open_total, "tie": tie,
                         "unapplied": unapplied, "buckets": bucket,
                         "nWarn": counts["warn"], "nCrit": counts["crit"], "nOver": counts["over"],
                         "warnDays": rule["warn_days"], "critDays": rule["crit_days"],
                         "hardLimitDays": rule.get("hard_limit_days"),
                         "why": rule.get("why", ""), "action": rule.get("action", ""),
                         "owner": rule.get("owner", "")})
    order = {"over": 0, "crit": 1, "warn": 2, "ok": 3}
    items.sort(key=lambda x: (order[x["level"]], -x["ageDays"]))
    return {"asOf": asof.isoformat(), "generated": dt.datetime.now().isoformat(timespec="seconds"),
            "sample": True, "accounts": accounts, "items": items, "errors": errors}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", default=os.path.join(ROOT, "data", "ledger_sample.csv"))
    ap.add_argument("--rules", default=os.path.join(ROOT, "config", "openitems_rules.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "data", "openitems.json"))
    ap.add_argument("--asof", help="YYYY-MM-DD (ค่าเริ่มต้น = วันที่ล่าสุดใน ledger)")
    a = ap.parse_args(argv)
    res = build(a.ledger, a.rules, dt.date.fromisoformat(a.asof) if a.asof else None)
    if res["errors"]:
        print("❌ ยอดไม่ tie กับ GL — ไม่เขียนไฟล์:\n  " + "\n  ".join(res["errors"]))
        return 1
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    for x in res["accounts"]:
        print(f"{x['acct']} {x['name'][:28]:<28} ค้าง {x['openTotal']:>13,.2f}  "
              f"⚠️{x['nWarn']} 🔴{x['nCrit']} ⛔{x['nOver']}  tie={'✅' if x['tie'] else '❌'}")
    print(f"→ {a.out} (asOf {res['asOf']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

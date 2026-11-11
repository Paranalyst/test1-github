"""สร้างเนื้อหา GitHub Issue รายสัปดาห์จาก docs/data/openitems.json

    python scripts/weekly_alert.py > issue.md     # exit 3 = ไม่มีอะไรต้องเตือน (ไม่ต้องเปิด issue)
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON = {"over": "⛔", "crit": "🔴", "warn": "⚠️"}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "docs", "data", "openitems.json")
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    with open(os.path.join(ROOT, "config", "openitems_rules.json"), encoding="utf-8") as f:
        rules = json.load(f)
    hot = [i for i in d["items"] if i["level"] in ("over", "crit", "warn")]
    if not hot:
        return 3
    page = os.environ.get("PAGE_URL", "")
    out = [f"ข้อมูล ณ **{d['asOf']}**" + (" · ⚠️ ข้อมูลตัวอย่าง (แต่งขึ้น)" if d.get("sample") else ""),
           f"ดูทั้งหมด: {page}" if page else "", "",
           "| บัญชี | ยอดค้าง | ⚠️ | 🔴 | ⛔ | ต้องทำ |", "|---|---:|---:|---:|---:|---|"]
    for a in d["accounts"]:
        out.append(f"| {a['acct']} {a['name']} | {a['openTotal']:,.2f} | {a['nWarn']} | {a['nCrit']} | {a['nOver']} | {a['action']} |")
    names = {a["acct"]: a for a in d["accounts"]}
    for acct in sorted({i["acct"] for i in hot}):
        a = names[acct]
        owners = " ".join("@" + h for h in rules.get("owners", {}).get(a["owner"], []))
        out += ["", f"### {acct} {a['name']} {owners}".rstrip(), f"_{a['why']}_"]
        for i in [x for x in hot if x["acct"] == acct]:
            out.append(f"- [ ] {ICON[i['level']]} `{i['voucher']}` {i['date']} · ค้าง {i['ageDays']} วัน · "
                       f"฿{i['open']:,.2f} — {i['desc']}")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

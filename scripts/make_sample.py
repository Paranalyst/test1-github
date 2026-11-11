"""สร้าง ledger ตัวอย่าง (ข้อมูลแต่งขึ้นทั้งหมด — ไม่ใช่ข้อมูลจริงของบริษัทใด)

    python scripts/make_sample.py            # เขียน data/ledger_sample.csv
"""
import csv
import datetime as dt
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "ledger_sample.csv")
ASOF = dt.date(2026, 11, 11)
random.seed(42)

VENDORS = ["บริษัท ตัวอย่าง จำกัด", "ร้าน สมมติ", "บริษัท ทดลอง เทรดดิ้ง", "หจก. เดโม่ ซัพพลาย",
           "บริษัท แซมเปิล โลจิสติกส์", "บริษัท ฝึกหัด ซอฟต์แวร์"]
STAFF = ["พนักงาน A", "พนักงาน B", "พนักงาน C", "พนักงาน D"]
CUSTOMERS = ["ลูกค้า Alpha", "ลูกค้า Beta", "ลูกค้า Gamma", "ลูกค้า Delta"]

rows = []
seq = {"DN": 0, "GPP": 0, "JV": 0, "PV": 0, "RV": 0}


def vno(prefix, d):
    seq[prefix] += 1
    return f"{prefix}{d:%y%m}-{seq[prefix]:03d}"


def add(d, voucher, acct, amt, desc):
    rows.append({"date": d.isoformat(), "voucher": voucher, "account": acct, "amount": round(amt, 2), "description": desc})


def day(back_min, back_max):
    return ASOF - dt.timedelta(days=random.randint(back_min, back_max))


# 137006 ภาษีซื้อยังไม่ถึงกำหนด (VATU): ตั้งตอน DN · ย้ายเข้า 137005 ตอนได้ใบกำกับ (GPP) — บางใบไม่เคยได้
for i in range(40):
    d = day(125, 200) if i < 5 else day(5, 260)          # 5 ใบแรก: ตั้งใจให้ค้างนานเพื่อสาธิตการเตือน
    vat = round(random.uniform(500, 25000), 2)
    v = random.choice(VENDORS)
    dn = vno("DN", d)
    add(d, dn, "137006", vat, f"ภาษีซื้อรอใบกำกับ {dn} - {v}")
    if i >= 5 and random.random() < 0.7:
        d2 = d + dt.timedelta(days=random.randint(10, 60))
        if d2 <= ASOF:
            add(d2, vno("GPP", d2), "137006", -vat, f"ได้ใบกำกับ {dn} ย้ายเข้า 137005 - {v}")

# 137013 พักภาษีนำเข้า
for i in range(6):
    d = day(3, 90)
    amt = round(random.uniform(5000, 90000), 2)
    dn = vno("DN", d)
    add(d, dn, "137013", amt, f"ภาษีนำเข้า {dn} - บริษัท ชิปปิ้ง สมมติ")
    if random.random() < 0.5:
        d2 = d + dt.timedelta(days=random.randint(5, 20))
        if d2 <= ASOF:
            add(d2, vno("JV", d2), "137013", -amt, f"ย้ายภาษีนำเข้า {dn} เข้า 137005")

# 134002 ทดรองจ่ายพนักงาน
for i in range(15):
    d = day(1, 120)
    amt = round(random.uniform(300, 8000), 2)
    s = random.choice(STAFF)
    pv = vno("PV", d)
    add(d, pv, "134002", amt, f"ทดรองจ่าย {s} {pv}")
    if random.random() < 0.6:
        d2 = d + dt.timedelta(days=random.randint(3, 40))
        if d2 <= ASOF:
            add(d2, vno("JV", d2), "134002", -amt, f"เคลียร์ทดรอง {s} {pv}")

# 154004 มัดจำระยะสั้น
for i in range(8):
    d = day(100, 420) if i < 2 else day(10, 500)
    amt = round(random.uniform(2000, 50000), 2)
    v = random.choice(VENDORS)
    dn = vno("DN", d)
    add(d, dn, "154004", amt, f"เงินมัดจำ {dn} - {v}")
    if i >= 2 and random.random() < 0.4:
        d2 = d + dt.timedelta(days=random.randint(20, 120))
        if d2 <= ASOF:
            add(d2, vno("RV", d2), "154004", -amt, f"รับคืนมัดจำ {dn} - {v}")

# 211313 เงินรับลูกค้ายังไม่ระบุ (ฝั่งเครดิต)
for i in range(12):
    d = day(1, 75)
    amt = round(random.uniform(1000, 120000), 2)
    c = random.choice(CUSTOMERS)
    rv = vno("RV", d)
    add(d, rv, "211313", -amt, f"เงินโอนเข้ายังไม่ระบุ {rv} ({c}?)")
    if random.random() < 0.55:
        d2 = d + dt.timedelta(days=random.randint(2, 25))
        if d2 <= ASOF:
            add(d2, vno("JV", d2), "211313", amt, f"จับคู่ invoice {rv} - {c}")

rows.sort(key=lambda r: (r["date"], r["voucher"]))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["date", "voucher", "account", "amount", "description"])
    w.writeheader()
    w.writerows(rows)
print(f"wrote {len(rows)} rows → {OUT}")

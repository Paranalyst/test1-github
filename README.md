# 🔔 Open-items alert — โปรเจกต์ฝึก

ระบบแจ้งเตือน **บัญชีค้าง** (เงินทดรอง · ภาษีซื้อรอใบกำกับ · มัดจำ · เงินรับยังไม่ระบุ ฯลฯ)
คำนวณอายุรายการแบบ FIFO → หน้าเว็บ (GitHub Pages) → GitHub Issue ทุกวันจันทร์

> ⚠️ **ข้อมูลใน `data/ledger_sample.csv` แต่งขึ้นทั้งหมด** — ห้ามใส่ข้อมูลจริงของบริษัทใน repo นี้
> (GitHub Pages ของ account ฟรีเปิดสาธารณะเสมอ แม้ repo เป็น private)

## โครงสร้าง

```
config/openitems_rules.json     กฎต่อบัญชี: กี่วันเตือน / วิกฤต / เพดาน · ต้องทำอะไร · ใครดูแล   ← แก้ตรงนี้
data/ledger_sample.csv          ledger ตัวอย่าง (date, voucher, account, amount ±, description)
scripts/make_sample.py          สร้าง ledger ตัวอย่างใหม่
scripts/openitems.py            คำนวณ → docs/data/openitems.json (ยอดค้างรวมต้อง = ยอด GL ไม่งั้นไม่เขียนไฟล์)
scripts/weekly_alert.py         สร้างเนื้อหา issue รายสัปดาห์
docs/index.html                 หน้าเว็บ (อ่าน docs/data/openitems.json)
tests/test_openitems.py         ทดสอบ FIFO · ระดับเตือน · tie GL
.github/workflows/
  build-and-deploy.yml          push / ทุกวัน 06:30 → test → build → deploy GitHub Pages
  weekly-alert.yml              ทุกจันทร์ 08:40 → เปิด issue "🔔 บัญชีค้าง YYYY-Www" (ปิดของสัปดาห์ก่อน)
```

## ติดตั้งบน GitHub (ทำครั้งเดียว ผ่านหน้าเว็บ)

1. เปิด repo (เช่น `Paranalyst/test1-github`) → **Add file → Upload files** → ลากทุกไฟล์/โฟลเดอร์จาก zip นี้ลงไป → **Commit changes**
   - โฟลเดอร์ `.github` เป็นโฟลเดอร์ซ่อน — ถ้าลากไม่ติด ให้สร้างไฟล์เองด้วย **Add file → Create new file** ตั้งชื่อ `.github/workflows/build-and-deploy.yml` แล้ววางเนื้อหา (ทำแบบเดียวกันกับ `weekly-alert.yml`)
2. **Settings → Pages → Build and deployment → Source: GitHub Actions**
3. **Actions** → เลือก "Build open items → GitHub Pages" → **Run workflow** → รอเขียว
4. เปิดหน้าเว็บที่ `https://<username>.github.io/<repo>/`
5. ลองแจ้งเตือน: **Actions → Weekly open-items alert → Run workflow** → ไปดูแท็บ **Issues**

## ลองแก้ดู

| อยากลอง | ทำที่ |
|---|---|
| เปลี่ยนกี่วันถึงเตือน | `config/openitems_rules.json` → `warn_days` / `crit_days` → commit → เว็บอัปเดตเอง |
| ให้ issue แท็กคน | `owners` → `{"ap": ["github-username"]}` |
| เพิ่มบัญชีใหม่ | เพิ่ม object ใน `rules` + มีรายการบัญชีนั้นใน ledger |
| ทดสอบในเครื่อง | `python scripts/openitems.py` · `python -m unittest discover -s tests -v` · `python -m http.server -d docs` |

## ข้อจำกัดของ FIFO (สิ่งที่จะเห็นในข้อมูลตัวอย่าง)

FIFO เอารายการเคลียร์ไปตัด **รายการตั้งเก่าสุดก่อน** เสมอ — ถ้าจริง ๆ คนเคลียร์ใบใหม่ (เช่น ได้ใบกำกับของเดือนล่าสุดก่อน)
ใบเก่าจะดู "เคลียร์แล้ว" ทั้งที่ยังค้าง → ระบบจริงควรจับคู่ด้วยเลขเอกสารก่อน (เช่น `DN2607-005` อยู่ทั้งในบรรทัดตั้งและบรรทัดเคลียร์) แล้วค่อย FIFO ส่วนที่เหลือ
→ ลองเขียนเพิ่มเป็นแบบฝึกหัดถัดไป

## ย้ายไปใช้ของจริง

เมื่อพร้อม ย้ายโค้ดเข้า repo ของบริษัท (ตามเอกสารออกแบบ `open-items-alert-design`) — อ่านข้อมูลจาก warehouse แทน CSV และแสดงหน้าเว็บหลังระบบ login ของบริษัท **ไม่ใช่** GitHub Pages

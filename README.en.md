# Korean Delivery-App P&L Agent (baedal-pnl)

[한국어](README.md) · **English**

[![CI](https://github.com/yuneunmi814-cmyk/baedal-pnl/actions/workflows/ci.yml/badge.svg)](https://github.com/yuneunmi814-cmyk/baedal-pnl/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![platforms](https://img.shields.io/badge/Baemin·CoupangEats·Yogiyo-settlement%20parsing-FF6B00)

> **Upload settlement Excel files from Korea's food-delivery apps (배민 Baemin, 쿠팡이츠
> Coupang Eats, 요기요 Yogiyo) and get an income statement (down to net income) plus a
> VAT settlement by tax type — automatically.**
> Turns the monthly "so how much did I actually make?" spreadsheet grind into one minute.

![demo](docs/demo.gif)

*(Synthetic demo data — not real settlement values.)*

---

## ⚡ Try it in 5 minutes

**No delivery-app files? No problem** — a sample file is included so you can see output right away.

### 0. Prerequisite — Python 3.10+
```bash
python3 --version      # e.g. Python 3.11.x  (3.10 or newer)
```
> Don't have it? Install from [python.org](https://www.python.org/downloads/) and re-check.

### 1. Get the code
```bash
git clone https://github.com/yuneunmi814-cmyk/baedal-pnl.git
cd baedal-pnl
```
> No Git? Use **Code ▾ → Download ZIP** on the GitHub page and unzip.

### 2. Install (virtual env recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate      # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

### 3. Run it on the sample file 👇
```bash
python run_cli.py data/_FAKE_yogiyo_sample.xlsx
```
An income statement prints right in your terminal:
```
손익계산서 (2026-05)  [일반과세자]   # Income Statement (general taxpayer)
============================================
Ⅰ. 매출액 (Revenue)                      66,364
Ⅴ. 영업이익 (Operating profit)           45,800
Ⅹ. 당기순이익 (Net income)               45,800
--------------------------------------------
VAT  output 6,636 · input 1,856 · payable 4,780
```
> An Excel file `손익계산서.xlsx` is saved in the same folder too. 🎉 **If you got here, it works.**

### 4. Use the web UI (drag & drop)
```bash
uvicorn app.main:app --port 8077
```
Open **http://127.0.0.1:8077**, drop a file, click **[생성 / Generate]**.
(Try uploading `data/_FAKE_yogiyo_sample.xlsx`.)

### 5. Now with your real files
- **Coupang Eats**: download the settlement Excel from the merchant portal and upload as-is.
- **Baemin**: the settlement file is **password-protected** — enter the password in the UI field (it differs per file).
- Upload **multiple files / platforms at once** → they merge into one combined statement.
- Add **food cost, labor, rent** (not in the files) via the manual-input fields to reach net income.

---

## 🛠️ Troubleshooting

| Symptom | Fix |
|---|---|
| `command not found: python3` | Install Python from [python.org](https://www.python.org/downloads/) |
| `pip install` hangs/fails | `pip install --upgrade pip`, then retry |
| `Address already in use` | Use another port: `uvicorn app.main:app --port 9000` |
| Baemin file shows "처리 실패" (failed) | It's encrypted → enter the password in the UI field |
| Items lumped into "기타비용" (misc.) | New line-item name → add one line to `app/classify/rules.py` |
| Do I need Ollama (LLM)? | **No, it's optional.** Rule-based classification works without it |

---

## What it does

Reads each platform's messy settlement Excel (fees, delivery, ads, discounts, VAT…) and turns it into a **standard income statement**.

```
Upload settlement Excel
   ├─ ① auto-detect which platform
   ├─ ② parse hidden fee/discount columns precisely
   ├─ ③ classify each item into an account (rules + LLM only for the fuzzy ones)
   ├─ ④ merge multiple files/periods
   ├─ ⑤ split VAT by tax type
   └─ ⑥ income statement (net income) + Excel export
```

**Design philosophy:** numbers come from **deterministic code (pandas)**; only the fuzzy
"what account is this?" mapping uses a **local LLM (Ollama)** — so the numbers never drift.

## Coverage

| Platform | Status |
|---|---|
| 🟢 Coupang Eats | verified on a real file (settlement identity, zero error) |
| 🟢 Baemin | verified on a real file (decrypts password file, per-row reconciliation zero error) |
| 🟡 Yogiyo | adaptive (auto header matching) — self-reconciliation confirms on a real file |

**Tax types:** general (supply-value P&L + VAT settlement) · simplified (reduced rate) · exempt — via `--tax-type` or the UI.

---

<details>
<summary><b>📂 Project layout</b></summary>

```
app/
  importers/  base.py · coupangeats.py · baemin.py · yogiyo.py · registry.py
  classify/   rules.py · llm.py (Ollama fallback) · engine.py
  manual/     inputs.py (COGS / fixed costs / tax manual entry)
  tax/        vat.py (VAT split by tax type)
  report/     aggregate.py · income_statement.py (structure + Excel render)
  main.py     FastAPI: POST /api/generate
static/index.html  upload UI
run_cli.py    CLI
data/_FAKE_yogiyo_sample.xlsx  sample (fake) file
```
</details>

<details>
<summary><b>🧾 VAT handling by tax type</b></summary>

VAT is a pass-through, not P&L. Each row declares a `vat_basis` (gross/supply/exact/none),
and **the file's own VAT columns are used first** (Coupang ads & Baemin "우리가게클릭" =
explicit VAT, Baemin fees = supply value, Coupang bundled fees = 10% estimate).
- **General taxpayer:** P&L at supply value (VAT-excluded); VAT settlement (output − input = payable) shown separately.
- **Simplified taxpayer:** P&L at gross; reduced VAT using the 15% food-service value-added rate.
- **Tax-exempt:** no VAT, gross basis.
- Sanity identity (holds exactly): `exempt operating profit − general operating profit = general VAT payable`.

CLI: `python run_cli.py file.xlsx --tax-type simplified`
</details>

<details>
<summary><b>🔧 CLI options / dev notes</b></summary>

```bash
python run_cli.py baemin.xlsx coupang.xlsx \
  --password BAEMIN_PW --food-cost 6000000 --labor 3500000 \
  --tax-type general --out income_statement.xlsx
```
- References studied: beancount/beangulp (importer skeleton) · smart_importer (classification hook) · billcat-local-llm (local-LLM categorization).
- LLM fallback is optional (`--use-llm` / UI checkbox); without Ollama it safely falls back to "기타비용" (misc. expense).
</details>

<details>
<summary><b>⚠️ Status · known limitations</b></summary>

- ✅ Coupang importer — `settlement = order − service fee (rollup) − ad cost`, zero error.
- ✅ Baemin importer — decrypts CDFV2 file via `msoffcrypto-tool`, parses "상세" sheet; per-row sum = deposit across 66 rows, zero error.
- ⚠️ Yogiyo importer — no real file yet; adaptive synonym matching + self-reconciliation. If it mismatches, only `yogiyo.py`'s `SYNONYMS` need tuning.
- Coupang's "service fee" rollup vs. summed fees differs by ≈0.7% of revenue (a VAT adjustment) — flagged as a warning.
- VAT figures are for management accounting; for actual tax filing, confirm with an accountant / Hometax data.
</details>

## 🤝 Contributing

New platform importers, a one-line classification rule, typo fixes, real-file Yogiyo
verification — **all welcome.** See [**CONTRIBUTING.md**](CONTRIBUTING.md) for a
step-by-step guide. (A new importer is usually just one file!)

## License
MIT — free to use, modify, and distribute.

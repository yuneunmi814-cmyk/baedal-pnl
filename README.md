# 배달앱 손익계산서 Agent (baedal-pnl)

**한국어** · [English](README.en.md)

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![platforms](https://img.shields.io/badge/배민·쿠팡이츠·요기요-정산파싱-FF6B00)

> **배민·쿠팡이츠·요기요 정산 엑셀을 올리면, 손익계산서(당기순이익)와 과세유형별 부가세를 자동으로 만들어 줍니다.**
> 매달 배달앱 정산서를 들여다보며 "이번 달 진짜 얼마 남았지?" 계산하던 일을 1분으로 줄여줍니다.

![demo](docs/demo.gif)

*(가짜 데모 데이터 — 실제 정산값 아님)*

---

## ⚡ 5분 안에 직접 돌려보기

배달앱 파일이 **없어도 괜찮습니다.** 저장소에 들어 있는 예시 파일로 바로 결과를 볼 수 있어요.

### 0. 준비물 — Python 3.10 이상
먼저 설치돼 있는지 확인하세요. 버전 숫자가 나오면 OK입니다.
```bash
python3 --version      # 예: Python 3.11.x  (3.10 이상이면 됨)
```
> 없다면 [python.org](https://www.python.org/downloads/)에서 설치 후 다시 확인하세요.

### 1. 내려받기
```bash
git clone https://github.com/yuneunmi814-cmyk/baedal-pnl.git
cd baedal-pnl
```
> Git이 없다면 GitHub 페이지의 **Code ▾ → Download ZIP** 으로 받아 압축을 풀어도 됩니다.

### 2. 설치 (가상환경 권장)
```bash
python3 -m venv .venv          # 깔끔하게 격리된 공간 생성
source .venv/bin/activate      # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

### 3. 예시 파일로 바로 실행 👇
```bash
python run_cli.py data/_FAKE_yogiyo_sample.xlsx
```
그러면 터미널에 **손익계산서가 바로 출력**됩니다:
```
손익계산서 (2026-05)  [일반과세자]
============================================
Ⅰ. 매출액                               66,364
    · yogiyo                         66,364
...
Ⅴ. 영업이익                              45,800
Ⅹ. 당기순이익                             45,800
--------------------------------------------
부가세 정산  매출세액        6,636
            매입세액        1,856
          납부예상세액        4,780
```
> 같은 폴더에 `손익계산서.xlsx`(엑셀)도 함께 저장됩니다. 🎉 **여기까지 오면 성공입니다.**

### 4. 웹 화면으로 써보기 (드래그&드롭 업로드)
```bash
uvicorn app.main:app --port 8077
```
브라우저에서 **http://127.0.0.1:8077** 접속 → 파일을 끌어다 놓고 **[손익계산서 생성]** 클릭.
(테스트는 `data/_FAKE_yogiyo_sample.xlsx`를 올려보세요.)

### 5. 이제 내 진짜 파일로
- **쿠팡이츠**: 사장님 사이트 → 정산 엑셀 다운로드 → 그대로 업로드
- **배민**: 정산명세서는 **암호가 걸려** 있습니다. 업로드 후 화면의 **비밀번호 칸**에 입력하면 됩니다 (파일마다 다름)
- **여러 파일·여러 플랫폼**을 한 번에 올리면 **하나의 통합 손익계산서**로 합쳐집니다
- **식자재비·인건비·임대료** 등 파일에 없는 항목은 화면의 **수기입력 칸**에 넣으면 당기순이익까지 완성됩니다

---

## 🛠️ 잘 안 될 때 (자주 묻는 문제)

| 증상 | 해결 |
|---|---|
| `command not found: python3` | Python 미설치 → [python.org](https://www.python.org/downloads/)에서 설치 |
| `pip install`이 멈추거나 실패 | `pip install --upgrade pip` 후 다시 시도 |
| `Address already in use` (포트 충돌) | 다른 포트로: `uvicorn app.main:app --port 9000` |
| 배민 파일이 "처리 실패"로 나옴 | 정산명세서는 암호화됨 → 화면 **비밀번호 칸**에 입력 |
| 항목이 "기타비용"으로 뭉뚱그려짐 | 신규 항목명 → `app/classify/rules.py`에 한 줄 추가하면 분류됨 |
| LLM(Ollama) 꼭 필요한가요? | **아니요, 선택사항입니다.** 없으면 규칙 분류만으로 동작합니다 |

---

## 무엇을 해주나요

배달앱마다 제각각인 정산 엑셀(수수료·배달비·광고비·할인·부가세…)을 읽어 **표준 손익계산서**로 정리합니다.

```
정산 엑셀 업로드
   │
   ├─ ① 어느 플랫폼인지 자동 인식
   ├─ ② 엑셀의 숨은 수수료·할인 항목을 정확히 파싱
   ├─ ③ 각 항목을 손익계산서 계정과목으로 분류 (규칙 + 막막한 것만 AI)
   ├─ ④ 여러 파일·기간을 하나로 합산
   ├─ ⑤ 과세유형별 부가세 분리
   └─ ⑥ 손익계산서(당기순이익) + 엑셀 출력
```

**설계 철학:** 숫자는 **결정적 코드(pandas)** 로 정확하게, "이 항목이 무슨 계정이지?" 같은 **막막한 매핑만 로컬 LLM(Ollama)** 으로 — 그래서 숫자가 틀어지지 않습니다.

## 지원 범위

| 플랫폼 | 상태 |
|---|---|
| 🟢 쿠팡이츠 | 실파일 검증 완료 (정산금액 등식 오차 0원) |
| 🟢 배민 | 실파일 검증 완료 (암호 파일 복호화·행별 검산 오차 0원) |
| 🟡 요기요 | 적응형(헤더 자동 매칭) — 실파일 투입 시 자동 검산으로 확인 |

**과세유형:** 일반과세자(공급가액 기준 + 부가세 정산) · 간이과세자(저율) · 면세사업자 — `--tax-type` 또는 화면에서 선택.

---

<details>
<summary><b>🖼️ 정지 화면 (업로드 / 결과)</b></summary>

| 업로드 | 결과 (손익계산서 + 부가세 정산) |
|---|---|
| ![업로드 화면](docs/screenshot-upload.png) | ![결과 화면](docs/screenshot-result.png) |
</details>

<details>
<summary><b>📂 프로젝트 구조</b></summary>

```
app/
  importers/  base.py · coupangeats.py · baemin.py · yogiyo.py · registry.py
  classify/   rules.py(규칙) · llm.py(Ollama 폴백) · engine.py(오케스트레이터)
  manual/     inputs.py(매출원가·고정비·세금 수기입력)
  tax/        vat.py(과세유형별 부가세 분리)
  report/     aggregate.py · income_statement.py(구조 + 엑셀 렌더)
  main.py     FastAPI: POST /api/generate
static/index.html  업로드 UI
run_cli.py    CLI
data/_FAKE_yogiyo_sample.xlsx  예시(가짜) 파일
```
</details>

<details>
<summary><b>🧾 과세유형별 VAT 처리 상세</b></summary>

부가세는 손익이 아니라 통과항목 → 각 거래행이 `vat_basis`(gross/supply/exact/none)를 선언하고,
**파일의 부가세 컬럼을 우선 사용**(쿠팡 광고·배민 우리가게클릭 = 명시값, 배민 수수료 = 공급가액, 쿠팡 번들수수료 = 10% 추정).
- **일반과세자**: 손익을 공급가액(VAT 제외)으로, 부가세 정산(매출세액−매입세액=납부세액) 별도.
- **간이과세자**: 손익 총액, 음식점업 부가가치율 15% 저율 납부세액.
- **면세사업자**: 부가세 없음, 총액.
- 검증 항등식: `면세 영업이익 − 일반 영업이익 = 일반 납부세액` (정확 일치).

CLI 예시: `python run_cli.py 파일.xlsx --tax-type simplified`
</details>

<details>
<summary><b>🔧 CLI 옵션 / 개발 메모</b></summary>

```bash
# 여러 파일 + 수기입력 + 과세유형
python run_cli.py 배민.xlsx 쿠팡.xlsx \
  --password 배민비번 --food-cost 6000000 --labor 3500000 \
  --tax-type general --out 손익계산서.xlsx
```
- 레퍼런스: beancount/beangulp(importer 골격) · smart_importer(분류 hook) · billcat-local-llm(로컬 LLM 분류)
- LLM 폴백은 선택(`--use-llm` / UI 체크박스). Ollama 미기동 시 안전하게 '기타비용'으로 폴백.
</details>

<details>
<summary><b>⚠️ 현재 상태 · 알려진 한계</b></summary>

- ✅ 쿠팡이츠 importer — 실파일 검증. `정산금액 = 주문금액 − 서비스이용료(롤업) − 광고비` 오차 0원.
- ✅ 배민 importer — 암호화(CDFV2) 파일 `msoffcrypto-tool` 복호화 후 '상세' 시트 파싱. 행별 합=입금금액 66건 오차 0원.
- ⚠️ 요기요 importer — 실파일 미확보. 헤더 동의어 매칭 적응형 + 자동 검산(항목합=입금액). 안 맞으면 `yogiyo.py`의 `SYNONYMS`만 조정.
- 쿠팡 서비스이용료(롤업)와 개별수수료 합의 차이(≈매출의 0.7%)는 VAT 조정분 — 경고로 표기.
- **부가세 추정은 경영관리용.** 실제 세무신고는 세무사·홈택스 자료로 확정 권장.
</details>

## 라이선스
MIT — 자유롭게 사용·수정·배포할 수 있습니다.

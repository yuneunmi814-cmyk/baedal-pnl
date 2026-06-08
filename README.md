# 배달앱 손익계산서 Agent (baedal-pnl)

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)
![Ollama](https://img.shields.io/badge/LLM-Ollama-000000?logo=ollama&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)
![platforms](https://img.shields.io/badge/배민·쿠팡이츠·요기요-정산파싱-FF6B00)

배민·쿠팡이츠·요기요 **정산/매출 파일을 업로드하면 자동으로 손익계산서(당기순이익 + 과세유형별 부가세)** 를 만든다.
설계 철학: **숫자는 결정적 코드(pandas/openpyxl)로, 막막한 항목명 매핑만 LLM(Ollama)으로.**

> 레퍼런스: beancount/beangulp(importer 골격) · smart_importer(분류 hook) · billcat-local-llm(로컬 LLM 분류)

## 스크린샷

| 업로드 (파일 + 과세유형 + 수기입력) | 결과 (손익계산서 + 부가세 정산) |
|---|---|
| ![업로드 화면](docs/screenshot-upload.png) | ![결과 화면](docs/screenshot-result.png) |

## 파이프라인
업로드 → ① 플랫폼 식별(`identify`) → ② 선언적 파싱(`extract`) → ③ 규칙 분류(+미매칭만 LLM 폴백)
→ ④ 기간·플랫폼 통합 → ⑤ 과세유형별 부가세 분리 → ⑥ 손익계산서 + 엑셀 출력

## 구조
```
app/
  importers/  base.py · coupangeats.py · baemin.py · registry.py
  classify/   rules.py(규칙) · llm.py(Ollama 폴백) · engine.py(오케스트레이터)
  manual/     inputs.py(매출원가·고정비·세금 수기입력)
  tax/        vat.py(과세유형별 부가세 분리)
  report/     aggregate.py · income_statement.py(구조+엑셀렌더)
  main.py     FastAPI: POST /api/generate
static/index.html  업로드 UI
run_cli.py    CLI
```

## 과세유형별 VAT 처리 (`--tax-type general|simplified|exempt`)
부가세는 손익이 아니라 통과항목 → 각 거래행이 `vat_basis`(gross/supply/exact/none)를 선언하고,
**파일의 부가세 컬럼을 우선 사용**(쿠팡 광고·배민 우리가게클릭 = 명시값, 배민 수수료 = 공급가액, 쿠팡 번들수수료 = 10% 추정).
- **일반과세자**: 손익을 공급가액(VAT 제외)으로, 부가세 정산(매출세액−매입세액=납부세액) 별도.
- **간이과세자**: 손익 총액, 음식점업 부가가치율 15% 저율 납부세액.
- **면세사업자**: 부가세 없음, 총액.
- 검증 항등식: `면세 영업이익 − 일반 영업이익 = 일반 납부세액` (정확 일치).

## 실행
```bash
pip install -r requirements.txt

# CLI
python run_cli.py "쿠팡파일.xlsx" --food-cost 6000000 --labor 3500000 --out 손익계산서.xlsx

# 웹 (업로드 UI)
uvicorn app.main:app --reload --port 8077   # http://127.0.0.1:8077
```

## 상태
- ✅ 쿠팡이츠 importer — 2026-05 실파일 검증 완료. `정산금액 = 주문금액 − 서비스이용료(롤업) − 광고비` 오차 0원.
- ✅ 배민 importer — 암호화(CDFV2) 파일 `msoffcrypto-tool` 복호화 후 '상세' 시트 파싱. 행별 합=입금금액 66건 오차 0원. 부가세·만나서결제 현금차감은 P&L 제외.
- ✅ 배민+쿠팡 통합 손익계산서. 비번은 **파일마다 다르므로** 업로드 사용자가 UI에서 입력(`needs_baemin_password` 플래그로 유도).
- ⚠️ 요기요 importer — 실파일 미확보. **헤더 이름(동의어) 매칭 적응형** + 비용부호 자동판별 + **자동 검산(항목합=입금액)**. 실파일 투입 시 `ImportResult.notes`에 '검산 통과/불일치'가 찍혀 즉시 맞는지 확인 가능. 안 맞으면 `yogiyo.py`의 `SYNONYMS`만 조정. (`data/_FAKE_yogiyo_sample.xlsx`는 시연용 가짜 데이터)
- LLM 폴백은 선택(`--use-llm` / UI 체크박스). Ollama 미기동 시 안전하게 '기타비용'으로 폴백.

## 알려진 한계
- 쿠팡 서비스이용료(롤업)와 개별수수료 합의 차이(≈매출의 0.7%)는 **VAT 조정분**. 손익엔 개별수수료 기준으로 계상하고, 정산입금액과의 차이를 경고로 표기.
- 과세유형(일반/간이/면세)별 VAT 분리는 미구현(향후 설정값).

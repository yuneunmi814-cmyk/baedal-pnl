# 기여 가이드 (Contributing)

먼저, 관심 가져주셔서 고맙습니다. 🙇
이 프로젝트는 **자영업 사장님들이 배달앱 정산을 손익계산서로 한눈에 보게** 하려고 만들어졌습니다.
배달앱은 계속 양식을 바꾸고 새 플랫폼도 생기기 때문에, **여러 사람의 손**이 모일수록 정확해집니다.

거창한 기여만 환영하는 게 아닙니다. 아래 전부 **진짜 도움**이 됩니다:

- 오타·어색한 문장 수정, 번역(영문 README) 개선
- "이 파일이 안 열려요" 같은 **버그 리포트**(이슈만 올려도 큰 기여)
- 새로 본 정산 항목명을 분류 규칙에 **한 줄 추가**
- **새 배달앱 importer** 추가 (가장 가치 있는 기여 — 아래 가이드 참고)
- 요기요 importer를 **실파일로 검증**

> 처음이신가요? `good first issue`, `help wanted` 라벨이 붙은 이슈부터 보세요.
> 막히면 **편하게 이슈/Discussion으로 질문**하셔도 됩니다. 답해 드립니다.

---

## 🔒 가장 중요한 규칙 — 실제 정산 데이터를 올리지 마세요

정산 파일에는 **남의 매출·상호 같은 민감정보**가 들어 있습니다.

- 실제 배민/쿠팡/요기요 정산 파일이나, 거기서 나온 **실제 금액이 담긴 결과물**을 커밋·PR·이슈에 올리지 마세요.
- 샘플이 필요하면 `data/_FAKE_yogiyo_sample.xlsx`처럼 **직접 만든 가짜 데이터**를 쓰세요(파일명에 `_FAKE_` 권장).
- 버그 리포트 시 숫자는 **임의의 가짜 값으로 바꿔서** 첨부하세요.
- `.gitignore`가 `data/*.xlsx` 등을 막아두었지만, **습관적으로 한 번 더 확인**해 주세요.

실수로 올렸다면 부끄러워 말고 알려주세요. 함께 정리하면 됩니다.

---

## 개발 환경 세팅 (2분)

[README의 ⚡5분 퀵스타트](README.md#-5분-안에-직접-돌려보기)와 동일합니다.

```bash
git clone https://github.com/<당신_계정>/baedal-pnl.git
cd baedal-pnl
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 동작 확인 (가짜 샘플로 손익계산서가 나오면 OK)
python run_cli.py data/_FAKE_yogiyo_sample.xlsx
```

---

## 🌟 새 배달앱 importer 추가하기 (가장 환영하는 기여)

땡겨요·위메프오 같은 **새 플랫폼**이나, 기존 플랫폼의 **새 양식**을 지원하는 방법입니다.
구조가 단순해서 보통 파일 하나만 추가하면 됩니다.

### 1) `app/importers/`에 importer 파일을 만든다
`app/importers/base.py`의 `DeliveryImporter`를 상속해 **두 메서드만** 구현합니다.

```python
# app/importers/ttenggeo.py  (예: 땡겨요)
import openpyxl, pandas as pd
from .base import DeliveryImporter, ImportResult

class TtenggeoImporter(DeliveryImporter):
    platform = "ttenggeo"
    doc_type = "settlement"

    def identify(self, filepath: str) -> bool:
        # 이 파일이 우리 플랫폼 담당인지 헤더 시그니처로 판별 (True/False)
        ...

    def extract(self, filepath: str) -> ImportResult:
        rows = []  # 정규화된 거래 행 목록
        # 부호 규칙: 매출은 +, 비용은 −
        # vat_basis: gross(총액) | supply(공급가액) | exact(부가세 명시) | none(비과세)
        rows.append(dict(date="2026-05-01", platform=self.platform, doc_type=self.doc_type,
                         order_no="", item_name="땡겨요 주문금액", amount=+10000,
                         vat_basis="gross", vat=0.0))
        rows.append(dict(date="2026-05-01", platform=self.platform, doc_type=self.doc_type,
                         order_no="", item_name="땡겨요 중개이용료", amount=-1000,
                         vat_basis="gross", vat=0.0))
        return ImportResult(platform=self.platform, doc_type=self.doc_type,
                            period="2026-05", rows=pd.DataFrame(rows),
                            payout_reported=...,  # 파일에 적힌 실입금액 (검산용)
                            notes="")
```

- 금액 문자열(`"1,234원"`)은 `self.won(value)`로 숫자 변환하세요(쉼표·원·빈값 처리됨).
- `item_name`은 분류기 입력입니다. "중개", "배달비", "광고" 같은 키워드가 들어가면
  `app/classify/rules.py`가 알아서 계정과목으로 분류합니다.

### 2) `app/importers/registry.py`에 등록
```python
def build_importers(baemin_password=None):
    return [
        CoupangEatsImporter(),
        BaeminImporter(password=baemin_password),
        YogiyoImporter(),
        TtenggeoImporter(),   # ← 추가
    ]
```

### 3) **검산으로 증명** (이 프로젝트의 핵심 원칙)
"동작하는 것 같다"가 아니라 **숫자로 맞다는 걸 보여주세요.**
배달앱 정산은 보통 `매출 − 각종 수수료 = 실입금액`이 성립합니다.

- 행별 또는 월합계로 **항목 합 ≈ 파일의 입금액**인지 확인하고, 결과를 PR 설명에 적어주세요.
- 부호가 헷갈리면 `app/importers/yogiyo.py`의 자동 검산/부호판별 패턴을 참고하세요.
- **가짜 샘플 파일**(`_FAKE_` 접두)을 함께 넣어 `python run_cli.py <가짜파일>`이 도는지 보여주면 최고입니다.

> 실파일은 없지만 양식만 아는 경우? `yogiyo.py`처럼 **헤더 이름(동의어) 매칭 + 자동검산**
> 방식으로 만들면 됩니다. 누군가 실파일로 검증해 주면 완성됩니다.

---

## 분류 규칙 한 줄 추가하기

새로운 정산 항목명이 "기타비용"으로 뭉뚱그려진다면, `app/classify/rules.py`에 키워드를 추가하면 됩니다.

```python
KEYWORD_RULES = [
    ...
    ("새항목키워드", ("판매비와관리비", "광고선전비")),   # (포함될 단어, (대분류, 계정과목))
]
```
> 순서가 중요합니다 — **더 구체적인 키워드를 위쪽**에 두세요
> (예: `"배달서비스"`(운반비)를 `"서비스이용료"`(지급수수료)보다 먼저).

---

## Pull Request 보내는 법

1. 저장소를 **Fork** 하고 브랜치를 만듭니다: `git switch -c feat/ttenggeo-importer`
2. 변경 후 커밋합니다. 커밋 메시지는 **무엇을·왜** 위주로(한글/영문 무관):
   ```
   땡겨요 importer 추가 (헤더 매칭 + 월합계 검산 오차 0원)
   ```
3. `python run_cli.py data/_FAKE_yogiyo_sample.xlsx`로 **깨지지 않는지** 확인합니다.
4. Push 후 **Pull Request**를 엽니다. 설명에 다음을 적어주면 리뷰가 빨라집니다:
   - 무엇을 바꿨는지 / 왜 필요한지
   - **검산 결과**(항목 합 vs 입금액)
   - 테스트한 방법(가짜 파일 첨부 또는 CLI 출력)

작은 PR을 환영합니다. 큰 변경은 먼저 이슈로 상의해 주시면 방향을 맞추기 좋습니다.

---

## 코드 스타일 · 약속

- Python 3.10+ · 표준 라이브러리 우선, 의존성 추가는 꼭 필요할 때만(`requirements.txt`에 반영).
- **숫자는 결정적 코드로, 막막한 매핑만 LLM** — 금액 계산에 LLM을 쓰지 마세요.
- 함수·변수명은 읽히게, 도메인 용어(중개이용료 등)는 그대로 유지.
- 서로 존중해 주세요. 초보자 질문도 환영합니다. (Be kind. 🙂)

---

## 라이선스

기여하신 내용은 이 프로젝트의 [MIT 라이선스](LICENSE)를 따릅니다.

궁금한 점은 언제든 이슈로 남겨주세요. 당신의 첫 PR을 기다립니다! 🚀

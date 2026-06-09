"""스모크 테스트 — 의존성 없이(`python tests/smoke_test.py`) 실행되는 회귀 방지 체크.

동봉된 가짜 샘플(data/_FAKE_yogiyo_sample.xlsx)로 전체 파이프라인을 돌려,
'깨지지 않는지' + '핵심 숫자가 맞는지'를 확인한다. CI(.github/workflows/ci.yml)에서도 이걸 돌린다.

검증하는 불변식:
  - importer 검산: 항목 합 = 입금액 50,580
  - 면세(총액) 기준 영업이익 = 입금액 (배달앱 정산의 기본 항등식)
  - 부가세 항등식: 면세 영업이익 − 일반 영업이익 = 일반 납부세액
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.importers.registry import import_file          # noqa: E402
from app.report.aggregate import combine_and_classify   # noqa: E402
from app.report.income_statement import build_income_statement, render_xlsx  # noqa: E402
from app.tax.vat import compute_vat                      # noqa: E402

SAMPLE = ROOT / "data" / "_FAKE_yogiyo_sample.xlsx"
PASS, FAIL = "✅", "❌"
errors = []


def check(name, cond):
    print(f"  {PASS if cond else FAIL} {name}")
    if not cond:
        errors.append(name)


def main():
    print("스모크 테스트:", SAMPLE.name)

    # 1) importer 인식 + 검산
    res = import_file(str(SAMPLE))
    check("플랫폼 인식 = yogiyo", res.platform == "yogiyo")
    check("정산입금액 = 50,580", round(res.payout_reported) == 50580)
    check("자동 검산 통과(notes)", "통과" in res.notes)
    check("거래행 추출됨", not res.rows.empty)

    # 2) 분류 + 손익 (면세=총액 기준)
    df, _ = combine_and_classify([res.rows], use_llm=False)
    ex_df, _ = compute_vat(df.copy(), "exempt")
    ex = build_income_statement(ex_df)
    check("면세 매출액 = 73,000", round(ex.revenue) == 73000)
    check("면세 영업이익 = 입금액(50,580)", round(ex.operating_profit) == 50580)

    # 3) 일반과세 + 부가세 항등식
    gn_df, vat = compute_vat(df.copy(), "general")
    gn = build_income_statement(gn_df)
    identity = round(ex.operating_profit) - round(gn.operating_profit) == round(vat["payable"])
    check("부가세 항등식(면세op − 일반op = 납부세액)", identity)
    check("납부예상세액 > 0", vat["payable"] > 0)

    # 4) 엑셀 렌더 산출물
    check("엑셀 바이트 생성", len(render_xlsx(gn, vat)) > 1000)

    print()
    if errors:
        print(f"{FAIL} 실패 {len(errors)}건:", ", ".join(errors))
        sys.exit(1)
    print(f"{PASS} 전체 통과")


if __name__ == "__main__":
    main()

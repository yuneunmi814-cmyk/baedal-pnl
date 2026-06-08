"""CLI: 정산파일 경로들을 받아 손익계산서를 출력하고 xlsx로 저장.

사용: python run_cli.py <file1.xlsx> [file2.xlsx ...] [--password PW] [--out out.xlsx]
수기입력은 --food-cost 등으로(선택). LLM은 기본 off.
"""
from __future__ import annotations

import argparse
import sys

from app.importers.registry import import_file
from app.manual.inputs import ManualInputs
from app.report.aggregate import combine_and_classify
from app.report.income_statement import as_lines, build_income_statement, render_xlsx
from app.tax.vat import compute_vat


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("files", nargs="+")
    p.add_argument("--password", default=None)
    p.add_argument("--out", default="손익계산서.xlsx")
    p.add_argument("--use-llm", action="store_true")
    p.add_argument("--tax-type", default="general",
                   choices=["general", "simplified", "exempt"])
    p.add_argument("--food-cost", type=float, default=0)
    p.add_argument("--labor", type=float, default=0)
    p.add_argument("--rent", type=float, default=0)
    args = p.parse_args(argv)

    frames, payout, period = [], 0.0, ""
    for f in args.files:
        try:
            res = import_file(f, args.password)
            frames.append(res.rows)
            payout += res.payout_reported
            period = period or res.period
            print(f"✓ {f}: {res.platform}/{res.doc_type} {len(res.rows)}행 "
                  f"정산입금 {res.payout_reported:,.0f}원")
        except Exception as e:
            print(f"✗ {f}: {e}")

    manual = ManualInputs(period=period, food_cost=args.food_cost,
                          labor=args.labor, rent=args.rent)
    frames.append(manual.to_rows())

    df, unresolved = combine_and_classify(frames, use_llm=args.use_llm)
    adj_df, vat_summary = compute_vat(df, args.tax_type)
    stmt = build_income_statement(adj_df, period=period)

    print("\n" + "=" * 44)
    print(f"손익계산서 ({period})  [{vat_summary['label']}]")
    print("=" * 44)
    for label, amount, level in as_lines(stmt):
        print(f"{label:<28} {amount:>14,.0f}")
    print("-" * 44)
    print(f"부가세 정산  매출세액 {vat_summary['output_vat']:>12,.0f}")
    print(f"            매입세액 {vat_summary['input_vat']:>12,.0f}")
    print(f"          납부예상세액 {vat_summary['payable']:>12,.0f}")
    if unresolved:
        print("\n[규칙 미매칭]", ", ".join(unresolved))
    if payout:
        print(f"[검증] 플랫폼 정산입금(파일) 합계: {payout:,.0f}원")

    with open(args.out, "wb") as fh:
        fh.write(render_xlsx(stmt, vat_summary))
    print(f"\n→ 저장: {args.out}")


if __name__ == "__main__":
    main()

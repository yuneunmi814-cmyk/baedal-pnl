"""FastAPI 손익계산서 agent — 업로드 → 식별·파싱 → 분류 → 통합 → 손익계산서.

gpt-researcher식: 백엔드가 파이프라인을 돌리고 얇은 UI가 결과를 표시.
stateless: /api/generate 한 번에 JSON(표) + base64 xlsx를 함께 반환.
"""
from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from .importers.baemin import BaeminPasswordRequired
from .importers.registry import import_file
from .manual.inputs import ManualInputs
from .report.aggregate import combine_and_classify
from .report.income_statement import (
    as_lines, build_income_statement, render_xlsx,
)
from .tax.vat import compute_vat

app = FastAPI(title="배달앱 손익계산서 Agent")

STATIC = Path(__file__).resolve().parent.parent / "static"


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.post("/api/generate")
async def generate(
    files: list[UploadFile] = File(default=[]),
    baemin_password: str = Form(default=""),
    use_llm: bool = Form(default=False),
    tax_type: str = Form(default="general"),   # general | simplified | exempt
    period: str = Form(default=""),
    food_cost: float = Form(default=0),
    labor: float = Form(default=0),
    rent: float = Form(default=0),
    utilities: float = Form(default=0),
    other_sga: float = Form(default=0),
    other_income: float = Form(default=0),
    interest_expense: float = Form(default=0),
    income_tax: float = Form(default=0),
):
    frames, warnings, payout_reported = [], [], 0.0
    detected_period = period
    needs_baemin_password = False

    for uf in files:
        data = await uf.read()
        with tempfile.NamedTemporaryFile(suffix=Path(uf.filename).suffix or ".xlsx",
                                         delete=False) as tmp:
            tmp.write(data)
            path = tmp.name
        try:
            res = import_file(path, baemin_password or None)
            frames.append(res.rows)
            payout_reported += res.payout_reported
            if res.period and not detected_period:
                detected_period = res.period
            if res.notes:
                warnings.append(f"[{uf.filename}] {res.notes}")
        except BaeminPasswordRequired as e:
            # 배민 암호는 파일마다 다름 → 해당 사용자에게 비번 입력을 요청
            needs_baemin_password = True
            warnings.append(f"[{uf.filename}] 🔒 {e}")
        except Exception as e:
            warnings.append(f"[{uf.filename}] 처리 실패: {e}")

    manual = ManualInputs(
        period=detected_period, food_cost=food_cost, labor=labor, rent=rent,
        utilities=utilities, other_sga=other_sga, other_income=other_income,
        interest_expense=interest_expense, income_tax=income_tax,
    )
    frames.append(manual.to_rows())

    df, unresolved = combine_and_classify(frames, use_llm=use_llm)

    # 검증은 총액 기준 — 파일 입금액과 직접 비교 (exempt = 모든 항목 총액 환산)
    gross_df, _ = compute_vat(df.copy(), "exempt")
    gross_stmt = build_income_statement(gross_df, period=detected_period)

    # 과세유형별 VAT 처리 후 손익 (일반=공급가액, 간이/면세=총액)
    adj_df, vat_summary = compute_vat(df, tax_type)
    stmt = build_income_statement(adj_df, period=detected_period)

    if payout_reported:
        platform_op = (gross_stmt.revenue
                       - sum(v for k, v in gross_stmt.sga_detail.items()
                             if k in ("지급수수료", "운반비", "광고선전비", "판매촉진비")))
        diff = round(platform_op - payout_reported)
        stmt.warnings.append(
            f"플랫폼 정산입금액(파일) {payout_reported:,.0f}원 ↔ "
            f"플랫폼기여 영업이익(총액) {platform_op:,.0f}원 (차이 {diff:,.0f}원, VAT·만나서결제 등)")
    if unresolved:
        stmt.warnings.append(
            "규칙 미매칭(검토→rules 승격 권장): " + ", ".join(unresolved[:20]))
    stmt.warnings.extend(warnings)

    xlsx_b64 = base64.b64encode(render_xlsx(stmt, vat_summary)).decode()
    return JSONResponse({
        "needs_baemin_password": needs_baemin_password,
        "tax_type": tax_type,
        "vat_summary": vat_summary,
        "period": stmt.period,
        "lines": [{"label": l, "amount": round(a), "level": lv}
                  for l, a, lv in as_lines(stmt)],
        "net_income": round(stmt.net_income),
        "operating_profit": round(stmt.operating_profit),
        "unresolved": unresolved,
        "warnings": stmt.warnings,
        "xlsx_base64": xlsx_b64,
        "xlsx_filename": f"손익계산서_{stmt.period or 'output'}.xlsx",
    })

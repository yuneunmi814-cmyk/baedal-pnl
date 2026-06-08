"""수기입력 — 배달앱 파일에 없는 항목(매출원가·고정비·영업외·세금)을 손익에 합류.

당기순이익까지 산출하려면 필요. 각 항목은 NORMALIZED 거래 1행(비용은 음수)으로 변환된다.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
from pydantic import BaseModel, Field


class ManualInputs(BaseModel):
    period: str = Field("", description="YYYY-MM")
    # 매출원가
    food_cost: float = Field(0, description="식자재(매출원가)")
    # 판관비 고정비
    labor: float = Field(0, description="인건비/급여")
    rent: float = Field(0, description="임대료")
    utilities: float = Field(0, description="공과금(수도/전기/가스)")
    other_sga: float = Field(0, description="기타 판관비")
    # 영업외 / 세금
    other_income: float = Field(0, description="영업외수익")
    interest_expense: float = Field(0, description="이자비용(영업외)")
    income_tax: float = Field(0, description="법인세등")

    def to_rows(self) -> pd.DataFrame:
        # (항목, 금액, vat_basis) — 입력값은 VAT포함(총액) 가정 → gross.
        # 인건비는 면세, 영업외/세금은 비과세 → none.
        items = [
            ("식자재(매출원가)", -abs(self.food_cost), "gross"),
            ("인건비", -abs(self.labor), "none"),
            ("임대료", -abs(self.rent), "gross"),
            ("공과금", -abs(self.utilities), "gross"),
            ("기타 판관비", -abs(self.other_sga), "gross"),
            ("영업외 이자수익", +abs(self.other_income), "none"),
            ("이자비용", -abs(self.interest_expense), "none"),
            ("법인세", -abs(self.income_tax), "none"),
        ]
        recs = [dict(date=f"{self.period}-01", platform="manual", doc_type="manual",
                     order_no="", item_name=name, amount=amt,
                     vat_basis=basis, vat=0.0)
                for name, amt, basis in items if amt]
        return pd.DataFrame(recs)

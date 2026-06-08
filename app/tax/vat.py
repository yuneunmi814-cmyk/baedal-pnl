"""과세유형별 부가가치세 처리.

부가세는 손익이 아니라 통과항목 → 일반과세자는 손익을 '공급가액(VAT 제외)' 기준으로
보이고, 부가세 정산(매출세액−매입세액=납부세액)을 별도로 산출한다.

vat_basis 별 (공급가액, vat) 산정:
  - gross : 금액=총액(VAT포함). 공급가액=금액/1.1, vat=금액−공급가액
  - supply: 금액=공급가액(VAT제외). 공급가액=금액, vat=금액×10%
  - exact : 파일에 부가세 명시. 공급가액=금액−vat, vat=명시값
  - none  : 비과세/면세. 공급가액=금액, vat=0
파일 부가세 컬럼 우선: 쿠팡 광고·배민 우리가게클릭은 exact, 배민 수수료는 supply(=col26),
쿠팡 번들수수료만 gross(10% 추정).
"""
from __future__ import annotations

import pandas as pd

VAT_RATE = 0.10
SIMPLIFIED_VALUE_ADDED_RATE = 0.15   # 간이과세 음식점업 부가가치율
SIMPLIFIED_INPUT_CREDIT_RATE = 0.005  # 간이과세 매입세액공제율(0.5%)

COST_L1 = ("매출원가", "판매비와관리비")


def _supply_and_vat(amount: float, basis: str, vat: float):
    """returns (공급가액, vat). 총액=공급가액+vat."""
    if basis == "gross":
        supply = amount / (1 + VAT_RATE)
        return supply, amount - supply
    if basis == "supply":
        return amount, amount * VAT_RATE
    if basis == "exact":
        return amount - vat, vat
    return amount, 0.0  # none


def _gross(amount: float, basis: str, vat: float):
    """총액(VAT포함) 환산 — 면세/간이는 총액 기준 손익."""
    if basis == "supply":
        return amount * (1 + VAT_RATE)
    return amount  # gross/exact 는 이미 총액, none 은 그대로


def compute_vat(df: pd.DataFrame, tax_type: str):
    """returns (adjusted_df, vat_summary). adjusted_df.amount = 손익 표시용 금액."""
    df = df.copy()
    if "vat_basis" not in df.columns:
        df["vat_basis"] = "none"
    if "vat" not in df.columns:
        df["vat"] = 0.0
    df["vat_basis"] = df["vat_basis"].fillna("none")
    df["vat"] = df["vat"].fillna(0.0)

    if df.empty or tax_type == "exempt":
        if not df.empty:  # 손익은 총액 기준으로 통일 (supply→총액)
            df["amount"] = [_gross(a, b, v)
                            for a, b, v in zip(df["amount"], df["vat_basis"], df["vat"])]
        return df, {
            "label": "면세사업자", "output_vat": 0, "input_vat": 0, "payable": 0,
            "note": "면세사업자 — 부가가치세 없음. 손익은 총액 기준.", "basis": "gross",
        }

    supplies, vats = [], []
    for amt, b, v in zip(df["amount"], df["vat_basis"], df["vat"]):
        s, vt = _supply_and_vat(amt, b, v)
        supplies.append(s)
        vats.append(vt)
    df["_supply"] = supplies
    df["_vat"] = vats

    output_vat = df.loc[df["account_l1"] == "매출액", "_vat"].sum()
    input_vat = -df.loc[df["account_l1"].isin(COST_L1), "_vat"].sum()

    if tax_type == "general":
        df["amount"] = df["_supply"]  # 손익 = 공급가액
        payable = output_vat - input_vat
        summary = {
            "label": "일반과세자",
            "output_vat": round(output_vat), "input_vat": round(input_vat),
            "payable": round(payable),
            "note": ("손익은 공급가액(VAT 제외) 기준. 납부세액=매출세액−매입세액. "
                     "광고·배민수수료는 파일 부가세값, 쿠팡 번들수수료는 10% 추정."),
            "basis": "supply",
        }
    else:  # simplified 간이과세 — 손익은 총액 기준
        df["amount"] = [_gross(a, b, v)
                        for a, b, v in zip(df["amount"], df["vat_basis"], df["vat"])]
        rev_gross = df.loc[df["account_l1"] == "매출액", "amount"].sum()
        buy_gross = -df.loc[(df["account_l1"].isin(COST_L1))
                            & (df["vat_basis"] != "none"), "amount"].sum()
        out = rev_gross * SIMPLIFIED_VALUE_ADDED_RATE * VAT_RATE
        cred = buy_gross * SIMPLIFIED_INPUT_CREDIT_RATE
        payable = max(0.0, out - cred)
        summary = {
            "label": "간이과세자",
            "output_vat": round(out), "input_vat": round(cred), "payable": round(payable),
            "note": ("음식점업 부가가치율 15% 가정. 손익은 총액 기준. "
                     "납부세액=공급대가×15%×10%−매입×0.5%."),
            "basis": "gross",
        }
        # 손익은 총액 유지 (amount 그대로)

    return df.drop(columns=["_supply", "_vat"]), summary

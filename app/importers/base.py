"""Importer 프로토콜 — beancount/beangulp importer.py 를 손익 단건매핑용으로 축약."""
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import List

import pandas as pd

# 정규화 거래 1행이 가지는 필드. amount 부호규칙: 매출 +, 비용 −.
NORMALIZED_COLUMNS = [
    "date",         # 'YYYY-MM-DD'
    "platform",     # baemin | coupangeats | yogiyo
    "doc_type",     # sales | settlement
    "order_no",
    "item_name",    # 항목 개념명 (분류기 입력)
    "amount",       # float, 원 (vat_basis가 gross면 VAT포함, supply면 VAT제외)
    "vat_basis",    # gross(총액) | supply(공급가액) | exact(vat명시) | none(비과세)
    "vat",          # vat_basis=exact 일 때 명시 VAT (그 외 0)
]


@dataclass
class ImportResult:
    platform: str
    doc_type: str
    period: str            # 'YYYY-MM' (가능하면)
    rows: pd.DataFrame     # NORMALIZED_COLUMNS
    payout_reported: float = 0.0   # 파일에 적힌 실정산(입금)액 — 검증용
    notes: str = ""


class DeliveryImporter(abc.ABC):
    platform: str = ""
    doc_type: str = ""

    @abc.abstractmethod
    def identify(self, filepath: str) -> bool:
        """이 파일이 이 importer 담당인지 헤더 시그니처로 판별."""

    @abc.abstractmethod
    def extract(self, filepath: str) -> ImportResult:
        """정규화된 거래 추출."""

    # 공용 유틸 ---------------------------------------------------------
    @staticmethod
    def won(value) -> float:
        """'1,234원' / '-' / None / 음수 등을 float 으로. (beangulp Amount(subs=) 패턴)"""
        if value is None:
            return 0.0
        s = str(value).strip().replace(",", "").replace("원", "").replace("₩", "")
        if s in ("", "-", "nan", "None"):
            return 0.0
        try:
            return float(s)
        except ValueError:
            return 0.0

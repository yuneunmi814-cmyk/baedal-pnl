"""업로드 파일을 모든 importer의 identify()에 돌려 담당을 찾는다 (beangulp identify.py 패턴).

identify 단계의 예외는 '다음 importer로'지만, 일단 담당이 정해지면 extract 예외는
그대로 전파한다(예: 배민 비번오류가 '담당 없음'으로 삼켜지지 않도록).
"""
from __future__ import annotations

from typing import Optional

from .base import DeliveryImporter, ImportResult
from .baemin import BaeminImporter
from .coupangeats import CoupangEatsImporter
from .yogiyo import YogiyoImporter


def build_importers(baemin_password: Optional[str] = None) -> list[DeliveryImporter]:
    return [
        CoupangEatsImporter(),   # 구체 시그니처 먼저
        BaeminImporter(password=baemin_password),  # 암호화 OLE
        YogiyoImporter(),        # 헤더 동의어 매칭(적응형) — 마지막
    ]


def import_file(filepath: str, baemin_password: Optional[str] = None) -> ImportResult:
    for imp in build_importers(baemin_password):
        try:
            matched = imp.identify(filepath)
        except Exception:
            continue  # identify 실패 → 이 importer 담당 아님
        if matched:
            return imp.extract(filepath)  # extract 예외는 전파
    raise ValueError(f"담당 importer를 찾지 못했습니다: {filepath}")

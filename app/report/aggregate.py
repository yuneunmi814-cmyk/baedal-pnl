"""여러 importer 결과 + 수기입력을 하나의 분류된 거래 테이블로 통합 (기간·플랫폼 합산)."""
from __future__ import annotations

import pandas as pd

from ..classify.engine import classify_rows


def combine_and_classify(frames: list[pd.DataFrame], use_llm: bool = True):
    """frames: NORMALIZED rows들의 리스트 → (classified_df, unresolved_items)."""
    nonempty = [f for f in frames if f is not None and not f.empty]
    if not nonempty:
        combined = pd.DataFrame(columns=[
            "date", "platform", "doc_type", "order_no", "item_name", "amount"])
    else:
        combined = pd.concat(nonempty, ignore_index=True)
    return classify_rows(combined, use_llm=use_llm)

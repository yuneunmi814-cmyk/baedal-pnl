"""분류 오케스트레이터: 규칙 우선 → 미매칭만 LLM 폴백 → 미해결 항목 로깅.

LLM이 분류한 신규 항목은 unresolved 로 함께 반환 → 사람이 승인하면 rules.py 로 승격
(= smart_importer '이력학습'의 경량판; reference §4-F/G).
"""
from __future__ import annotations

from typing import Tuple

import pandas as pd

from .rules import classify_by_rules

Account = Tuple[str, str]


def classify_rows(rows: pd.DataFrame, use_llm: bool = True) -> Tuple[pd.DataFrame, list[str]]:
    """rows(NORMALIZED) 에 account_l1, account_l2, classified_by 컬럼 추가."""
    if rows.empty:
        rows = rows.copy()
        for c in ("account_l1", "account_l2", "classified_by"):
            rows[c] = pd.Series(dtype=str)
        return rows, []

    llm_fn = None
    if use_llm:
        try:
            from .llm import classify_by_llm as llm_fn  # 지연 임포트 (requests 선택적)
        except Exception:
            llm_fn = None

    l1, l2, by = [], [], []
    unresolved: list[str] = []
    for name in rows["item_name"]:
        acc = classify_by_rules(name)
        src = "rules"
        if acc is None:
            if llm_fn is not None:
                acc = llm_fn(name)
                src = "llm"
            else:
                acc = ("판매비와관리비", "기타비용")
                src = "default"
            unresolved.append(name)
        l1.append(acc[0]); l2.append(acc[1]); by.append(src)

    out = rows.copy()
    out["account_l1"], out["account_l2"], out["classified_by"] = l1, l2, by
    # 중복 제거한 미해결 항목명 (승인→rules 승격 후보)
    seen, uniq = set(), []
    for n in unresolved:
        if n not in seen:
            seen.add(n); uniq.append(n)
    return out, uniq

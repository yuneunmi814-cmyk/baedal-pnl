"""LLM 폴백 분류 — billcat-local-llm/main.py:59-116 패턴을 Ollama로 이식.

규칙(rules.py)으로 못 잡은 신규 항목명만 여기로. Ollama 미기동/실패 시 ('기타비용')로 안전 폴백.
환각 방어: temperature=0 + 허용 계정 화이트리스트 '첫 등장'만 채택.
"""
from __future__ import annotations

import functools
import os
from typing import Tuple

import requests

Account = Tuple[str, str]

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")

# (라벨, 계정) — 라벨이 LLM 답에 등장하면 그 계정 채택
ALLOWED: list[tuple[str, Account]] = [
    ("매출", ("매출액", "배달매출")),
    ("재료비", ("매출원가", "재료비")),
    ("지급수수료", ("판매비와관리비", "지급수수료")),
    ("운반비", ("판매비와관리비", "운반비")),
    ("광고선전비", ("판매비와관리비", "광고선전비")),
    ("판매촉진비", ("판매비와관리비", "판매촉진비")),
    ("급여", ("판매비와관리비", "급여")),
    ("임차료", ("판매비와관리비", "임차료")),
    ("수도광열비", ("판매비와관리비", "수도광열비")),
    ("기타비용", ("판매비와관리비", "기타비용")),
]
DEFAULT: Account = ("판매비와관리비", "기타비용")


@functools.lru_cache(maxsize=4096)
def classify_by_llm(item_name: str) -> Account:
    labels = ", ".join(lbl for lbl, _ in ALLOWED)
    prompt = (
        "너는 정확하고 간결한 회계 분류기다. 배달앱 정산 항목명을 손익계산서 "
        f"계정과목 하나로만 분류하라. 허용 답(이 중 하나만): {labels}.\n"
        f"항목명: {item_name}\n답(계정과목 한 단어만):"
    )
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0},
        }, timeout=30)
        answer = r.json().get("response", "")
    except Exception:
        return DEFAULT
    # billcat: 답 안에서 허용 라벨 '첫 등장'만 채택 (환각 방어)
    best_pos, best_acc = 10**9, DEFAULT
    for label, acc in ALLOWED:
        pos = answer.find(label)
        if pos != -1 and pos < best_pos:
            best_pos, best_acc = pos, acc
    return best_acc

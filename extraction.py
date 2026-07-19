"""
extraction.py

Rule-based claim checker: compares a model's free-text answer against the
verified ground_truth dict and produces a 0-100 consistency score.

This is a v0 heuristic (regex/keyword matching), not real NLP. Good enough
to prove the pipeline shape and get real, comparable numbers across the
three conditions -- not good enough to ship as a product. A production
version would use structured-output extraction (ask the model to return
JSON matching a schema) or an embedding-based semantic matcher.

One deliberate design choice worth understanding, not just using: the
hallucination check below is negation-aware on purpose. An earlier version
of a similar checker I (Claude) built flagged a sentence like "not
affiliated with LinearB" as a hallucination about an affiliation with
LinearB, because it matched the keyword without checking whether the
sentence was asserting or denying the relationship. That's a real failure
mode worth knowing about before you rely on keyword matching for anything.
"""

import re
import unicodedata
from dataclasses import dataclass, field

# Models sometimes typeset multi-word names with a non-breaking hyphen/space
# (e.g. "San‑Francisco") instead of a regular one. A naive substring
# check then misses a perfectly correct answer. Normalize dash-like and
# space-like characters to a plain space before comparing.
_DASH_CHARS = "‐‑‒–—―−-"


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    for ch in _DASH_CHARS:
        text = text.replace(ch, " ")
    return re.sub(r"\s+", " ", text).lower()

_STATUS_WEIGHT = {"correct": 1.0, "partial": 0.5, "missing": 0.25, "incorrect": 0.0}

_FIELD_WEIGHTS = {
    "founded_year": 0.15,
    "hq": 0.15,
    "category": 0.20,
    "pricing_model": 0.20,
    "key_products": 0.30,
}


@dataclass
class FieldResult:
    field: str
    status: str
    detail: str = ""


@dataclass
class EvalResult:
    fields: list = field(default_factory=list)
    score: float = 0.0

    def as_dict(self):
        return {"fields": [f.__dict__ for f in self.fields], "score": round(self.score, 1)}


def _check_year(text: str, gt_year: int) -> FieldResult:
    years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", text)]
    if not years:
        return FieldResult("founded_year", "missing")
    if gt_year in years:
        return FieldResult("founded_year", "correct")
    return FieldResult("founded_year", "incorrect", f"model said {years[0]}, actual {gt_year}")


def _check_hq(text: str, gt_hq: str) -> FieldResult:
    gt_city = _normalize(gt_hq.split(",")[0].strip())
    text_n = _normalize(text)
    if gt_city in text_n:
        return FieldResult("hq", "correct")
    other_cities = ["new york", "seattle", "austin", "boston", "chicago",
                     "los angeles", "denver", "remote", "london"]
    for c in other_cities:
        if c in text_n and c != gt_city:
            return FieldResult("hq", "incorrect", f"model said '{c}', actual '{gt_city}'")
    return FieldResult("hq", "missing")


def _check_keyword_field(text: str, gt_value: str, field_name: str) -> FieldResult:
    gt_tokens = set(re.findall(r"[a-z]+", gt_value.lower()))
    text_tokens = set(re.findall(r"[a-z]+", text.lower()))
    overlap = len(gt_tokens & text_tokens) / max(1, len(gt_tokens))
    if overlap >= 0.4:
        return FieldResult(field_name, "correct")
    if overlap > 0:
        return FieldResult(field_name, "partial")
    return FieldResult(field_name, "missing")


def _check_list_field(text: str, gt_items: list, field_name: str) -> FieldResult:
    text_l = text.lower()
    hits = [item for item in gt_items if any(word in text_l for word in item.lower().split())]
    frac = len(hits) / max(1, len(gt_items))
    if frac >= 0.5:
        return FieldResult(field_name, "correct", f"{len(hits)}/{len(gt_items)} matched")
    if frac > 0:
        return FieldResult(field_name, "partial", f"{len(hits)}/{len(gt_items)} matched")
    return FieldResult(field_name, "missing")


def evaluate_response(text: str, ground_truth: dict) -> EvalResult:
    result = EvalResult()
    result.fields.append(_check_year(text, ground_truth["founded_year"]))
    result.fields.append(_check_hq(text, ground_truth["hq"]))
    result.fields.append(_check_keyword_field(text, ground_truth["category"], "category"))
    result.fields.append(_check_keyword_field(text, ground_truth["pricing_model"], "pricing_model"))
    result.fields.append(_check_list_field(text, ground_truth["key_products"], "key_products"))

    weighted = sum(_STATUS_WEIGHT[f.status] * _FIELD_WEIGHTS[f.field] for f in result.fields)
    result.score = weighted * 100
    return result

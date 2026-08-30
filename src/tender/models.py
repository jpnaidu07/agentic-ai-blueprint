"""Input validation at the API and policy-engine boundaries."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)


class Criterion(Contract):
    id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{1,39}$")
    description: str = Field(min_length=5, max_length=1000)
    category: Literal["eligibility", "technical", "commercial", "experience", "delivery", "risk"]
    method: Literal["at_least", "at_most", "higher", "lower"]
    target: Decimal = Field(gt=0, le=Decimal("1e15"))
    weight: Decimal = Field(ge=0, le=100)

    @model_validator(mode="after")
    def policy_shape(self):
        if self.category == "eligibility":
            if self.weight != 0 or self.method not in {"at_least", "at_most"}:
                raise ValueError("Eligibility is a mandatory gate, never a weighted score")
        elif self.weight <= 0 or self.method not in {"higher", "lower"}:
            raise ValueError("Scored criteria need positive weight and higher/lower normalization")
        if self.category == "commercial" and self.method != "lower":
            raise ValueError("Commercial comparison uses lowest complete eligible bid as baseline")
        return self


class TenderInput(Contract):
    id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{2,63}$")
    title: str = Field(min_length=5, max_length=200)
    agency: str = Field(min_length=2, max_length=200)
    closing_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    criteria: list[Criterion] = Field(min_length=2, max_length=40)

    @model_validator(mode="after")
    def valid_policy(self):
        from datetime import date

        date.fromisoformat(self.closing_date)
        if len({c.id for c in self.criteria}) != len(self.criteria):
            raise ValueError("Duplicate criterion IDs")
        if sum(c.weight for c in self.criteria) != 100:
            raise ValueError("Non-mandatory criterion weights must total exactly 100")
        if not any(c.category == "eligibility" for c in self.criteria):
            raise ValueError("At least one explicit eligibility criterion is required")
        if sum(c.category == "commercial" for c in self.criteria) != 1:
            raise ValueError("Exactly one commercial total is required for L1 comparison")
        return self


class BidInput(Contract):
    id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{2,63}$")
    bidder: str = Field(min_length=2, max_length=200)


class FactInput(Contract):
    criterion_id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{1,39}$")
    value: Decimal = Field(ge=0, le=Decimal("1e15"))
    document_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    page: int = Field(ge=1, le=250)
    quote: str = Field(min_length=3, max_length=4000)
    confidence: float = Field(ge=0, le=1)
    origin: Literal["human", "model"]
    producer: str = Field(min_length=2, max_length=200)
    review_note: str = Field(min_length=10, max_length=2000)


class EvaluationInput(Contract):
    idempotency_key: str = Field(pattern=r"^[A-Za-z0-9-]{8,100}$")


class DecisionInput(Contract):
    action: Literal["approve", "reject"]
    comment: str = Field(min_length=10, max_length=4000)
    expected_revision: int = Field(ge=0)


class ExtractionInput(Contract):
    document_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    page: int = Field(ge=1, le=250)


def score_bids(criteria, bids):
    """No LLM calls. Missing evidence blocks ranking; ties share rank."""
    criteria = [Criterion.model_validate(c) for c in criteria]
    commercial = next(c for c in criteria if c.category == "commercial")
    reports = []
    for bid in bids:
        facts = {f["criterion_id"]: f for f in bid["facts"]}
        missing = [c.id for c in criteria if c.id not in facts]
        failed = [
            c.id
            for c in criteria
            if c.category == "eligibility"
            and c.id in facts
            and (
                (c.method == "at_least" and Decimal(str(facts[c.id]["value"])) < c.target)
                or (c.method == "at_most" and Decimal(str(facts[c.id]["value"])) > c.target)
            )
        ]
        low = [c.id for c in criteria if c.id in facts and facts[c.id]["confidence"] < 0.8]
        zero_cost = commercial.id in facts and Decimal(str(facts[commercial.id]["value"])) <= 0
        state = (
            "INELIGIBLE"
            if failed
            else "NEEDS_REVIEW"
            if missing or low or zero_cost
            else "ELIGIBLE"
        )
        reports.append(
            {
                "bid_id": bid["id"],
                "bidder": bid["bidder"],
                "status": state,
                "missing": missing,
                "eligibility_failures": failed,
                "risk_flags": [*low, *(["NONPOSITIVE_PRICE"] if zero_cost else [])],
                "facts": list(facts.values()),
                "score": None,
                "rank": None,
                "commercial_total": str(facts[commercial.id]["value"])
                if commercial.id in facts
                else None,
            }
        )
    eligible = [r for r in reports if r["status"] == "ELIGIBLE"]
    baseline = min((Decimal(r["commercial_total"]) for r in eligible), default=None)
    for report in eligible:
        facts = {f["criterion_id"]: f for f in report["facts"]}
        breakdown = []
        for criterion in criteria:
            if not criterion.weight:
                continue
            value = Decimal(str(facts[criterion.id]["value"]))
            target = baseline if criterion.category == "commercial" else criterion.target
            ratio = (
                min(Decimal(1), value / target)
                if criterion.method == "higher"
                else (Decimal(1) if value == 0 else min(Decimal(1), target / value))
            )
            points = (ratio * criterion.weight).quantize(Decimal("0.0001"))
            breakdown.append(
                {
                    "criterion_id": criterion.id,
                    "value": str(value),
                    "baseline": str(target),
                    "points": str(points),
                }
            )
        report["breakdown"] = breakdown
        report["score"] = str(
            sum(Decimal(p["points"]) for p in breakdown).quantize(Decimal("0.01"))
        )
        report["is_l1"] = Decimal(report["commercial_total"]) == baseline
    ordered = sorted(eligible, key=lambda r: Decimal(r["score"]), reverse=True)
    for index, report in enumerate(ordered):
        report["rank"] = (
            ordered[index - 1]["rank"]
            if index and report["score"] == ordered[index - 1]["score"]
            else index + 1
        )
    return {
        "bids": reports,
        "lowest_eligible_commercial": str(baseline) if baseline else None,
        "decision": "HUMAN_REVIEW_REQUIRED",
        "scoring_version": "deterministic-v1",
    }

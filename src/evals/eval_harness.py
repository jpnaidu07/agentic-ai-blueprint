"""Measured offline golden checks. No fabricated benchmark percentages."""

import json
import time
from pathlib import Path

from src.tender.documents import retrieve
from src.tender.models import score_bids

ROOT = Path(__file__).resolve().parents[2]


def run_evaluation_benchmark():
    dataset = json.loads(
        (ROOT / "solutions/government-tender-processing/datasets/golden.json").read_text(
            encoding="utf-8"
        )
    )
    cases = []
    start = time.perf_counter()
    for case in dataset["retrieval"]:
        results = retrieve(case["query"], dataset["documents"], top_k=3)
        found, expected = {r["id"] for r in results}, set(case["relevant"])
        precision = len(found & expected) / len(found) if found else (1.0 if not expected else 0.0)
        recall = len(found & expected) / len(expected) if expected else (1.0 if not found else 0.0)
        cases.append(
            {
                "id": case["id"],
                "suite": "retrieval",
                "passed": found == expected,
                "precision": precision,
                "recall": recall,
            }
        )
    criteria = [
        {
            "id": "EL-01",
            "description": "Minimum experience",
            "category": "eligibility",
            "method": "at_least",
            "target": "5",
            "weight": "0",
        },
        {
            "id": "TECH-01",
            "description": "Technical score",
            "category": "technical",
            "method": "higher",
            "target": "100",
            "weight": "60",
        },
        {
            "id": "COST-01",
            "description": "Commercial total",
            "category": "commercial",
            "method": "lower",
            "target": "1",
            "weight": "40",
        },
    ]
    for case in dataset["scoring"]:
        facts = [
            {"criterion_id": key, "value": case[field], "confidence": case["confidence"]}
            for key, field in [
                ("EL-01", "experience"),
                ("TECH-01", "technical"),
                ("COST-01", "cost"),
            ]
            if case[field] is not None
        ]
        result = score_bids(criteria, [{"id": case["id"], "bidder": "Synthetic", "facts": facts}])[
            "bids"
        ][0]
        cases.append(
            {
                "id": case["id"],
                "suite": "scoring",
                "passed": result["status"] == case["status"] and result["score"] == case["score"],
            }
        )
    report = {
        "dataset_version": dataset["version"],
        "mode": "offline-deterministic",
        "cases": cases,
        "passed": sum(c["passed"] for c in cases),
        "total": len(cases),
        "latency_ms": round((time.perf_counter() - start) * 1000, 3),
        "live_model_quality": "not measured",
        "cloud_token_cost": "not measured",
    }
    output = ROOT / "reports"
    output.mkdir(exist_ok=True)
    (output / "offline-evaluation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    report = run_evaluation_benchmark()
    raise SystemExit(0 if report["passed"] == report["total"] else 1)

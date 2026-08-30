"""End-to-end persistence, evidence integrity, authorization and concurrency regressions."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.tender.documents import MAX_BYTES, parse_pdf, retrieve
from src.tender.models import TenderInput, score_bids
from src.tender.security import authenticate
from src.tests.conftest import accept_all, as_user, pdf_bytes, seed_bid


def test_full_evidence_evaluation_review_and_audit(client, policy):
    document_id, raw = seed_bid(client, policy)
    accept_all(client, document_id)
    payload = {"idempotency_key": "evaluation-request-001"}
    first = client.post("/api/tenders/TND-001/evaluate", json=payload)
    assert first.status_code == 200, first.text
    report = first.json()
    assert report["report"]["bids"][0]["score"] == "91.00"
    assert report["report"]["bids"][0]["is_l1"] is True
    assert client.post("/api/tenders/TND-001/evaluate", json=payload).json()["id"] == report["id"]
    decision_url = f"/api/tenders/TND-001/evaluations/{report['id']}/decision"
    body = {
        "action": "approve",
        "comment": "Committee verified the complete evidence",
        "expected_revision": report["revision"],
    }
    assert client.post(decision_url, json=body).status_code == 403
    as_user(client, "reviewer", user="evaluator-one")
    assert client.post(decision_url, json=body).status_code == 403
    as_user(client, "reviewer")
    assert client.post(decision_url, json=body).json()["state"] == "APPROVED"
    assert client.post(decision_url, json=body).status_code == 409
    trail = client.get("/api/tenders/TND-001/audit").json()
    assert trail["chain_valid"] and trail["events"][-1]["kind"] == "COMMITTEE_DECISION"
    downloaded = client.get(f"/api/tenders/TND-001/documents/{document_id}/download")
    assert downloaded.content == raw
    as_user(client, "evaluator")
    assert (
        client.post(
            "/api/tenders/TND-001/bids", json={"id": "BID-002", "bidder": "Late bidder"}
        ).status_code
        == 409
    )


def test_stale_evidence_rejects_approval_and_idempotency_reuse(client, policy):
    doc, _ = seed_bid(client, policy)
    accept_all(client, doc)
    body = {"idempotency_key": "stable-request-001"}
    evaluation = client.post("/api/tenders/TND-001/evaluate", json=body).json()
    accept_all(client, doc)
    assert client.post("/api/tenders/TND-001/evaluate", json=body).status_code == 409
    as_user(client, "reviewer")
    response = client.post(
        f"/api/tenders/TND-001/evaluations/{evaluation['id']}/decision",
        json={
            "action": "approve",
            "comment": "Reviewed old evidence snapshot",
            "expected_revision": evaluation["revision"],
        },
    )
    assert response.status_code == 409


def test_missing_evidence_cannot_be_approved(client, policy):
    seed_bid(client, policy)
    evaluation = client.post(
        "/api/tenders/TND-001/evaluate", json={"idempotency_key": "missing-evidence-1"}
    ).json()
    assert evaluation["report"]["bids"][0]["score"] is None
    as_user(client, "reviewer")
    assert (
        client.post(
            f"/api/tenders/TND-001/evaluations/{evaluation['id']}/decision",
            json={
                "action": "approve",
                "comment": "Attempt to approve without evidence",
                "expected_revision": evaluation["revision"],
            },
        ).status_code
        == 409
    )


def test_tender_scope_applies_to_every_read(client, policy):
    doc, _ = seed_bid(client, policy)
    as_user(client, "viewer", scopes=("TND-OTHER",))
    assert client.get("/api/tenders").json()["tenders"] == []
    for suffix in [
        "",
        f"/documents/{doc}",
        f"/documents/{doc}/download",
        "/search?q=experience",
        "/audit",
    ]:
        assert client.get("/api/tenders/TND-001" + suffix).status_code == 404


def test_invalid_authentication_and_safe_headers(client, monkeypatch):
    client.app.dependency_overrides.pop(authenticate)
    monkeypatch.setenv(
        "AUTH_USERS",
        json.dumps(
            [
                {
                    "token_sha256": hashlib.sha256(b"test-only-token").hexdigest(),
                    "user_id": "viewer",
                    "role": "viewer",
                    "tender_ids": [],
                }
            ]
        ),
    )
    assert client.get("/api/tenders").status_code == 401
    assert (
        client.get("/api/tenders", headers={"Authorization": "Bearer invalid"}).status_code == 401
    )
    response = client.get("/api/tenders", headers={"Authorization": "Bearer test-only-token"})
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_document_dedup_and_append_only_evidence(client, policy):
    doc, raw = seed_bid(client, policy)
    second = client.post(
        "/api/tenders/TND-001/documents?bid_id=BID-001",
        files={"file": ("renamed.pdf", raw, "application/pdf")},
    )
    assert second.json() == {"id": doc, "duplicate": True}
    accept_all(client, doc)
    with pytest.raises(IntegrityError), client.app.state.tender_store.engine.begin() as conn:
        conn.execute(text("DELETE FROM facts"))
    with pytest.raises(IntegrityError), client.app.state.tender_store.engine.begin() as conn:
        conn.execute(text("UPDATE audit_events SET kind = 'tampered'"))


@pytest.mark.parametrize(
    "change",
    [
        {"quote": "This quote was invented"},
        {"page": 99},
        {"criterion_id": "UNKNOWN"},
        {"value": "NaN"},
        {"value": "Infinity"},
        {"value": "-1"},
    ],
)
def test_invalid_evidence_is_rejected(client, policy, change):
    doc, _ = seed_bid(client, policy)
    body = {
        "criterion_id": "EL-01",
        "value": "7",
        "document_id": doc,
        "page": 1,
        "quote": "Experience: 7 years.",
        "confidence": 1,
        "origin": "human",
        "producer": "human-review",
        "review_note": "Checked the original page",
    }
    body.update(change)
    assert client.post("/api/tenders/TND-001/bids/BID-001/facts", json=body).status_code == 422


def test_bid_cannot_use_another_bidders_evidence(client, policy):
    doc, _ = seed_bid(client, policy)
    client.post("/api/tenders/TND-001/bids", json={"id": "BID-002", "bidder": "Other bidder"})
    body = {
        "criterion_id": "EL-01",
        "value": "7",
        "document_id": doc,
        "page": 1,
        "quote": "Experience: 7 years.",
        "confidence": 1,
        "origin": "human",
        "producer": "human-review",
        "review_note": "Attempt cross-bid evidence",
    }
    assert client.post("/api/tenders/TND-001/bids/BID-002/facts", json=body).status_code == 422


def test_concurrent_identical_evaluations_are_idempotent(client, policy):
    doc, _ = seed_bid(client, policy)
    accept_all(client, doc)

    def request(_):
        return client.post(
            "/api/tenders/TND-001/evaluate", json={"idempotency_key": "concurrent-request-001"}
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(request, range(4)))
    assert all(r.status_code == 200 for r in responses)
    assert len({r.json()["id"] for r in responses}) == 1
    assert client.get("/api/tenders/TND-001/audit").json()["chain_valid"]


def test_pdf_type_and_resource_limits():
    for invalid in [b"", b"not a pdf", b"%PDF-" + b"x" * MAX_BYTES]:
        with pytest.raises(ValueError):
            parse_pdf(invalid)
    with pytest.raises(ValueError, match="Malware"):
        parse_pdf(pdf_bytes(), scanner=lambda _: False)
    assert parse_pdf(pdf_bytes())["pages"][0]["page"] == 1


def test_upload_limits_and_scanner_fail_closed(client, policy, monkeypatch):
    seed_bid(client, policy)
    monkeypatch.setenv("APP_ENV", "production")
    response = client.post(
        "/api/tenders/TND-001/documents",
        files={"file": ("bid.pdf", pdf_bytes(), "application/pdf")},
    )
    assert response.status_code == 503
    assert client.post("/api/tenders", content=b"x" * (11 * 1024 * 1024 + 1)).status_code == 413


def test_search_and_model_transfer_gate(client, policy):
    doc, _ = seed_bid(client, policy)
    result = client.get("/api/tenders/TND-001/search?q=experience").json()
    assert result["matches"][0]["document_id"] == doc
    assert result["matches"][0]["page"] == 1
    assert (
        client.get("/api/tenders/TND-001/search?q=unfindablexyz").json()["status"]
        == "INSUFFICIENT_EVIDENCE"
    )
    assert (
        client.post(
            "/api/tenders/TND-001/extraction-proposals", json={"document_id": doc, "page": 1}
        ).status_code
        == 503
    )


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-1"])
def test_policy_rejects_nonfinite_or_negative_weights(policy, bad):
    policy["criteria"][1]["weight"] = bad
    with pytest.raises(ValidationError):
        TenderInput.model_validate(policy)


def test_scoring_excludes_ineligible_commercial_and_shares_ties(policy):
    def bid(id, experience, cost):
        return {
            "id": id,
            "bidder": id,
            "facts": [
                {"criterion_id": k, "value": v, "confidence": 1}
                for k, v in [("EL-01", experience), ("TECH-01", 80), ("COST-01", cost)]
            ],
        }

    report = score_bids(policy["criteria"], [bid("B1", 7, 100), bid("B2", 7, 100), bid("B3", 2, 1)])
    assert [b["rank"] for b in report["bids"]] == [1, 1, None]
    assert report["lowest_eligible_commercial"] == "100"


def test_hybrid_extension_and_abstention():
    records = [{"text": "disk replacement"}, {"text": "procurement evidence"}]
    assert retrieve("procurement", records)[0]["text"] == "procurement evidence"
    assert retrieve("unrelated", records) == []
    result = retrieve("procurement", records, embedder=lambda _: [[1, 0], [0, 1], [1, 0]])
    assert result[0]["retrieval_method"] == "hybrid-rrf"
    with pytest.raises(ValueError):
        retrieve("procurement", records, embedder=lambda _: [[1, 0]])

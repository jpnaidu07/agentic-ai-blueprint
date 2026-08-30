"""Isolated temporary storage and synthetic documents; no live provider access."""

import io

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from src.api.server import create_app
from src.tender.security import Principal, authenticate


def pdf_bytes(text="Experience: 7 years. Technical score: 85. Total cost: 100000 INR."):
    writer = PdfWriter()
    page = writer.add_blank_page(width=600, height=800)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
    )
    stream = DecodedStreamObject()
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream.set_data(f"BT /F1 12 Tf 30 750 Td ({escaped}) Tj ET".encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    result = io.BytesIO()
    writer.write(result)
    return result.getvalue()


@pytest.fixture
def policy():
    return {
        "id": "TND-001",
        "title": "Digital records platform",
        "agency": "Synthetic Committee",
        "closing_date": "2030-12-31",
        "currency": "INR",
        "criteria": [
            {
                "id": "EL-01",
                "description": "Five years of relevant experience",
                "category": "eligibility",
                "method": "at_least",
                "target": "5",
                "weight": "0",
            },
            {
                "id": "TECH-01",
                "description": "Technical evaluation out of 100",
                "category": "technical",
                "method": "higher",
                "target": "100",
                "weight": "60",
            },
            {
                "id": "COST-01",
                "description": "Comparable commercial total",
                "category": "commercial",
                "method": "lower",
                "target": "1",
                "weight": "40",
            },
        ],
    }


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("ALLOW_DOCUMENT_LLM", raising=False)
    monkeypatch.chdir(tmp_path)
    app = create_app(f"sqlite:///{(tmp_path / 'tender.sqlite').as_posix()}")
    app.dependency_overrides[authenticate] = lambda: Principal("admin-one", "admin", ("*",))
    with TestClient(app) as test_client:
        yield test_client


def as_user(client, role, user=None, scopes=("TND-001",)):
    client.app.dependency_overrides[authenticate] = lambda: Principal(
        user or role + "-one", role, scopes
    )


def seed_bid(client, policy, bid_id="BID-001", bidder="Example Bidder"):
    as_user(client, "admin")
    response = client.post("/api/tenders", json=policy)
    assert response.status_code in {201, 409}, response.text
    as_user(client, "evaluator")
    response = client.post("/api/tenders/TND-001/bids", json={"id": bid_id, "bidder": bidder})
    assert response.status_code == 201, response.text
    raw = pdf_bytes()
    response = client.post(
        f"/api/tenders/TND-001/documents?bid_id={bid_id}",
        files={"file": ("bid.pdf", raw, "application/pdf")},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"], raw


def accept_all(client, document_id, bid_id="BID-001"):
    for criterion, value, quote in [
        ("EL-01", "7", "Experience: 7 years."),
        ("TECH-01", "85", "Technical score: 85."),
        ("COST-01", "100000", "Total cost: 100000 INR."),
    ]:
        response = client.post(
            f"/api/tenders/TND-001/bids/{bid_id}/facts",
            json={
                "criterion_id": criterion,
                "value": value,
                "document_id": document_id,
                "page": 1,
                "quote": quote,
                "confidence": 1,
                "origin": "human",
                "producer": "human-review",
                "review_note": "Checked quote, units and tender criterion",
            },
        )
        assert response.status_code == 201, response.text

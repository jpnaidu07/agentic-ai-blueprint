"""Bounded digital-PDF extraction and explicit optional embedding retrieval."""

import hashlib
import io
import math
import re
from collections import Counter

from pypdf import PdfReader

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 250


def parse_pdf(data: bytes, scanner=None):
    if not data or len(data) > MAX_BYTES or not data.startswith(b"%PDF-"):
        raise ValueError("A digital PDF no larger than 10 MiB is required")
    if scanner is not None and scanner(data) is not True:
        raise ValueError("Malware scan did not return a clean result")
    try:
        reader = PdfReader(io.BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs require an approved decryption pipeline")
        root = reader.trailer["/Root"]
        names = root.get("/Names", {})
        if hasattr(names, "get_object"):
            names = names.get_object()
        if (
            "/OpenAction" in root
            or "/AA" in root
            or "/JavaScript" in names
            or "/EmbeddedFiles" in names
            or "/AcroForm" in root
        ):
            raise ValueError("PDF actions, attachments and interactive forms are not accepted")
        if not 0 < len(reader.pages) <= MAX_PAGES:
            raise ValueError("PDF must contain 1–250 pages")
        pages = []
        for number, page in enumerate(reader.pages, 1):
            if "/AA" in page or "/Annots" in page:
                raise ValueError("Annotated/interactive PDFs require flattening before upload")
            text = page.extract_text(extraction_mode="layout").strip()
            if len(text) > 100_000:
                raise ValueError("PDF page exceeds extraction limit")
            pages.append({"page": number, "text": text})
        if not any(p["text"] for p in pages):
            raise ValueError(
                "No digital text found; route scanned documents to the optional OCR pipeline"
            )
        return {
            "sha256": hashlib.sha256(data).hexdigest(),
            "pages": pages,
            "scanner": "clean" if scanner else "not_configured",
        }
    except ValueError:
        raise
    except Exception:
        raise ValueError("Malformed or unsupported digital PDF") from None


def chunks(pages, size=1400, overlap=150):
    output = []
    for page in pages:
        text = page["text"]
        for start in range(0, len(text), size - overlap):
            section = text[start : start + size]
            if section.strip():
                output.append(
                    {
                        "page": page["page"],
                        "section": f"page-{page['page']}-offset-{start}",
                        "text": section,
                    }
                )
    return output


def tokens(text):
    return re.findall(r"\w+", text.casefold())


def retrieve(query, records, top_k=5, embedder=None):
    """BM25; optional supplied embeddings use reciprocal-rank fusion, never fake semantics."""
    if not records:
        return []
    query_tokens = set(tokens(query))
    docs = [Counter(tokens(r["text"])) for r in records]
    avg = sum(sum(d.values()) for d in docs) / len(docs) or 1
    scored = []
    for index, doc in enumerate(docs):
        score = 0.0
        for term in query_tokens:
            df = sum(term in other for other in docs)
            freq = doc[term]
            idf = math.log(1 + (len(docs) - df + 0.5) / (df + 0.5))
            score += idf * freq * 2.5 / (freq + 1.5 * (0.25 + 0.75 * sum(doc.values()) / avg))
        if score > 0:
            scored.append((index, score))
    scored.sort(key=lambda pair: pair[1], reverse=True)
    if embedder:
        vectors = embedder([query, *[r["text"] for r in records]])
        if len(vectors) != len(records) + 1 or any(len(v) != len(vectors[0]) for v in vectors):
            raise ValueError("Embedding provider returned inconsistent dimensions")

        def cosine(a, b):
            denominator = math.sqrt(sum(x * x for x in a) * sum(x * x for x in b))
            return sum(x * y for x, y in zip(a, b, strict=True)) / denominator if denominator else 0

        semantic = sorted(
            [(i, cosine(vectors[0], v)) for i, v in enumerate(vectors[1:])],
            key=lambda p: p[1],
            reverse=True,
        )
        fused = {}
        for ranking in (scored, semantic):
            for rank, (index, score) in enumerate(ranking, 1):
                if score > 0:
                    fused[index] = fused.get(index, 0) + 1 / (60 + rank)
        scored = sorted(fused.items(), key=lambda p: p[1], reverse=True)
    return [
        {
            **records[i],
            "retrieval_score": round(score, 6),
            "retrieval_method": "hybrid-rrf" if embedder else "bm25",
        }
        for i, score in scored[:top_k]
    ]

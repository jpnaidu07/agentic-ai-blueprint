"""Generate a maintainable SVG from the eight-module architecture vocabulary."""

from html import escape
from pathlib import Path

MODULES = [
    (
        "Purpose & Scope",
        [
            "Business capability & personas",
            "Constraints, scale & sensitivity",
            "Success and acceptance criteria",
        ],
    ),
    (
        "System Prompt Design",
        [
            "Role, policy & output contracts",
            "Untrusted evidence boundaries",
            "Versioning, refusal & escalation",
        ],
    ),
    (
        "Choose LLM",
        [
            "Configurable provider & model",
            "Capability, cost & latency fit",
            "Explicit failure and fallback",
        ],
    ),
    (
        "Tools & Integrations",
        [
            "Typed inputs, outputs & errors",
            "Authorization, timeout & retries",
            "APIs, MCP & deterministic tools",
        ],
    ),
    (
        "Memory Systems",
        [
            "Working and episodic context",
            "SQL entities & object storage",
            "Evidence retrieval when justified",
        ],
    ),
    (
        "Orchestration",
        [
            "State, routes & dependencies",
            "Idempotency and recovery",
            "Human approval at boundaries",
        ],
    ),
    (
        "User Interface",
        [
            "Capability-derived screens",
            "APIs, chat & review workflows",
            "Evidence and operational status",
        ],
    ),
    (
        "Testing & Evaluation",
        [
            "Unit, integration & security",
            "Golden data and retrieval quality",
            "Measured latency, cost & regression",
        ],
    ),
]


def main():
    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 1000" role="img" aria-labelledby="title desc">',
        '<title id="title">Agentic AI Blueprint: eight engineering modules</title>',
        '<desc id="desc">Eight modules surround a shared contract boundary. A separate spec-first workflow connects business use cases to capability, design, decomposition, implementation and evaluation.</desc>',
        '<rect width="1440" height="1000" fill="#f3f5ef"/>',
        "<style>text{font-family:Segoe UI,Arial,sans-serif}.eyebrow{font-size:13px;letter-spacing:2px;fill:#64805b}.title{font-size:40px;font-weight:700;fill:#17382c}.card-title{font-size:21px;font-weight:650;fill:#183a2e}.body{font-size:16px;fill:#536858}.number{font-size:17px;fill:white;font-weight:700}.step{font-size:16px;fill:#193c2b;font-weight:600}</style>",
        '<text x="48" y="49" class="eyebrow">REUSABLE ENGINEERING METHODOLOGY</text>',
        '<text x="48" y="104" class="title">Agentic AI Blueprint</text>',
        '<text x="48" y="141" class="body">Start from a business capability. Make decisions explicit. Keep evidence and human authority intact.</text>',
    ]
    for index, (title, lines) in enumerate(MODULES):
        x = 48 + (index % 4) * 340
        y = 185 if index < 4 else 512
        svg += [
            f'<rect x="{x}" y="{y}" width="322" height="235" rx="12" fill="white" stroke="#ced9c8"/>',
            f'<rect x="{x + 20}" y="{y + 23}" width="36" height="36" rx="8" fill="#24593f"/>',
            f'<text x="{x + 38}" y="{y + 47}" text-anchor="middle" class="number">{index + 1}</text>',
            f'<text x="{x + 20}" y="{y + 96}" class="card-title">{escape(title)}</text>',
        ]
        for j, line in enumerate(lines):
            svg.append(
                f'<text x="{x + 20}" y="{y + 138 + j * 29}" class="body">{escape(line)}</text>'
            )
        cy = 420 if index < 4 else 492
        svg.append(f'<path d="M {x + 161} {cy} V {cy + 20}" stroke="#8caa7a" stroke-width="2"/>')
    svg += [
        '<rect x="48" y="440" width="1342" height="52" rx="8" fill="#1b3c2f"/>',
        '<text x="719" y="473" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="17" fill="#e5eeda">Shared contracts · resource authorization · evidence provenance · observability</text>',
        '<text x="48" y="801" class="eyebrow">SPEC-FIRST DELIVERY FLOW</text>',
    ]
    steps = [
        "Business use case",
        "Capability spec",
        "Design spec",
        "Decomposition",
        "Implementation",
        "Tests & evals",
    ]
    for i, label in enumerate(steps):
        x = 48 + i * 226
        svg.append(f'<rect x="{x}" y="826" width="204" height="58" rx="6" fill="#e2ecd8"/>')
        svg.append(
            f'<text x="{x + 102}" y="861" text-anchor="middle" class="step">{escape(label)}</text>'
        )
        if i < 5:
            svg.append(
                f'<path d="M {x + 208} 855 h 12 m -5 -5 l 5 5 -5 5" fill="none" stroke="#668556" stroke-width="2"/>'
            )
    svg += [
        '<text x="48" y="925" class="body">First execution produces specifications. Approved skills implement selected work packages. Deployment follows validation.</text>',
        '<text x="48" y="962" class="eyebrow">BLUEPRINT = METHOD   /   SPECS = SOLUTION DECISIONS   /   SKILLS = PROCESS   /   CODE = IMPLEMENTATION</text>',
        "</svg>",
    ]
    target = Path(__file__).resolve().parents[1] / "docs/diagrams/agent-blueprint.svg"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(svg) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

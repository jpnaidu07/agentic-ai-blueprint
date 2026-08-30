"""Versioned, strict input and specification contracts."""

from graphlib import TopologicalSorter
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Requirement(Contract):
    id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{1,39}$")
    objective: str = Field(min_length=10)
    acceptance: list[str] = Field(min_length=1)
    skill: Literal["backend", "database", "frontend", "agents", "rag", "infrastructure", "security"]
    depends_on: list[str] = Field(default_factory=list)
    blueprint_modules: list[Annotated[int, Field(ge=1, le=8)]] = Field(default_factory=list)


class UseCase(Contract):
    schema_version: Literal[1] = 1
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{2,63}$")
    title: str = Field(min_length=5)
    problem: str = Field(min_length=20)
    objectives: list[str] = Field(min_length=1)
    personas: list[str] = Field(min_length=1)
    journeys: list[str] = Field(min_length=1)
    requirements: list[Requirement] = Field(min_length=1)
    business_rules: list[str] = Field(min_length=1)
    inputs: list[str] = Field(min_length=1)
    outputs: list[str] = Field(min_length=1)
    security: list[str] = Field(min_length=1)
    compliance: list[str] = Field(min_length=1)
    data_sensitivity: str = Field(min_length=3)
    scale: str = Field(min_length=3)
    nonfunctional: list[str] = Field(min_length=1)
    human_approvals: list[str] = Field(min_length=1)
    failures: list[str] = Field(min_length=1)
    deployment: str = Field(min_length=3)
    model_selection: str = Field(min_length=10)
    open_questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_requirements(self):
        ids = [r.id for r in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("Requirement IDs must be unique")
        if set(ids) & {"TESTS", "EVALS", "DEPLOYMENT"}:
            raise ValueError("TESTS, EVALS and DEPLOYMENT are reserved gate IDs")
        for requirement in self.requirements:
            if set(requirement.depends_on) - set(ids):
                raise ValueError(f"Unknown requirement dependency: {requirement.id}")
        list(TopologicalSorter({r.id: r.depends_on for r in self.requirements}).static_order())
        return self


class Module(Contract):
    number: int = Field(ge=1, le=8)
    name: str
    decisions: list[str] = Field(min_length=1)


class Design(Contract):
    schema_version: Literal[1] = 1
    solution: str
    capability_digest: str
    modules: list[Module] = Field(min_length=8, max_length=8)
    tradeoffs: list[str] = Field(min_length=1)
    production_gates: list[str] = Field(min_length=1)


class Task(Contract):
    id: str = Field(pattern=r"^[A-Z][A-Z0-9-]{1,79}$")
    parent_capability: str
    objective: str
    skill: str
    dependencies: list[str]
    inputs: list[str] = Field(min_length=1)
    outputs: list[str] = Field(min_length=1)
    affected_modules: list[str] = Field(min_length=1)
    blueprint_modules: list[Annotated[int, Field(ge=1, le=8)]] = Field(default_factory=list)
    api_contract: str
    data_contract: str
    agent_tools: list[str]
    instructions: list[str] = Field(min_length=1)
    tests: list[str] = Field(min_length=1)
    definition_of_done: list[str] = Field(min_length=1)


class Decomposition(Contract):
    schema_version: Literal[1] = 1
    solution: str
    design_digest: str
    tasks: list[Task] = Field(min_length=1)

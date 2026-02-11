from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Goals(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project_goals: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)


class Tech(BaseModel):
    model_config = ConfigDict(extra="ignore")

    languages: list[str] = Field(default_factory=list)
    stack: list[str] = Field(default_factory=list)
    runtime_constraints: list[str] = Field(default_factory=list)


class Module(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1)
    responsibility: str = Field(default="")
    depends_on: list[str] = Field(default_factory=list)


class Capability(BaseModel):
    model_config = ConfigDict(extra="ignore")

    module: str = Field(min_length=1)
    provides: list[str] = Field(default_factory=list)
    not_provide: list[str] = Field(default_factory=list)


class Contract(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1)
    purpose: str = Field(default="")
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    guarantees: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)


class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1)
    module: str = Field(min_length=1)
    description: str = Field(default="")
    depends_on: list[str] = Field(default_factory=list)


class ArchitectPlan(BaseModel):
    """Strict-ish schema for architect output.

    We allow extra fields to keep backward compatibility with models,
    but validate core shapes so downstream nodes can rely on them.
    """

    model_config = ConfigDict(extra="ignore")

    goals: Goals = Field(default_factory=Goals)
    tech: Tech = Field(default_factory=Tech)
    modules: list[Module] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
    contracts: list[Contract] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)


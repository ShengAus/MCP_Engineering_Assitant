from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class VoltageDropInput(BaseModel):
    current_a: float = Field(gt=0, description="Load current in amps.")
    length_m: float = Field(gt=0, description="One-way cable route length in metres.")
    line_voltage_v: float = Field(gt=0, description="Line-to-line voltage in volts.")
    resistance_ohm_per_km: float = Field(ge=0, description="Cable resistance in ohm/km.")
    reactance_ohm_per_km: float = Field(ge=0, description="Cable reactance in ohm/km.")
    power_factor: float = Field(gt=0, le=1, description="Load power factor.")
    threshold_percent: float = Field(default=5.0, gt=0, description="Demo voltage drop threshold.")


class VoltageDropResult(BaseModel):
    voltage_drop_v: float
    voltage_drop_percent: float
    threshold_percent: float
    is_within_threshold: bool
    formula: str
    inputs: VoltageDropInput


class EvidenceItem(BaseModel):
    section_id: str
    title: str
    source_file: str
    snippet: str
    score: float = 0


class DocSection(EvidenceItem):
    content: str


class EngineeringReportInput(BaseModel):
    title: str = "Engineering Calculation Report"
    user_question: str
    inputs: dict[str, Any]
    assumptions: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    calculation_result: dict[str, Any]
    limitations: list[str] = Field(default_factory=list)
    suggested_next_checks: list[str] = Field(default_factory=list)
    tool_trace: list[str] = Field(default_factory=list)

    @field_validator("limitations")
    @classmethod
    def require_limitations(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("At least one limitation is required for engineering reports.")
        return value


class EngineeringReportResult(BaseModel):
    markdown: str

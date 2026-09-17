"""Pydantic models for qibocal-report."""

from typing import Any

from pydantic import BaseModel, Field


class ServerModel(BaseModel):
    id: str
    name: str
    url: str
    description: str | None = ""
    avatar: str | None = "quantum-ring"
    is_default: bool = False
    created_at: str | None = None


class ServerCreate(BaseModel):
    url: str
    name: str | None = None
    description: str | None = None
    avatar: str | None = None


class ServerUpdate(BaseModel):
    url: str | None = None
    name: str | None = None
    description: str | None = None
    avatar: str | None = None
    is_default: bool | None = None


class ProtocolFigure(BaseModel):
    id: str
    title: str
    data: list[dict[str, Any]] = Field(default_factory=list)
    layout: dict[str, Any] = Field(default_factory=dict)


class ProtocolSummary(BaseModel):
    id: str
    name: str
    category: str | None = "characterization"
    execution_time: str | None = None
    status: str = "success"
    num_figures: int = 0


class ProtocolDetail(BaseModel):
    id: str
    name: str
    category: str | None = "characterization"
    execution_time: str | None = None
    status: str = "success"
    html: str | None = ""
    figures: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None


class ReportSummary(BaseModel):
    id: str
    path: str
    title: str = ""
    date: str
    time: str | None = ""
    author: str | None = "Unknown"
    platform: str | None = "Unknown"
    targets: list[Any] = Field(default_factory=list)
    protocols: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    total_execution_time: str | None = None
    has_cached_report: bool = False


class ReportDetail(ReportSummary):
    history: Any | None = Field(default_factory=dict)
    platform_snapshot: dict[str, Any] | None = Field(default_factory=dict)
    protocols_summary: list[ProtocolSummary] = Field(default_factory=list)


class ProtocolFrequency(BaseModel):
    name: str
    count: int


class DateHistogramBin(BaseModel):
    date: str
    count: int


class FilterStats(BaseModel):
    authors: list[str]
    tags: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    protocols: list[ProtocolFrequency]
    date_histogram: list[DateHistogramBin]


class HealthResponse(BaseModel):
    status: str = "ok"
    server_name: str
    reports_count: int
    root_dir: str

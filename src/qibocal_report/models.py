"""Pydantic models for qibocal-report."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ServerModel(BaseModel):
    id: str
    name: str
    url: str
    description: Optional[str] = ""
    avatar: Optional[str] = "quantum-ring"
    is_default: bool = False
    created_at: Optional[str] = None


class ServerCreate(BaseModel):
    url: str
    name: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None


class ServerUpdate(BaseModel):
    url: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    avatar: Optional[str] = None
    is_default: Optional[bool] = None


class ProtocolFigure(BaseModel):
    id: str
    title: str
    data: List[Dict[str, Any]] = Field(default_factory=list)
    layout: Dict[str, Any] = Field(default_factory=dict)


class ProtocolSummary(BaseModel):
    id: str
    name: str
    category: Optional[str] = "characterization"
    execution_time: Optional[str] = None
    status: str = "success"
    num_figures: int = 0


class ProtocolDetail(BaseModel):
    id: str
    name: str
    category: Optional[str] = "characterization"
    execution_time: Optional[str] = None
    status: str = "success"
    html: Optional[str] = ""
    figures: List[Dict[str, Any]] = Field(default_factory=list)


class ReportSummary(BaseModel):
    id: str
    path: str
    title: str
    date: str
    time: Optional[str] = ""
    author: Optional[str] = "Unknown"
    platform: Optional[str] = "Unknown"
    targets: List[Any] = Field(default_factory=list)
    protocols: List[str] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    total_execution_time: Optional[str] = None
    has_cached_report: bool = False


class ReportDetail(ReportSummary):
    history: Optional[Any] = Field(default_factory=dict)
    platform_snapshot: Optional[Dict[str, Any]] = Field(default_factory=dict)
    protocols_summary: List[ProtocolSummary] = Field(default_factory=list)


class ProtocolFrequency(BaseModel):
    name: str
    count: int


class DateHistogramBin(BaseModel):
    date: str
    count: int


class FilterStats(BaseModel):
    authors: List[str]
    labels: List[str]
    protocols: List[ProtocolFrequency]
    date_histogram: List[DateHistogramBin]


class HealthResponse(BaseModel):
    status: str = "ok"
    server_name: str
    reports_count: int
    root_dir: str

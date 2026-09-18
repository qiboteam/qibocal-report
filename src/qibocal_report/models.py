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
    author_identities: dict[str, list[str]] = Field(default_factory=dict)
    protocol_docs: dict[str, str] = Field(default_factory=dict)


class ServerCreate(BaseModel):
    url: str
    name: str | None = None
    description: str | None = None
    avatar: str | None = None
    author_identities: dict[str, list[str]] | None = None
    protocol_docs: dict[str, str] | None = None


class ServerUpdate(BaseModel):
    url: str | None = None
    name: str | None = None
    description: str | None = None
    avatar: str | None = None
    is_default: bool | None = None
    author_identities: dict[str, list[str]] | None = None
    protocol_docs: dict[str, str] | None = None


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
    has_old_platform: bool = False
    has_new_platform: bool = False
    search_index: str = ""


class ReportDetail(ReportSummary):
    history: Any | None = Field(default_factory=dict)
    platform_snapshot: dict[str, Any] | None = Field(default_factory=dict)
    protocols_summary: list[ProtocolSummary] = Field(default_factory=list)


class PlatformDataResponse(BaseModel):
    report_id: str
    platform_name: str | None = None
    platform_type: str = "new"  # "old" or "new"
    has_old_platform: bool = False
    has_new_platform: bool = False
    parameters: dict[str, Any] | None = None
    calibration: dict[str, Any] | None = None


class PaginatedReportsResponse(BaseModel):
    items: list[ReportSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProtocolFrequency(BaseModel):
    name: str
    count: int


class PlatformFrequency(BaseModel):
    name: str
    count: int


class AuthorFrequency(BaseModel):
    name: str
    count: int


class TagFrequency(BaseModel):
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
    platforms: list[PlatformFrequency] = Field(default_factory=list)
    author_frequencies: list[AuthorFrequency] = Field(default_factory=list)
    tag_frequencies: list[TagFrequency] = Field(default_factory=list)
    total_reports: int = 0


class HealthResponse(BaseModel):
    status: str = "ok"
    server_name: str
    reports_count: int
    root_dir: str
    original_root_dir: str | None = None


class BulkActionRequest(BaseModel):
    action: str  # "label", "unlabel", "delete", "author"
    report_ids: list[str]
    label: str | None = None
    author: str | None = None


class BulkActionResponse(BaseModel):
    success: bool
    action: str
    affected: int
    message: str


class SingleLabelRequest(BaseModel):
    label: str = ""


class UpdateAuthorRequest(BaseModel):
    author: str


class DirectoryBreadcrumb(BaseModel):
    name: str
    path: str


class DirectoryEntry(BaseModel):
    name: str
    path: str
    has_subdirs: bool = False
    is_current: bool = False
    reports_count: int = 0


class ServerDirectoryInfo(BaseModel):
    original_root: str
    current_root: str
    relative_current: str
    reports_count: int = 0


class DirectoryBrowseResponse(BaseModel):
    original_root: str
    current_root: str
    current_browse_path: str
    parent_path: str | None = None
    breadcrumbs: list[DirectoryBreadcrumb] = Field(default_factory=list)
    directories: list[DirectoryEntry] = Field(default_factory=list)
    is_active_root: bool = False
    reports_count: int = 0


class ChangeDirectoryRequest(BaseModel):
    path: str = ""

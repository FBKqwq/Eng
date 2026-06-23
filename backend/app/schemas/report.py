"""分析报告 API 契约（占位）。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3 report 域
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ReportType(str, Enum):
  periodic = "periodic"
  event = "event"


class ReportStatus(str, Enum):
  draft = "draft"
  published = "published"
  archived = "archived"


class ReportListItem(BaseModel):
  report_id: str
  report_type: ReportType
  title: str
  risk_level: Optional[str] = None
  summary: str = ""
  created_at: datetime
  task_id: Optional[str] = None


# 统一信封 data 负载模型
class ReportListData(BaseModel):
  items: List[ReportListItem] = Field(default_factory=list)
  total: int = 0
  limit: int = 20


class ReportDetailData(BaseModel):
  report_id: str
  report: Optional[dict[str, Any]] = None

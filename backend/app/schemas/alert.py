"""预警 API 契约（占位）。

规划：doc/后端开发总体规划-Services-LangGraph-MCP.md §1.3 alert 域
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class AlertStatus(str, Enum):
  active = "active"
  acknowledged = "acknowledged"
  resolved = "resolved"


class AlertSeverity(str, Enum):
  low = "low"
  medium = "medium"
  high = "high"
  critical = "critical"


class AlertListItem(BaseModel):
  alert_id: str
  alert_type: str
  severity: AlertSeverity
  status: AlertStatus
  title: str
  affected_service: Optional[str] = None
  evidence_count: int = 1
  created_at: datetime
  updated_at: datetime


class AlertAckRequest(BaseModel):
  operator: Optional[str] = Field(default=None, description="确认人")


# 统一信封 data 负载模型
class AlertListData(BaseModel):
  items: List[AlertListItem] = Field(default_factory=list)
  total: int = 0


class AlertAckData(BaseModel):
  alert_id: str
  status: AlertStatus = AlertStatus.acknowledged

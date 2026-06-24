"""AI日志问答数据模型"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class LogQARequest(BaseModel):
    """日志问答请求"""
    question: str = Field(description="用户问题")
    context: Optional[dict] = Field(default=None, description="上下文信息")


class LogQASource(BaseModel):
    """回答来源"""
    timestamp: str = Field(description="日志时间")
    level: str = Field(description="日志级别")
    service: str = Field(description="服务名称")
    message: str = Field(description="日志消息")


class LogQAAnswer(BaseModel):
    """问答回答"""
    answer_id: str = Field(description="回答ID")
    question: str = Field(description="用户问题")
    answer: str = Field(description="AI回答")
    confidence: float = Field(description="置信度")
    sources: List[LogQASource] = Field(description="引用来源")
    timestamp: datetime = Field(description="回答时间")
    type: str = Field(description="回答类型")

"""统一 API 响应信封。

所有 v1 接口统一返回 `{ ok, data, error }` 结构，简化前端处理：
- 成功：`ok=true`，业务负载在 `data`，`error=null`。
- 失败：`ok=false`，`data=null`（或部分降级数据），`error={ code, message }`。

设计约束：
- 信封只负责包裹，不承载业务逻辑；service 层返回结构保持不变，由 API 层适配为信封。
- `data` 为强类型泛型，便于 FastAPI 生成 OpenAPI 文档与前端类型推导。
"""

from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field, model_serializer

T = TypeVar("T")


class ApiCode:
    """统一错误码常量；成功时 error 为 null，不使用 OK 码。"""

    ES_UNAVAILABLE = "es_unavailable"
    QUERY_FAILED = "query_failed"
    INVALID_PARAM = "invalid_param"
    NOT_FOUND = "not_found"
    DIAGNOSIS_FAILED = "diagnosis_failed"
    GRAPH_FAILED = "graph_failed"
    INTERNAL_ERROR = "internal_error"


class ErrorInfo(BaseModel):
    code: str
    message: str = ""


class ApiResponse(BaseModel, Generic[T]):
    ok: bool = Field(True, serialization_alias="ok")
    data: Optional[T] = Field(None, serialization_alias="data")
    error: Optional[ErrorInfo] = Field(None, serialization_alias="error")
    
    @model_serializer
    def serialize(self) -> dict:
        """确保所有字段都被序列化，包括默认值"""
        return {
            "ok": self.ok,
            "data": self.data,
            "error": self.error
        }


def ok_envelope(data: T | None = None) -> ApiResponse[T]:
    """构造成功信封。"""
    return ApiResponse(ok=True, data=data, error=None)


def error_envelope(code: str, message: str = "", *, data: T | None = None) -> ApiResponse[T]:
    """构造失败信封；允许携带部分降级 data。"""
    return ApiResponse(ok=False, data=data, error=ErrorInfo(code=code, message=message))

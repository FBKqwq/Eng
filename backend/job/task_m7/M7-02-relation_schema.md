# M7-02：关系发现输出 schema（RelationChainOutput）

## Agent 角色

Schema Agent — 在链层结构化输出模型中新增关系发现的 Pydantic 模型。

## 唯一负责文件

```
app/services/langchain/chain_schemas.py
```

## 禁止修改

- 已有的 `ReportChainOutput` / `DiagnosisChainOutput` 字段（除非确为 bug）
- 其他 langchain 文件

## 前置依赖

- M3 完成（chain_schemas.py 已存在 ReportChainOutput / DiagnosisChainOutput）

## 详细任务内容

新增两个模型（追加到文件末尾，复用现有 import 风格）：

### `RelationItem(BaseModel)`
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `relation_type` | `Literal["temporal_correlation","causal_hypothesis","co_occurrence"]` | 关系类型，默认 `temporal_correlation` |
| `description` | `str = ""` | 一句话中文描述 |
| `entities` | `list[str] = Field(default_factory=list)` | 涉及指标/服务/错误码 |
| `confidence` | `float = Field(default=0.0, ge=0.0, le=1.0)` | 置信度 |
| `evidence_refs` | `list[str] = Field(default_factory=list)` | 证据引用 |

- 为 `confidence` 加 `field_validator(mode="before")`，容忍 None/越界/非数值，钳制到 [0,1]（与 `DiagnosisChainOutput.normalize_confidence` 同风格）。

### `RelationChainOutput(BaseModel)`
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `relations` | `list[RelationItem] = Field(default_factory=list)` | 关系列表，LLM 无产出时为空 |

### 约定
- 字段命名须与 **M7-01 的 RELATION_PROMPT** 完全一致（本文件为字段真相源）。
- 简体中文注释；不要 commit。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `RelationItem` / `RelationChainOutput` 可正常实例化与默认构造 |
| AC-02 | `confidence` 校验器对 None/越界值钳制到 [0,1] |
| AC-03 | 不破坏既有两个模型；`python -c "from app.services.langchain.chain_schemas import RelationChainOutput"` 通过 |
| AC-04 | 更新 `task_m7/STATUS.md` 中 M7-02 行 |

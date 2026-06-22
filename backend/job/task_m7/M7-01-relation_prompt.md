# M7-01：隐藏关系发现 Prompt（RELATION_PROMPT）

## Agent 角色

Prompt Agent — 填充关系发现 Prompt 模板，供 `relation_chain` 调用。

## 唯一负责文件

```
app/services/langchain/prompts.py
```

## 禁止修改

- 其他 langchain 文件（relation_chain、chain_schemas 等）
- 已实现的 REPORT/DIAGNOSIS/ALERT/EVIDENCE_SUMMARY 四个模板的语义（除非确为 bug）

## 前置依赖

- M3 完成（prompts.py 已存在，`RELATION_PROMPT` 当前为 M7 占位文案）

## 详细任务内容

当前 `prompts.py` 中：
```python
RELATION_PROMPT = """[M7 待实现] 隐藏关系发现 Prompt。..."""
```
需将其替换为可投产的中文 Prompt，并保持 `_PROMPT_REGISTRY["relation"]` 指向它（注册项已存在，无需改动注册结构）。

### Prompt 设计要求

1. **角色设定**：电商日志关联分析专家，从证据包中发现「指标/事件之间的隐藏因果或相关关系」（例如「请求高峰 → 随后支付失败率上升」「某服务延迟升高 → 下游错误增多」）。
2. **输入说明**：证据包（evidence_package）含多模板聚合摘要（traffic/errors/latency/funnel 等）与样本日志摘要；时间窗已给定。
3. **输出格式**：严格输出 JSON，字段需与 **M7-02 的 `RelationChainOutput`** 对齐：
   - `relations`: 数组，每项含
     - `relation_type`: 关系类型（如 `temporal_correlation` / `causal_hypothesis` / `co_occurrence`）
     - `description`: 一句话中文描述
     - `entities`: 涉及的指标/服务/错误码名称列表
     - `confidence`: 0~1 置信度
     - `evidence_refs`: 支撑该关系的证据引用（聚合模板名或样本片段标识）
4. **约束**：只能基于证据包内出现的实体下结论；无法发现关系时输出 `{"relations": []}`；不得编造数据。
5. **风格**：与 REPORT/DIAGNOSIS 模板保持一致的措辞与结构（便于 output_parsers 复用 JSON 修复路径）。

### 约定
- 与 M7-02 字段命名严格一致（你们需对齐；以 chain_schemas 为字段真相源）。
- 简体中文；不要 commit。

## 验收标准（AC）

| # | 标准 |
| --- | --- |
| AC-01 | `get_prompt("relation")` 返回非占位的完整 Prompt |
| AC-02 | Prompt 明确要求 JSON 输出且字段与 `RelationChainOutput` 对齐 |
| AC-03 | 不破坏其余四个模板与注册结构 |
| AC-04 | 更新 `task_m7/STATUS.md` 中 M7-01 行 |

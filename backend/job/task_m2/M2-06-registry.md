# M2-06：工具注册中心 registry

## Agent 角色

Registry 专项 Agent — **LangChain StructuredTool 注册 + 读写分离**。

## 唯一负责文件

```
app/services/tools/registry.py
```

## 可修改的附加文件

```
requirements.txt   # 追加 langchain-core（版本与项目 pydantic 2.x 兼容）
```

## 禁止修改

- M2-01~05 各工具实现逻辑（只 import）
- `create_mcp_server` 完整实装（M7；可保留 `NotImplementedError` 或返回 None + 文档说明）

## 前置依赖

- M2-01 ~ M2-05 均为 `已完成`/`已合并`

## 开发要求

### 1. `get_langchain_tools(include_write_tools=False)`

- 为 10 个工具函数各建 `StructuredTool`（name、description、args_schema、func）
- 默认列表：**9 个读工具**（1~5、8~10）
- `include_write_tools=True` 时追加 6、7

### 2. `list_registered_tool_names()`

- 返回与注册一致的有序名称列表（10 个）

### 3. `create_mcp_server()`

- 保持占位，注释指向 M7

### 4. 依赖

- `langchain-core` 写入 `requirements.txt`

## 验收标准

| # | 标准 |
| --- | --- |
| AC-01 | `len(get_langchain_tools()) == 9` |
| AC-02 | `len(get_langchain_tools(include_write_tools=True)) == 10` |
| AC-03 | 每个 StructuredTool 可 `.invoke` 合法入参（mock 环境） |
| AC-04 | requirements 已含 langchain-core |
| AC-05 | 更新 STATUS 本行 |

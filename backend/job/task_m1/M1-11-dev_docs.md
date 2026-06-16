# M1-11：DEV 文档收敛

## Agent 角色

文档维护专项 Agent — **仅在 M1 全部 Service/API 任务合并后，统一更新 DEV 基线**。

## 唯一负责文件

```
app/services/elasticsearch/DEV.md
app/tasks/DEV.md
```

## 禁止修改

- 任何 `.py` 业务代码与测试代码
- `backend/DEV.md`（可选：若需更新，须在本任务显式申请扩展文件列表）

## 前置依赖

- M1-01 ~ M1-06 均已合并
- M1-07 ~ M1-10 测试已就绪（至少离线 mock 用例通过）

## 开发要求

### 1. 更新 `elasticsearch/DEV.md`

必须更新以下章节：

| 章节 | 内容 |
| --- | --- |
| 模块总览 | 7 个文件及职责（含四个 M1 新模块真实状态） |
| 已实现功能清单 | field_catalog / index_service / aggregation / context 的已实现能力列表 |
| 待开发功能清单 | P3 聚合缓存等；移除已完成的 P0 项 |
| 模块状态表 | 风险等级调整：search/health 低，M1 四模块中 |
| 真实实现与设计愿景差异 | 拆索引 vs 当前 Logstash 单索引回退说明 |
| 开发日志区 | 追加一行：M1 完成日期、涉及文件、验收结论 |

### 2. 更新 `app/tasks/DEV.md`

| 章节 | 内容 |
| --- | --- |
| 模块总览 | 增加 `init_indices.py` |
| 已实现功能清单 | `python -m app.tasks.init_indices` 用法 |
| 开发日志区 | 追加 M1-03 记录 |

### 3. 文档约束

- 简体中文
- 不得与 `task_m1/README.md` 总体验收清单矛盾
- 如实标注：Logstash 路由未改时拆索引收益受限

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 范围 | git diff 仅含上述两个 DEV.md |
| AC-02 | 状态表 | elasticsearch DEV 模块状态表已更新日期为 M1 完成日 |
| AC-03 | init 文档 | tasks DEV 含 init_indices 启动命令 |
| AC-04 | 无代码 | diff 中无 `.py` 文件 |

## 完成定义（DoD）

- [ ] M1-01~M1-10 已全部合并后再执行本任务
- [ ] 两个 DEV.md 更新完成
- [ ] AC-01~AC-04 通过

## 执行时机

**必须最后一个执行**，避免与开发 Agent 同时修改 DEV.md。

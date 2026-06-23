# F7-03：Kibana 链接 kibana_links

## Agent 角色

工具专项 Agent — **环境配置与 Kibana 深链生成**。

## 唯一负责文件

```
location/frontend/.env.example
src/utils/kibanaLinks.js
```

## 禁止修改

- views、components（消费方自行 import utils）

## 前置依赖

- F3 `VITE_KIBANA_URL` 约定
- 后端 `kibana_generate_link` 契约（或前端拼接 Discover URL 规则）

## 开发要求

### 1. .env.example

```bash
VITE_KIBANA_URL=http://localhost:5601
# 可选：VITE_KIBANA_DEFAULT_INDEX_PATTERN=app-logs-*
```

### 2. kibanaLinks.js

- `getKibanaBaseUrl()` — 读 env，无则 null
- `buildDiscoverLink({ index, query, timeRange })` — 生成外链
- `buildDashboardLink(id)` — 若有
- 无 URL 时返回 null，调用方隐藏按钮

### 3. 约束

- 不直连 Kibana API；仅生成链接
- 简体中文注释

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | env | .env.example 文档化 |
| AC-02 | discover | 链接可拼出 |
| AC-03 | 空配置 | 无 URL 返回 null |
| AC-04 | 构建 | 通过 |

## 完成定义（DoD）

- [ ] 仅修改上述两文件
- [ ] 更新 STATUS F7-03 行

## 下游消费说明

- F3 ConfigSnapshotCard、监控页「在 Kibana 中打开」扩展位

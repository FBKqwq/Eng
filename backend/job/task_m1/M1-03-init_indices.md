# M1-03：索引初始化任务 init_indices

## Agent 角色

Task 层专项 Agent — **仅新建索引初始化 CLI 入口**，调用 M1-02 已实现的 service。

## 唯一负责文件

```
app/tasks/init_indices.py   （新建）
```

## 禁止修改

- `index_service.py` 及任何 `services/` 下其他文件
- `api/`、`schemas/`、测试文件、`DEV.md`

## 前置依赖

- **必须等待 M1-02 合并**：`app.services.elasticsearch.index_service.init_all_indices` 已实现且非占位

## 开发要求

### 1. 脚本行为

```bash
python -m app.tasks.init_indices
```

可选参数（建议实现）：

| 参数 | 说明 |
| --- | --- |
| `--verify-only` | 只调用 `verify_templates()`，不创建 |
| `--skip-analysis` | 跳过 `create_analysis_indices`（需在 service 层支持或本脚本分步调用前三函数） |

若 service 未提供分步跳过，则最小实现为：无参数时调用 `init_all_indices()`。

### 2. 输出规范

- 成功：stdout 打印 JSON 或结构化中文摘要（每 step 的 ok/error）
- 失败：`sys.exit(1)`，stderr 打印可诊断错误
- 不吞异常：捕获后格式化退出

### 3. 实现约束

```python
# 允许的唯一 service 导入
from app.services.elasticsearch.index_service import init_all_indices, verify_templates
```

- 不得在本文件内定义 ES mapping 或重复 template 逻辑
- 遵循 `run_log_producer.py` 的任务脚本风格（`if __name__ == "__main__"`）

## 验收标准

| 编号 | 验收项 | 通过条件 |
| --- | --- | --- |
| AC-01 | 执行成功 | ES 在线时 `python -m app.tasks.init_indices` 退出码 0 |
| AC-02 | 幂等 | 连续执行两次均为退出码 0 |
| AC-03 | ES 离线 | 退出码非 0，stderr 有明确提示 |
| AC-04 | 无越权 | `init_indices.py` 内无 mapping dict、无 `get_es_client` 直接调用（除非 verify 模式仅调 verify_templates） |
| AC-05 | import | `python -m compileall app/tasks/init_indices.py` 通过 |

## 完成定义（DoD）

- [ ] 仅新增 `app/tasks/init_indices.py`
- [ ] 不修改 `index_service.py`
- [ ] AC-01~AC-05 通过

## 下游说明

- M1-11 将在 `app/tasks/DEV.md` 登记本任务用法

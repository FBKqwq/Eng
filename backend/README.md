# Backend Scaffold

基于 FastAPI 的课设后端骨架，职责如下：
- 健康检查与系统状态接口
- Kafka 日志生产者
- Elasticsearch 查询封装
- 规则分流与智能诊断占位
- 模拟电商日志生成任务

## 启动
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 目录说明
- `app/api/v1`：API 路由
- `app/services`：Kafka / ES / 诊断 / 模拟业务逻辑
- `app/tasks`：可独立执行任务

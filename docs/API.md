# AgentOrchestrator API 文档

## Agent Core (Python FastAPI) — port 8000

### 健康检查

```http
GET /health
```

响应:
```json
{
  "status": "ok",
  "agents": 2,
  "tools": 5
}
```

---

### Agent

#### 创建 Agent

```http
POST /agents
Content-Type: application/json

{
  "name": "data-analyst",
  "description": "数据分析专家",
  "system_prompt": "你是一个精通SQL和数据分析的AI助手...",
  "tools": ["read_file", "execute_sql", "list_tables"],
  "max_iterations": 8,
  "temperature": 0.3
}
```

#### 列出所有 Agent

```http
GET /agents
```

#### 执行 Agent 任务

```http
POST /agents/{agent_name}/run
Content-Type: application/json

{
  "task": "分析 sales 表的月度趋势并给出优化建议",
  "context": {}
}
```

响应:
```json
{
  "agent": "data-analyst",
  "status": "completed",
  "response": "根据分析结果...",
  "iterations": 3,
  "events": [
    {"type": "thinking", "content": "我需要先查看表结构..."},
    {"type": "tool_call", "content": "调用 list_tables"},
    {"type": "result", "content": "分析完成"}
  ]
}
```

---

### 工作流

#### 顺序/并行工作流

```http
POST /workflows
Content-Type: application/json

{
  "agents": ["analyzer", "validator", "reporter"],
  "task": "分析项目代码质量并生成报告",
  "mode": "sequential"
}
```

#### DAG 工作流

```http
POST /workflows/dag
Content-Type: application/json

[
  {
    "agent": "analyzer",
    "step_name": "代码分析",
    "depends_on": []
  },
  {
    "agent": "validator",
    "step_name": "结果校验",
    "depends_on": ["代码分析"]
  }
]
```

---

## Streamlit Dashboard — port 8501

可视化仪表盘，查看 Agent 状态、任务执行情况。通过 Docker Compose 或手动 `streamlit run dashboard/app.py` 启动。

---

## 错误响应格式

```json
{
  "detail": "Agent 'xxx' not found"
}
```

HTTP 状态码:
- `200` 成功
- `201` 创建成功
- `400` 请求参数错误
- `404` 资源不存在
- `500` 服务内部错误

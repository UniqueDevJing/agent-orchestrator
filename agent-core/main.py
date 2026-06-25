"""Agent 编排核心 — FastAPI 服务"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.base import AgentConfig as AgentConfigDC
from agents.llm_agent import LLMAgent
from orchestration.workflow import WorkflowEngine, WorkflowStep
from tools.registry import tool_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 持久化已创建的 Agent
_agents: dict[str, AgentConfigDC] = {}
_workflow_engine = WorkflowEngine()


class AgentConfigRequest(BaseModel):
    name: str
    description: str = ""
    system_prompt: str = ""
    tools: list[str] = []
    max_iterations: int = 5
    temperature: float = 0.7


class TaskRequest(BaseModel):
    task: str
    context: dict = {}


class WorkflowRequest(BaseModel):
    agents: list[str]
    task: str
    mode: str = "sequential"  # sequential | parallel | dag


@asynccontextmanager
async def lifespan(app: FastAPI):
    await tool_registry.load_tools()
    logger.info(f"Agent Core 启动，已加载 {len(tool_registry.list_tools())} 个工具")
    yield
    logger.info("Agent Core 关闭")


app = FastAPI(title="Agent Core", version="0.4.0", lifespan=lifespan)


@app.post("/agents")
async def create_agent(config: AgentConfigRequest):
    for tool_name in config.tools:
        if not tool_registry.has_tool(tool_name):
            raise HTTPException(status_code=400, detail=f"工具 {tool_name} 不存在")
    dc = AgentConfigDC(
        name=config.name,
        description=config.description,
        system_prompt=config.system_prompt,
        tools=config.tools,
        max_iterations=config.max_iterations,
        temperature=config.temperature,
    )
    _agents[config.name] = dc
    return {"status": "ok", "agent": dc.__dict__}


@app.post("/agents/{agent_name}/run")
async def run_agent(agent_name: str, request: TaskRequest):
    if agent_name not in _agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} 不存在，请先创建")
    config = _agents[agent_name]
    agent = LLMAgent(config)
    try:
        result = await agent.run(request.task, request.context or None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "agent": agent_name,
        "status": agent.status.value,
        "response": result.get("result", ""),
        "iterations": result.get("iterations", 0),
        "events": [
            {"type": e.event_type, "content": e.content}
            for e in agent.events
        ],
    }


@app.post("/workflows")
async def run_workflow(request: WorkflowRequest):
    # 验证所有 agent 已创建
    agents = []
    for name in request.agents:
        if name not in _agents:
            raise HTTPException(status_code=404, detail=f"Agent {name} 不存在，请先创建")
        agents.append(LLMAgent(_agents[name]))

    try:
        if request.mode == "parallel":
            results = await _workflow_engine.run_parallel(agents, request.task)
        elif request.mode == "dag":
            raise HTTPException(status_code=400, detail="DAG 模式需要通过 /workflows/dag 端点提交")
        else:
            results = await _workflow_engine.run_sequential(agents, request.task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "ok",
        "mode": request.mode,
        "task": request.task,
        "results": results,
    }


@app.post("/workflows/dag")
async def run_workflow_dag(steps: list[dict], task: str):
    """DAG 工作流：steps 格式 [{"agent": "name", "step": "s1", "depends": []}]"""
    workflow_steps = []
    for s in steps:
        agent_name = s["agent"]
        if agent_name not in _agents:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} 不存在")
        workflow_steps.append(WorkflowStep(
            agent=LLMAgent(_agents[agent_name]),
            step_name=s.get("step", agent_name),
            depends_on=s.get("depends", []),
        ))
    try:
        results = await _workflow_engine.run_dag(workflow_steps, task)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok", "task": task, "results": results}


@app.get("/agents")
async def list_agents():
    return [
        {
            "name": c.name,
            "description": c.description,
            "tools": c.tools,
            "max_iterations": c.max_iterations,
        }
        for c in _agents.values()
    ]


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agents": len(_agents),
        "tools": len(tool_registry.list_tools()),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

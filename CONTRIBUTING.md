# Contributing to AgentOrchestrator

## Getting Started

```bash
git clone https://github.com/UniqueDevJing/agent-orchestrator.git
cd agent-orchestrator

# Agent Core (Python)
cd agent-core
pip install -r requirements.txt
uvicorn main:app --reload
```

## Development

```bash
# Run tests
cd agent-core && pytest tests/ -v
```

## Adding Custom Tools

1. Create a tool function in `agent-core/tools/builtin.py`
2. Add it to `load_tools()` in `tools/registry.py`
3. Add tests

```python
# builtin.py
async def my_tool(param: str) -> dict:
    """My custom tool description"""
    return {"result": f"Result: {param}"}

# registry.py load_tools()
self.register(my_tool)
```

## Pull Request

1. Update CHANGELOG.md
2. Ensure all tests pass
3. Describe what and why in the PR description

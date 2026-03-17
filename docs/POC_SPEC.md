

## Phase 1: DAG Engine Components

After Phase 0, implement DAG Engine in three components:

### Task DAG Generator
- Parse Plan JSON
- Build dependency graph
- Topological sort
- Generate execution queue

File structure:
- `/poc/dag_generator.py` - Task DAG Generator

### Workflow Engine
- Manage execution queue
- Track step status
- Submit steps to Worker Pool
- Handle workflow-level errors

File structure:
- `/poc/workflow_engine.py` - Workflow Engine

### Worker Pool
- Execute steps in parallel
- Apply retry logic
- Return results to Workflow Engine

File structure:
- `/poc/worker_pool.py` - Worker Pool


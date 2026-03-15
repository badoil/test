# PoC Specification: Hybrid Graph + DAG Runtime

This document defines Proof-of-Concept (PoC) plan JSON schema, Tool Adapter contract, State Manager, and Recovery policy for a hybrid Graph + DAG agent runtime. The goal is to standardize messages between Runtime → Planner → DAG → State Manager → Tool layers with built-in resilience for production-level deployments.

## Goals
- Define a minimal, unambiguous Plan JSON schema for T1–T3 PoC with state persistence.
- Define Tool Adapter contract (input, output, error format).
- Define State Manager interface for state persistence and recovery.
- Define Recovery/Retry policies for fault tolerance.
- Provide example plans and recommended validation checks.

---

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│         Runtime Layer                        │
│  (User Request → Plan Generation)            │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│         Planner                             │
│  (Goal → Plan JSON with state_config)        │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│         DAG Engine                           │
│  (Topological execution + Recovery Logic)    │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│         State Manager                       │
│  (State Persistence + Recovery)             │
│  (Redis/DB backend)                        │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│         Tool Adapters                       │
│  (Standardized I/O)                        │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│         Tools (Search, Tokenize, etc.)      │
└─────────────────────────────────────────────┘
```

**Key Design Principles:**
- **DAG for Execution**: Topological order, no cycles
- **State for Resilience**: Persist state at each step
- **Recovery for Fault Tolerance**: Auto-retry or cache reuse on failure
- **Graph Structure**: Simple DAG structure (no complex state machine transitions)

---

## Plan JSON (top-level)

A Plan is an object describing the high-level steps to achieve a user goal. Minimal fields:

- id (string): unique plan id
- user_id (string|null): optional user/session id
- goal (string): natural-language short description of the user goal
- steps (array of Step objects): ordered steps (DAG nodes)
- state_config (object, optional): state persistence configuration
  - enabled (boolean): whether to persist state
  - backend (string): "redis" | "memory" | "file"
  - ttl_seconds (integer, optional): time-to-live for state
- created_at (ISO8601)
- metadata (object): free-form

Example:

{
  "id": "plan-0001",
  "user_id": "session-42",
  "goal": "Summarize the latest sales report",
  "state_config": {
    "enabled": true,
    "backend": "redis",
    "ttl_seconds": 3600
  },
  "created_at": "2026-03-05T09:00:00Z",
  "steps": [ ... ]
}

---

## Step object (task node)

Each step is a node in the plan. For PoC we use a linear/acyclic structure and allow optional `depends_on` to express simple DAGs.

Fields:
- id (string): unique step id (within plan)
- name (string): human-readable name, e.g. "search_docs"
- tool (string): tool identifier, e.g. "search", "tokenize", "summarize"
- inputs (object): tool-specific inputs (see Tool IO spec)
- depends_on (array[string], optional): ids of steps this step depends on
- timeout_ms (integer, optional): maximum runtime
- retry (object, optional): retry configuration
  - attempts (integer): max retry attempts (default: 3)
  - backoff_ms (integer): backoff between retries in ms (default: 1000)
  - strategy (string): "fixed" | "exponential" (default: "exponential")
- recovery (object, optional): recovery configuration
  - enabled (boolean): whether to enable recovery (default: true)
  - strategy (string): "retry" | "cache" | "manual" (default: "retry")
- metadata (object, optional)

Example step:

{
  "id": "s1",
  "name": "search",
  "tool": "mock_search",
  "inputs": { "query": "sales report March 2026", "top_k": 3 },
  "retry": {
    "attempts": 3,
    "backoff_ms": 1000,
    "strategy": "exponential"
  },
  "recovery": {
    "enabled": true,
    "strategy": "retry"
  }
}

---

## Tool Adapter contract (I/O)

Each Tool must implement a small HTTP/Function-like contract so the Task Graph Engine can call it uniformly.

Tool Input: JSON object with the fields defined by the step.inputs. Additionally, the caller will provide:
- plan_id (string)
- step_id (string)
- user_id (string|null)

Example call (payload):
{
  "plan_id": "plan-0001",
  "step_id": "s1",
  "user_id": "session-42",
  "inputs": { "query": "sales report March 2026", "top_k": 3 }
}

Tool Output (success):
- status: "ok"
- outputs: object (tool-defined structured result)
- state (object, optional): step state to persist
- logs: optional array<string>
- metrics: optional object

Example success:
{
  "status": "ok",
  "outputs": {
    "documents": [ { "id": "doc-1", "text": "..." }, ... ]
  },
  "state": {
    "count": 3,
    "queries": ["sales report March 2026"]
  },
  "metrics": {
    "duration_ms": 45,
    "tokens": 123
  }
}

Tool Output (error):
{
  "status": "error",
  "error": {
    "code": "timeout" | "tool_error" | "invalid_input" | "retryable",
    "message": "human readable",
    "details": { ... },
    "retryable": true  // whether the error is retryable
  }
}

---

## State Manager Interface

The State Manager is responsible for persisting step state and recovery across executions.

### Interface

```python
class StateManager:
    async def save_step_state(
        self,
        plan_id: str,
        step_id: str,
        state: dict,
        ttl_seconds: Optional[int] = None
    ) -> bool

    async def get_step_state(
        self,
        plan_id: str,
        step_id: str
    ) -> Optional[dict]

    async def delete_plan_state(
        self,
        plan_id: str
    ) -> bool

    async def get_plan_status(
        self,
        plan_id: str
    ) -> Optional[dict]
```

### Backend Implementations

**Memory (PoC default):**
- In-memory dictionary
- No persistence across restarts
- Good for testing

**Redis (Production):**
- Distributed state
- TTL support
- Fast reads/writes

**File (Development):**
- JSON files per plan
- Good for debugging

---

## Recovery Policy

When a step fails, the DAG Engine will attempt recovery based on the `recovery` configuration.

### Recovery Strategies

**1. Retry (default)**
- Re-execute the step with exponential backoff
- Configurable attempts and backoff
- Only for retryable errors

**2. Cache**
- Load previously cached state (if available)
- Useful for expensive operations
- No re-execution

**3. Manual**
- Mark step as failed and wait for human intervention
- Requires external resubmission
- Useful for non-retryable errors

### Retry Logic

```python
async def execute_step_with_retry(step, recovery_config):
    for attempt in range(recovery_config["attempts"]):
        try:
            result = await execute_step(step)
            # Save state on success
            await state_manager.save_step_state(
                plan_id, step["id"], result["state"]
            )
            return result
        except Exception as e:
            if attempt == recovery_config["attempts"] - 1:
                # Final attempt failed, try cache or fail
                cached = await state_manager.get_step_state(plan_id, step["id"])
                if cached and recovery_config["strategy"] == "cache":
                    return cached
                raise
            # Exponential backoff
            backoff = recovery_config["backoff_ms"] * (2 ** attempt)
            await asyncio.sleep(backoff / 1000)
```

---

## Validation & Lightweight Schema

For PoC we recommend JSON Schema validation for Plan and Step objects. Minimal checks:
- plan.id unique string
- steps is non-empty array
- each step has id, tool, inputs (object)
- depends_on entries reference existing step ids (no cycles in PoC)
- state_config.backend is one of: "memory", "redis", "file"
- retry.strategy is one of: "fixed", "exponential"
- recovery.strategy is one of: "retry", "cache", "manual"

We will add a simple validator in /poc/utils/validator.py to surface schema errors early.

---

## Examples

Full plan example (two-step RAG-like flow with state):

{
  "id": "plan-0002",
  "user_id": "session-73",
  "goal": "Find and summarize the FAQ about refunds",
  "state_config": {
    "enabled": true,
    "backend": "redis",
    "ttl_seconds": 1800
  },
  "created_at": "2026-03-05T09:12:00Z",
  "steps": [
    {
      "id": "s1",
      "name": "search_faq",
      "tool": "mock_search",
      "inputs": { "query": "refund policy faq", "top_k": 5 },
      "retry": {
        "attempts": 3,
        "backoff_ms": 1000,
        "strategy": "exponential"
      },
      "recovery": {
        "enabled": true,
        "strategy": "retry"
      }
    },
    {
      "id": "s2",
      "name": "summarize_hits",
      "tool": "mock_summarize",
      "depends_on": ["s1"],
      "inputs": { "source_step": "s1", "mode": "short" },
      "retry": {
        "attempts": 2,
        "backoff_ms": 500,
        "strategy": "fixed"
      }
    }
  ]
}


---

## Tool Catalog (PoC)

For the PoC we will implement these tools:
- mock_search: returns canned documents for a query
  - inputs: { query: string, top_k: int }
  - outputs: { documents: [{id, text, score}] }
  - state: { query: string, count: int }

- tokenize (C++ tool): splits text into tokens
  - inputs: { text: string }
  - outputs: { tokens: [string] }
  - state: { token_count: int }

- mock_summarize: simple summarizer (Python) producing short text
  - inputs: { source_step: string }
  - outputs: { summary: string }
  - state: { input_length: int, output_length: int }

---

## Execution semantics (Hybrid)

1. **Plan Validation**: Validate plan schema and DAG structure
2. **State Initialization**: Initialize State Manager based on state_config
3. **Topological Execution**: Execute steps in topological order
   - Check dependencies are satisfied
   - Check if cached state exists (for recovery strategy "cache")
4. **Step Execution**: Execute step with retry logic
   - On success: Save state to State Manager
   - On failure: Apply recovery policy (retry/cache/manual)
5. **State Cleanup**: Delete plan state after completion (or after TTL)

**Key Differences from Pure DAG:**
- **State Persistence**: Each step state is saved for recovery
- **Retry with Backoff**: Automatic retry with exponential backoff
- **Cache Reuse**: Can skip expensive steps if cached state exists
- **Manual Recovery**: Can pause execution for human intervention

---

## Minimal Tests

- Schema validator tests: invalid plan (missing step inputs, invalid recovery strategy) should fail validation.
- State manager tests: save/get/delete state operations.
- Retry logic tests: verify exponential backoff and max attempts.
- Recovery tests: cache reuse on failure, manual recovery flag.
- End-to-end PoC test: a POST /chat with a simple goal yields a final response containing the summary from mock_summarize, with state persisted in Redis.

---

## Phase 0: State Manager & Recovery

Before implementing the DAG Engine, we will implement:
1. State Manager interface (memory backend for PoC)
2. Retry logic with exponential backoff
3. Recovery policy (retry/cache/manual)
4. Integration with Tool Adapter contract

File structure:
- `/poc/state_manager.py` - State Manager implementation
- `/poc/recovery.py` - Retry and recovery logic
- `/poc/utils/validator.py` - JSON Schema validator

---

File created by javi — PoC spec (hybrid Graph + DAG runtime with state management).

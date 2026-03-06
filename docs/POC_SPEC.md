# PoC Specification: Plan Schema & Tool IO

This document defines the Proof-of-Concept (PoC) plan JSON schema and the Tool Adapter input/output contract. The goal is to standardize the messages between Runtime → Planner → DAG → Tool layers so we can iterate quickly and swap implementations.

## Goals
- Define a minimal, unambiguous Plan JSON schema for T1–T3 PoC.
- Define Tool Adapter contract (input, output, error format).
- Provide example plans and recommended validation checks.

---

## Plan JSON (top-level)

A Plan is an object describing the high-level steps to achieve a user goal. Minimal fields:

- id (string): unique plan id
- user_id (string|null): optional user/session id
- goal (string): natural-language short description of the user goal
- steps (array of Step objects): ordered steps (DAG nodes)
- created_at (ISO8601)
- metadata (object): free-form

Example:

{
  "id": "plan-0001",
  "user_id": "session-42",
  "goal": "Summarize the latest sales report",
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
- retry (object, optional): { attempts: int, backoff_ms: int }
- metadata (object, optional)

Example step:

{
  "id": "s1",
  "name": "search",
  "tool": "mock_search",
  "inputs": { "query": "sales report March 2026", "top_k": 3 }
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
- logs: optional array<string>
- metrics: optional object

Example success:
{
  "status": "ok",
  "outputs": {
    "documents": [ { "id": "doc-1", "text": "..." }, ... ]
  }
}

Tool Output (error):
{
  "status": "error",
  "error": {
    "code": "timeout" | "tool_error" | "invalid_input",
    "message": "human readable",
    "details": { ... }
  }
}

---

## Validation & Lightweight Schema

For PoC we recommend JSON Schema validation for Plan and Step objects. Minimal checks:
- plan.id unique string
- steps is non-empty array
- each step has id, tool, inputs (object)
- depends_on entries reference existing step ids (no cycles in PoC)

We will add a simple validator in /poc/utils/validator.py to surface schema errors early.

---

## Examples

Full plan example (two-step RAG-like flow):

{
  "id": "plan-0002",
  "user_id": "session-73",
  "goal": "Find and summarize the FAQ about refunds",
  "created_at": "2026-03-05T09:12:00Z",
  "steps": [
    {
      "id": "s1",
      "name": "search_faq",
      "tool": "mock_search",
      "inputs": { "query": "refund policy faq", "top_k": 5 }
    },
    {
      "id": "s2",
      "name": "summarize_hits",
      "tool": "mock_summarize",
      "depends_on": ["s1"],
      "inputs": { "source_step": "s1", "mode": "short" }
    }
  ]
}


---

## Tool Catalog (PoC)

For the PoC we will implement these tools:
- mock_search: returns canned documents for a query
  - inputs: { query: string, top_k: int }
  - outputs: { documents: [{id, text, score}] }

- tokenize (C++ tool): splits text into tokens
  - inputs: { text: string }
  - outputs: { tokens: [string] }

- mock_summarize: simple summarizer (Python) producing short text
  - inputs: { source_step: string }
  - outputs: { summary: string }

---

## Execution semantics (PoC)

- The Task Graph Engine will execute steps in topological order. For PoC we execute sequentially: steps without dependencies first, then dependent steps.
- On tool error: the engine marks the step as failed. Behavior is configurable per-plan (retry policy). For PoC default is no retry.
- Each step result is stored in an in-memory results map indexed by step id for downstream steps to reference.

---

## Minimal Tests

- Schema validator tests: invalid plan (missing step inputs) should fail validation.
- End-to-end PoC test: a POST /chat with a simple goal yields a final response containing the summary from mock_summarize.

---

File created by javi — PoC spec (planner/DAG/tool contracts).

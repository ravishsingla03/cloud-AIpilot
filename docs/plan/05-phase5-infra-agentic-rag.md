# Phase 5 — Infrastructure Data & Agentic RAG

Read `docs/plan/00-rules.md` first. Corresponds to the original plan's
Phases 15-20, compressed. This phase is what makes CloudPilot different
from a generic RAG-over-docs project.

## Concepts to teach

- Why live infrastructure state can't be handled like static
  documents — it changes constantly and needs to be queried, not
  embedded
- Structured logs: timestamps, severity, service, error codes,
  identifiers — and why metadata filtering + lexical search often beats
  semantic search here
- What an "agent" is doing here, concretely: deciding *which tools to
  call* based on the question, not just retrieving from a fixed corpus
- Tool safety: the hard split between read-only tools (safe to call
  freely) and mutating tools (must require explicit confirmation)
- Why authorization/permissions for mutating actions matter even in a
  portfolio project — it demonstrates production thinking
- Conversation memory: why you can't just concatenate the entire
  history into every prompt forever (token limits), and what
  alternatives exist (summarization, relevant-history retrieval)

## Build tasks

1. **Mock infrastructure.** Create a mock Kubernetes-like state (JSON:
   cluster, nodes, pods, events, deployments). Expose read-only tool
   functions: `get_pod_status()`, `get_pod_logs()`, `get_node_status()`,
   `get_kubernetes_events()`, `get_deployment_status()`.

2. **Log analysis.** Add a small set of realistic logs (Kubernetes,
   Ceph, MinIO, nginx, application). Support searching them by
   metadata (service, severity, time range) and by keyword — don't
   just dump them through the same embedding pipeline as docs.

3. **Incident database.** Model `incidents` (id, service, severity,
   timestamp, symptoms, root_cause, resolution, logs, tags). Populate a
   handful of realistic examples. Support retrieving similar past
   incidents for a given symptom description.

4. **Agent / planner.** Build a simple planner (not a framework) that,
   given a question, decides which of the tools above (plus
   `search_docs()` / `search_incidents()` from earlier phases) to call,
   in what order, before generating a diagnosis. Start rule-based or
   simple-LLM-driven; keep it inspectable.

5. **Tool safety.** Explicitly separate read-only tools from mutating
   ones (`restart_pod`, `scale_deployment`, `delete_resource`,
   `run_ansible_job`). Mutating tools are disabled by default; when
   enabled, require a "proposed action → user confirmation → execution"
   flow. Never auto-execute a mutation.

6. **Conversation memory.** Implement short-term memory so a follow-up
   like "what logs support that?" resolves "that" correctly, without
   naively sending the full history every time.

## Deliverable

- Mock infra state + working read-only tool functions
- Log search (metadata + keyword) over sample logs
- Incident model + similar-incident retrieval
- Working agent/planner that selects and sequences tools for a given
  question, producing a diagnosis with citations across docs, logs,
  incidents, and live state
- Explicit read-only/mutating tool split, with mutations gated behind
  confirmation (even if only stubbed for now)
- `docs/agent.md`, `docs/tool-calling.md`

## Explicit non-goals for this phase

- No observability/caching/background jobs yet (Phase 6)
- No auth/authorization yet (Phase 6) — though tool safety above is
  related, full user-level authorization comes next
- No React dashboard yet (Phase 7)

## Sample interview questions for this phase

- How do you prevent an agent from executing a dangerous action
  automatically?
- What happens if a tool call fails mid-plan — does the agent retry,
  give up, or ask the user?
- How do you prevent an agent from looping indefinitely?
- Why treat logs differently from documentation in the retrieval
  pipeline?

Wait for confirmation before moving to
`06-phase6-production-engineering.md`.

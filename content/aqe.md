Title: AQE Automata: From Agent Contracts to Verified Regression Tests
Date: 2025-11-01
Modified: 2026-10-29
Category: Open Source Projects
Tags: agentic, quality engineering, ai, testing, temporal, rag, playwright, kubernetes
Slug: aqe
Summary: A technical deep dive into AQE Automata: durable Temporal workflows, contract-grounded test generation, independent review, bounded execution and repair, and versioned regression catalogs backed by traceable evidence.

[AQE — Agentic Quality Engineering](https://github.com/sqe/AQE) is a compound
agent system for turning declared behavior into executable, reviewable tests.
Its control plane, **AQE Automata**, coordinates discovery, generation, review,
execution, diagnosis, and bounded repair. The useful output is not an LLM's
opinion that a system works: it is a test result linked to its source, target,
grounding evidence, and execution attempts.

That distinction matters for AI-native systems. An agent may advertise a skill,
return a convincing answer, and still violate its contract. A generated test can
also pass for the wrong reason. AQE puts deterministic checks, an independent
review boundary, and a real test runtime between generation and publication.

## Watch a full execution run

**[Watch the full AQE execution-run demo on YouTube](https://youtu.be/A5VcteEc_jE).**
The demo is a visual walkthrough with light background music, no voice
narration, and no captions.
The recording accompanies this architecture walkthrough; it is a demonstration
of a particular run, not a benchmark or a guarantee that every target will pass.

[![AQE Automata Observe view with agent handoffs and test activity]({static}/images/aqe-automata.png)](https://youtu.be/A5VcteEc_jE)

*The Observe interface connects workflow activity, test nodes, target versions,
and Temporal history. The counters and health labels belong to the captured
environment, not to a live status feed on this page.*

## The architecture: three distinct planes

AQE separates **coordination**, **execution**, and **evidence**. A dashboard or
API client starts work directly through the Workflow API. A larger agent
platform can instead call AQE through its Bring Your Own Agent (BYOA) adapter.
Both entry paths lead to the same durable workflow rather than separate testing
implementations.

[![Detailed AQE Automata architecture: callers, Temporal stages, evidence storage, and publication gates]({static}/images/aqe-architecture.png)]({static}/images/aqe-architecture.png)

*Open the diagram at full size to inspect the architecture, gates, and feedback
paths. Dashed lines group storage and telemetry relationships; required state
and artifact writes are not optional merely because they are drawn with dashed
connectors.*

- **Workflow API and Temporal** own run identity, stage ordering, timeouts,
  bounded retries, and fleet child workflows. A completed workflow is not
  necessarily a passing test.
- **Generation and Quality Oracle** ground candidates in declared behavior and
  review their meaning before execution. Model approval does not replace a
  real test run.
- **HTTP and browser executors** apply the static gate, run pytest, collect
  results, and optionally repair. A sandbox does not remove the need for
  infrastructure security controls.
- **PostgreSQL and RustFS** retain run state, provenance, source, and execution
  evidence. Retention is not automatic permission to publish that material.
- **GitHub catalogs** preserve promoted tests and confirmed defect reproducers
  against identified target versions. Catalog publication is not production
  release approval.

### Kafka is the platform boundary; Temporal owns the run

The BYOA adapter accepts correlated JSON-RPC tasks on `tasks.aqe` and returns
results on `results.aqe`. It publishes the result before committing the consumed
offset. This is an **at-least-once** integration: replay is possible, and request
identity and downstream idempotency still matter. Kafka is not AQE's internal
generate–execute–repair state machine.

Temporal owns that state machine. Specialist calls are activities with explicit
timeouts and retry policies. The implementation deliberately gives generation a
single activity attempt because it persists a new artifact and does not yet
offer an idempotency key. Retrying a read and retrying an operation that creates
new evidence are different engineering decisions.

Fleet campaigns use child QE workflows and bound requested concurrency to a
maximum of five. Results remain attributable to individual targets rather than
being collapsed into a single ambiguous fleet verdict. Workflow patch markers
preserve replay compatibility as gates evolve; historical workflow executions
should not be mistaken for runs of the latest policy.

## 1. Discover behavior before generating tests

For an agent target, discovery reads its Agent Card, skills, invocation
contracts, version, and executable scenarios. The important question is not
just “does an endpoint respond?” It is “what observable outcome does this
particular skill promise, with what input and evaluation dimensions?”

AQE distinguishes an executable scenario from missing requirements. When every
discovered scenario needs a contract clarification, the workflow returns
`REQUIREMENTS_NEEDED` with zero executed tests and does not generate a suite.
It should not invent a payload, endpoint, or expected answer to fill the gap.
When only some scenarios are executable, those can proceed while the missing
requirements remain explicit.

Optional GitHub grounding is a separate read-only boundary. The caller supplies
an allowlisted repository and pinned source reference. Source analysis augments
the generation request; it does not turn arbitrary repository access into an
implicit authority to write or deploy code.

## 2. Generate an immutable candidate, not an automatic verdict

Generation combines supplied requirements, applicable agent ontology rules,
scenario context, and product knowledge retrieved through Qdrant. Product RAG
is optional: without an active product-knowledge artifact, generation can still
use the declared scenario and ontology. Provenance should distinguish these
cases instead of pretending every test has retrieved product evidence.

The system also has a deterministic declared-contract compiler path for
supported executable contracts. Not every candidate therefore needs to be
invented by a model. The workflow records the generation method and uses it
when deciding whether an Oracle-feedback regeneration is appropriate.

Before a candidate consumes review or execution resources, the static gate
checks its Python structure and testing policy. Tests should express atomic,
observable outcomes, use fixtures for shared setup, map to required skills and
dimensions, and avoid fixed sleeps, swallowed failures, or conditional assertion
skipping. Browser tests favor role, label, and test-id locators with explicit
state waits.

Generated source is stored as an immutable artifact in RustFS, with the task and
grounding metadata recorded in PostgreSQL. The artifact identity matters: review
must refer to the candidate that will actually execute, not a mutable text box
that can change after approval.

## 3. Use the Quality Oracle as a fail-closed review gate

The Quality Oracle reviews the candidate against requirements, ontology,
retrieved evidence, skill coverage, and risk policy. It returns structured
approval or rejection with issues and grounding citations. An unavailable or
non-approving review does not silently authorize execution.

For model-generated candidates, the current workflow permits one regeneration
using structured Oracle feedback, then reviews the new candidate. A second
rejection stops the workflow. The deterministic declared-contract path gets one
review attempt rather than that model-feedback loop.

There are two different mechanisms here: the AST gate checks structural rules;
the Oracle reviews meaning. Neither proves the target's behavior. Even an
independent reviewer can be wrong or share a blind spot with the generator, so
actual execution remains necessary.

## 4. Execute in the correct runtime and read the real result

AQE separates browser-free HTTP, Agent Card, and A2A testing from website
journeys. The agent executor does not need a Chromium installation. The website
executor supplies Playwright Chromium in its own runtime. Requests are routed
by test type, and an executor rejects a persisted task for the wrong mode.

Before each execution, the runtime applies the static quality gate again. It
writes the candidate into a temporary workspace, starts `python -m pytest`,
captures stdout and stderr, and requests JUnit XML. Resource limits, a restricted
environment, and a hard timeout bound the subprocess. Deployment-level
permissions and network isolation remain part of the security boundary: a
temporary directory alone is not a complete untrusted-code sandbox.

The subprocess exit status determines execution success; JUnit supplies counts
for passed, failed, errored, and skipped tests. AQE does not search console text
for a reassuring word and call that a pass.

This produces an important distinction for API consumers: **Temporal
`COMPLETED` means orchestration finished**. Inspect `result.successful`, the
failure/error counts, and the retained evidence before treating the run as a
successful verification. A run can finish durably with a failed test result.

## 5. Repair is bounded, and a green rerun is not the whole story

Execution repair is separate from pre-execution Oracle feedback. When enabled
and configured, the repair client receives the failing source and execution
result. `MAX_REPAIR_ATTEMPTS` defaults to two repairs after the initial run.
Repair can stop earlier when no model is configured, no candidate is returned,
or an attempt succeeds. Every new candidate goes through the static gate and
real execution again.

The repair prompt explicitly forbids weakening, deleting, or changing the
intended observable behavior. That is a policy, not a mathematical guarantee of
semantic equivalence. The current execution loop does not repeat the full
Quality Oracle review after each repair. Review the original and repaired
artifacts and the expected outcome when the risk warrants it; “the model made
the test green” is not sufficient evidence of correctness.

An ordinary failing run is not automatically a product defect. It may expose a
bad generated test, missing credentials, an unavailable dependency, an execution
error, or a genuine assertion failure. Keeping these possibilities distinct is
more useful than making every red result look like a discovered bug.

## 6. Separate operational evidence from the regression catalog

PostgreSQL and RustFS form the operational evidence layer. PostgreSQL keeps
queryable run metadata, target identity, outcomes, and catalog links. RustFS
keeps generated and repaired source and large artifacts. Failed and unpromoted
candidates still have an evidence trail.

GitHub is a narrower, reviewable publication boundary, enabled by catalog
configuration and a scoped token:

- **Validated tests** enter `generated-tests/` only after the execution quality
  gate and pytest pass. Paths identify runtime, test layer, target agent, and
  release version, with a source revision when supplied.
- **Confirmed defect reproducers** enter `generated-findings/` only after
  explicit confirmation with non-empty evidence. The confirmation endpoint
  reruns the persisted test without repair and requires assertion failures with
  zero execution or collection errors.
- **Test defects, environment failures, and untriaged results** remain
  operational evidence rather than being published as product defects.

The generated-catalog workflow then continuously tests the identified target
version. A confirmed-defect reproducer has a deliberately different expectation
from a green regression test: it should continue to reproduce until the defect
is fixed and its catalog disposition is updated. CI also needs network access
to the target; private endpoints may require a properly scoped self-hosted
runner. Sensitive scenarios belong in a private catalog.

Passing execution and successful publication are distinct outcomes. A run can
pass while catalog credentials are absent or a GitHub write fails; inspect
`test_catalog` and `test_catalog_error` instead of assuming a green runtime
result created a repository artifact.

## Observe the handoffs without confusing telemetry with truth

AQE's Observe view connects directed agent handoffs, generated test nodes,
target relationships, and final states, with separate graph and 3D views. The
Temporal history explains the durable sequence; PostgreSQL and object artifacts
explain what was tested and what happened.

Graph-event delivery is best-effort. The implementation catches telemetry
delivery errors so the live graph does not become a workflow dependency. A
missing animation is not itself a failed test, just as a healthy dashboard
badge is not itself a passing one.

The wider agent fleet includes capture, change detection, knowledge ingestion,
source analysis, artifact management, and diagnostics. Experimental agent and
dbt builders produce review-required artifacts, not automatically deployed
services. They should not be conflated with the verified-test publication path.

## Run it and inspect your own evidence

The repository's local entry point is Docker Compose:

```bash
git clone https://github.com/sqe/AQE.git
cd AQE
docker compose up --build
```

Open the dashboard on port 3000, the workflow API documentation on port 8008,
and Temporal UI on port 8233. Configure an appropriate model provider before
requesting model-generated tests, and use only targets you are authorized to
exercise. The dashboard provides agent and website examples; deployment and
provider configuration are documented in the repository.

For a meaningful result, retain the workflow ID, task ID, target version,
review evidence, source artifacts, JUnit summary, repair attempts, and any
catalog URL. Source checks, the architecture diagram, and a demo recording are
useful references, but none replaces executing the scenario in your own
environment. No throughput, availability, or cost benchmark is claimed here.

**Explore the implementation:**
[Repository](https://github.com/sqe/AQE) ·
[Full execution demo](https://youtu.be/A5VcteEc_jE) ·
[Architecture and operating rules](https://github.com/sqe/AQE/blob/main/docs/architecture.md) ·
[Agent testing runbook](https://github.com/sqe/AQE/blob/main/docs/testing-agents.md) ·
[Durable workflow](https://github.com/sqe/AQE/blob/main/temporal_worker/workflow.py) ·
[Execution and repair](https://github.com/sqe/AQE/blob/main/agents/test_execution/app.py)

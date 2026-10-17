Title: A Kubernetes Operator for Self-Hosted Cube Core
Date: 2026-09-02
Modified: 2026-10-17
Category: Open Source Projects
Tags: kubernetes, operator, cube, analytics, agents, telemetry, mcp, golang, kopf, kind, microk8s
Slug: cube-microk8s-operator
Summary: Deploy self-hosted Cube Core on Kubernetes, then query Kubernetes health and agent-execution telemetry: runs, skills, tools, handoffs, artifact references, validation, and model usage.

The [Cube Core MicroK8s Operator](https://github.com/sqe/cube-microk8s-operator)
encodes self-hosted Cube Core as a declarative Kubernetes API. A `CubeCluster`
describes API replicas, refresh workers, Cube Store topology, model and Secret
references, storage, and service exposure. The controller continuously turns
that intent into standard Kubernetes resources and reports readiness back to
the custom resource.

Despite its name, the operator is not tied to MicroK8s. It uses standard
Kubernetes APIs on supported managed or self-hosted clusters; Proxmox and
MicroK8s are optional infrastructure, not prerequisites. The current minimum
Kubernetes version is 1.34. I use it in local cluster setups and on Kind.

**Release scope:** the public v0.1.0 alpha OLM catalog is installation-tested.
The new agent-execution pipeline described below is prepared for the next
source/release update; it is not in the published v0.1.0 image. The OperatorHub
submission is under community review, not an available listing. The custom
OLM catalog works independently of that review.

![Cube Core MicroK8s Operator architecture]({static}/images/cube-microk8s-operator.png)

## Why an operator instead of deployment YAML

A static manifest can start Cube, but it does not provide a durable ownership
model. The operator validates referenced configuration, applies owner
references, chooses single or clustered Cube Store resources, preserves
allocated Service fields, removes resources made obsolete by topology changes,
and calculates readiness from every expected component.

The `platform.cube.dev/v1alpha1` API reconciles:

- Cube API Deployment, Service, and PodDisruptionBudget;
- a dedicated refresh-worker Deployment;
- either one Cube Store Deployment or router/worker StatefulSets;
- private services and a NetworkPolicy around Cube Store; and
- a Ready condition with observed generation and internal endpoint.

The operator reads model ConfigMaps and configuration Secrets but does not
create credentials. This keeps database passwords and JWT signing material out
of custom-resource specs and Git history.

## One API, two controller implementations

The default controller is written in Go with controller-runtime and Kubernetes
Lease leader election. It is the recommended production path because multiple
manager replicas can coordinate safely. A separately packaged Python/Kopf
controller implements the same resource contract as a readable, Pythonic
alternative for teams that prefer rapid Python iteration.

Exactly one implementation may run at a time. Both controllers own the same
Deployments, Services, StatefulSets, and status fields; running both would
create reconciliation races. Switching therefore means deleting one controller
Deployment, waiting for termination, and only then applying the other.

The [direct deployment guide](https://github.com/sqe/cube-microk8s-operator#deploy-or-switch-controllers)
covers Go/Kopf installation. Local image tags must be replaced with registry
images outside Kind. The OLM route below uses the already-published Go image.

This dual implementation is useful beyond language preference: it documents
which behavior belongs to the API contract and which belongs to a particular
framework.

## Install on Kubernetes

You need Kubernetes 1.34+, `kubectl`, classic OLM, a reachable PostgreSQL data
source, and a default StorageClass or an existing suitable PVC. Your networking
plugin must implement NetworkPolicy to enforce the Cube Store restrictions.

### Install the public operator catalog

If classic OLM is absent, install
[Operator SDK](https://sdk.operatorframework.io/docs/installation/) and run
`operator-sdk olm install --version 0.46.0 --timeout 5m` once. This uses classic
OLM's `CatalogSource` and `Subscription`, not OLM v1. Do not run it alongside
a direct Go or Kopf installation.

```bash
git clone https://github.com/sqe/cube-microk8s-operator.git
cd cube-microk8s-operator
kubectl apply -f config/olm/install.yaml
kubectl -n cube-system wait --for=create \
  csv/cube-microk8s-operator.v0.1.0 --timeout=5m
kubectl -n cube-system wait --for=jsonpath='{.status.phase}'=Succeeded \
  csv/cube-microk8s-operator.v0.1.0 --timeout=5m
kubectl -n cube-system rollout status deployment/cube-operator --timeout=2m
```

This installs the alpha Go controller cluster-wide in `cube-system`, not a Cube
instance or a database. The manifest assumes the global catalog namespace is
`olm`; adapt the CatalogSource namespace and Subscription's `sourceNamespace`
if yours differs. Review its automatic InstallPlan approval policy before use;
do not create a second OperatorGroup in an existing operator namespace.
[OperatorHub submission #9651](https://github.com/k8s-operatorhub/community-operators/pull/9651)
is a separate community review; OpenShift console listing is also separate.

### Configure a model, credentials, and storage

This minimal model checks connectivity without depending on an application
table. Replace it with semantic models for your own data afterward.

```bash
kubectl create namespace cube --dry-run=client -o yaml | kubectl apply -f -
kubectl -n cube apply -f - <<'YAML'
apiVersion: v1
kind: ConfigMap
metadata: {name: cube-model}
data:
  Connectivity.yml: |
    cubes:
      - name: Connectivity
        sql: SELECT 1 AS id
        measures:
          - name: count
            type: count
        dimensions:
          - name: id
            sql: id
            type: number
            primary_key: true
YAML

# Bash: enter credentials interactively; never commit them.
read -rp 'PostgreSQL hostname: ' CUBE_DB_HOST
read -rp 'PostgreSQL database: ' CUBE_DB_NAME
read -rp 'PostgreSQL user: ' CUBE_DB_USER
read -rsp 'PostgreSQL password: ' CUBE_DB_PASS; echo
read -rsp 'Cube API signing secret: ' CUBE_API_SECRET; echo
kubectl -n cube create secret generic cube-configuration \
  --from-literal=CUBEJS_DB_TYPE=postgres \
  --from-literal=CUBEJS_DB_HOST="$CUBE_DB_HOST" \
  --from-literal=CUBEJS_DB_PORT=5432 \
  --from-literal=CUBEJS_DB_NAME="$CUBE_DB_NAME" \
  --from-literal=CUBEJS_DB_USER="$CUBE_DB_USER" \
  --from-literal=CUBEJS_DB_PASS="$CUBE_DB_PASS" \
  --from-literal=CUBEJS_API_SECRET="$CUBE_API_SECRET" \
  --dry-run=client -o yaml | kubectl apply -f -
unset CUBE_DB_HOST CUBE_DB_NAME CUBE_DB_USER CUBE_DB_PASS CUBE_API_SECRET

kubectl -n cube apply -f - <<'YAML'
apiVersion: v1
kind: PersistentVolumeClaim
metadata: {name: cube-remote}
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests: {storage: 10Gi}
---
apiVersion: platform.cube.dev/v1alpha1
kind: CubeCluster
metadata: {name: analytics}
spec:
  modelConfigMap: cube-model
  configurationSecret: cube-configuration
  api: {replicas: 2}
  refreshWorker: {replicas: 1}
  cubeStore:
    mode: single
    remoteStorage:
      type: persistentVolume
      persistentVolume: {existingClaim: cube-remote}
    scratch: {size: 2Gi}
  service: {type: ClusterIP}
YAML
```

Use an external secret manager and the database TLS settings appropriate for
your provider in production. The operator does not provision PostgreSQL.
The default Cube Store image is for amd64. On arm64, select the tested arm64
image before waiting for readiness:

```bash
kubectl -n cube patch cubecluster analytics --type=merge -p \
  '{"spec":{"cubeStore":{"image":"cubejs/cubestore:arm64v8@sha256:d9254a2166513e99f888da6f85362362357805116cd4d70f2b22e318e6ca5007"}}}'
```

Then, on either architecture:

```bash
kubectl -n cube wait --for=condition=Ready cubecluster/analytics --timeout=15m
kubectl -n cube get cubecluster analytics
kubectl -n cube port-forward --address 127.0.0.1 service/analytics-api 4000:4000
# In another terminal:
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:4000/readyz
```

Health is unauthenticated. Metadata and queries require a short-lived Cube JWT,
sent directly in `Authorization` without `Bearer`; see the
[REST examples](https://github.com/sqe/cube-microk8s-operator#use-the-cube-core-rest-api).
Public access needs your own TLS ingress and authorization policy. This compact
single-store example is not an HA storage design.

## Storage and query topology

Cube API translates dimensions and measures from the model ConfigMap into SQL
for the configured data source. Cube Store serves caching and pre-aggregation;
the refresh worker updates those structures independently from request-serving
API replicas.

Single mode supports an ordinary existing PVC and is appropriate for compact
installations. Clustered mode creates a router and multiple worker StatefulSets.
Its remote directory must be genuinely shared and concurrently mountable, or it
should use S3. Merely attaching the same `ReadWriteOnce` volume name to several
nodes does not create a distributed filesystem.

```yaml
apiVersion: platform.cube.dev/v1alpha1
kind: CubeCluster
metadata:
  name: analytics
  namespace: cube
spec:
  modelConfigMap: cube-model
  configurationSecret: cube-configuration
  api: {replicas: 2}
  refreshWorker: {replicas: 1}
  cubeStore:
    mode: clustered
    workers: 2
    remoteStorage:
      type: s3
      s3:
        bucket: company-cube-prod
        region: us-west-2
        secretRef: cubestore-s3
```

Default Cube/Cube Store images are digest-pinned. Workload identity is preferable for
S3; a referenced Secret is available where static credentials are unavoidable.
Containers drop Linux capabilities and disallow privilege escalation, while
Cube Store accepts only the component traffic selected by NetworkPolicy.

## A telemetry demo that tests more than installation

The Kind environment creates PostgreSQL, a read-only Node/Pod collector, Cube
models, and Cube Core. The new update adds a separate authenticated ingestion
service and the `AgentExecutions` model. The Go image runs the manager,
collector, or ingestion as independent processes; event collection is not part
of reconciliation.

```bash
# From the source checkout; requires Docker, Kind, kubectl, curl, jq and Python.
python -m pip install -r demo/requirements-mcp.txt
make kind-up       # Go controller
make kind-e2e
make kind-down

# The same demo through the Python implementation
make kind-up-kopf
make kind-e2e
make kind-down
```

The E2E checks exercise health, metadata, Kubernetes observations, and every
execution-record kind through real Cube queries. A synthetic two-agent task
has nine spans, two runs (one failed), one failed validation, 13,000 ms average
run duration, 160 input tokens, 48 output tokens, and $0.0168 reported cost.
These are test fixtures, not a claim that real agents performed those tasks.
Checks cover bad credentials, invalid records, out-of-order delivery, duplicate
retries, conflicting replays, and persistence after ingestion pod replacement.
CI exercises Go and Kopf, including repeated setup, plus PostgreSQL integration
tests and the Go race detector.

Kind detects amd64/arm64 and selects the matching Cube Store image. Access the
demo at `http://127.0.0.1:4000`; ingestion is internal with temporary loopback
forwarding during E2E. Production DNS, certificates, firewalls, backups, and
ingress remain explicit environment responsibilities.

## A real weather agent, not only a synthetic trace

I also ran the weather agent from my separate platform checkout through a
standalone stdio MCP entrypoint. It uses the same Python `WeatherHandler` as
the platform's Kafka weather service, but this demonstration invoked it on the
host: it did not submit a Kafka task, run an LLM, or automatically instrument
the entire deployed fleet. The agent fetched real data from Open-Meteo.

For the October 17, 2026 capture, Reykjavik's observation at 20:45 was:

```json
{
  "location": "Reykjavik",
  "current": {
    "temperature_2m": 9.7,
    "relative_humidity_2m": 91,
    "wind_speed_10m": 45.0
  }
}
```

The units were °C, %, and km/h. These are captured values, not a current
forecast or a performance benchmark. The completed trace
`mcp-bb768566719a424aba21b58af46a6c8b` was ingested into PostgreSQL, then read
back through Cube. Both returned the same BI metrics:

| Agent | Spans | Runs | Failed runs | Average run ms | Input/output tokens | Reported USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| weather | 3 | 1 | 0 | 2160.206 | 0 / 0 | 0 |

The three successful records describe the **run**, the **MCP tool call**, and
the **JSON result artifact reference**. No model ran, so tokens and cost are
zero—not estimated or fabricated. A new invocation gets its own trace ID and
real timestamps.

The operator repository's
[MCP execution client](https://github.com/sqe/cube-microk8s-operator/blob/main/demo/mcp_execution.py)
can invoke a trusted stdio MCP server, save its actual response and completed
spans, submit them to ingestion, and verify the returned Cube graph. An
`--execute-only` mode explicitly skips ingestion and reports
`cubeVerified: false`; the full capture above reported `cubeVerified: true`.
The private agent implementation is not copied into the public operator repo.
See the [reproduction guide](https://github.com/sqe/cube-microk8s-operator/blob/main/docs/weather-mcp-demo.md)
for environment setup, token handling, and commands.

### What is stored in SQL, and what is semantic?

The execution records are physically persisted in
`public.agent_executions`: identities, parent links, timestamps, outcomes,
duration, usage, and typed detail fields in JSONB. The weather response itself
is a local `.result.json` artifact; SQL stores its URI and media type, **not**
normalized temperature or humidity observations. A `file:` URI is local to that
host, not an uploaded report or a portable download link.

Cube's `AgentExecutions.yml` defines the semantic measures and dimensions.
When a client requests runs or latency, Cube generates SQL over the stored
events. It does not create a materialized SQL table for every measure. The
verified `/cubejs-api/v1/sql` response reported `external: false` and
`preAggregations: []`: this demo queried PostgreSQL without a pre-aggregation.
Deploying Cube Store does not, by itself, prove caching or rollup acceleration.

For an authorized database audit, this query reproduces the captured run count
and average latency:

```sql
SELECT agent_name,
       count(*) FILTER (WHERE kind = 'run') AS runs,
       avg(duration_ms) FILTER (WHERE kind = 'run') AS average_run_ms
FROM public.agent_executions
WHERE trace_id = 'mcp-bb768566719a424aba21b58af46a6c8b'
GROUP BY agent_name;
```

It returned `weather`, `1`, and `2160.206`. The corresponding Cube REST query
lets BI applications use the shared semantic definitions instead of
reimplementing that SQL in every consumer:

```json
{
  "query": {
    "dimensions": ["AgentExecutions.agent"],
    "measures": ["AgentExecutions.runs", "AgentExecutions.averageRunDurationMs"],
    "filters": [{
      "member": "AgentExecutions.traceId", "operator": "equals",
      "values": ["mcp-bb768566719a424aba21b58af46a6c8b"]
    }]
  }
}
```

Post this to `/cubejs-api/v1/load` with a short-lived Cube JWT in
`Authorization`. For daily execution BI, group by agent and day using
`AgentExecutions.endedAt`, then compare run counts, failures, latency, and
reported model usage. For audit drill-down, query event/parent IDs, tool names,
and artifact URIs. Do not sum overlapping span durations as total run latency.
The [query guide](https://github.com/sqe/cube-microk8s-operator/blob/main/docs/weather-mcp-demo.md)
includes the full aggregate query, raw-record SQL, and inspection of Cube's
generated SQL. Retention applies, so replace the captured trace ID with a fresh
one when reproducing the example.

This is **BI about agent execution**, not yet weather-domain BI. Analyzing
temperature trends would require a separate observation table and Cube model.
Nor does this configure a dashboard product or expose Cube's SQL wire protocol.
The shared-token demo is not tenant isolation: server-side access policies are
still required before external or multi-tenant use.

Public CI exercises the MCP → ingestion → PostgreSQL → Cube path for both
controllers with a clearly labelled deterministic fixture. It does not depend
on my private checkout or the availability of a live weather API. The live
weather run and matching SQL/Cube results were verified separately.

## Concrete artifacts: infrastructure versus agent output

For `CubeCluster/analytics` in single-store mode, the **operator creates**
`analytics-api` (Deployment, Service, and PDB), `analytics-refresh-worker`
(Deployment), `analytics-cubestore` (Deployment and Service), and a Cube Store
NetworkPolicy. Clustered mode substitutes router/worker StatefulSets and
Services. These are inspectable Kubernetes objects with owner references:

```bash
kubectl -n cube get deployments,statefulsets,services,pdb,networkpolicy
kubectl -n cube get cubecluster analytics -o yaml
```

The optional telemetry service creates the `agent_executions` PostgreSQL table;
the demo provides `AgentExecutions.yml` in the model ConfigMap. Cube generates
source SQL when clients query the model. The operator itself neither authors
application SQL nor creates reports, screenshots, or code patches.

**Agents create those output artifacts.** The telemetry service records their
references and context. A completed artifact record could look like this
(illustrative IDs/timestamps, not a real published report):

```json
{
  "eventId": "task-123-artifact",
  "traceId": "task-123",
  "runId": "task-123-analytics",
  "parentId": "task-123-analytics",
  "tenantId": "local",
  "cluster": "kind-cube-demo",
  "namespace": "cube-demo",
  "agent": "analytics-worker",
  "kind": "artifact",
  "name": "usage-report",
  "status": "succeeded",
  "artifactUri": "urn:example:task-123:usage-report",
  "artifactType": "application/json",
  "startedAt": "2026-10-17T10:00:00Z",
  "endedAt": "2026-10-17T10:00:01Z"
}
```

This may reference an agent-produced report, SQL file, test result, code patch,
or screenshot stored elsewhere. Ingestion neither fetches nor stores the file;
never send private content, credentials, or signed download URLs as metadata.

## What we capture for a complete agent task

Agents instrument their runtime and submit terminal records to
`POST /v1/executions`, authenticated with a separate ingestion token. Each
record has an event ID, trace/run/parent links, agent, timestamps, and an outcome.

| Record | Captured evidence |
|---|---|
| Run | Agent identity, task name, success/failure/cancellation, latency. |
| Skill | Skill name/version and its parent run. |
| Tool | Tool identity, outcome, duration, parent skill or run. |
| Handoff | Target agent; a delegated run links to the handoff. |
| Artifact | URI and media type, not the artifact contents. |
| Validation | Check name and passed/failed/skipped outcome. |
| Model call | Provider/model, input/output tokens, reported USD cost. |

For example: an analytics worker runs `operating-cube-core`, calls a Cube query
tool, records a report URI, and hands review to a second agent. The reviewer
records its own run, model call, and validation result. All share a trace ID,
with parent IDs showing how work was nested or delegated. This answers
“which agents ran, what skills/tools did they use, what did they produce, and
how did verification turn out?” without collecting private reasoning.

Usage belongs only to model-call records, preventing double-counted run totals.
Immutable IDs make identical delivery retries safe and reject changed replays.
Retention defaults to seven days. Costs are producer-reported, not calculated
billing. A Cube query can compare outcomes and usage by agent:

```json
{
  "query": {
    "measures": ["AgentExecutions.runs", "AgentExecutions.failedRuns", "AgentExecutions.inputTokens", "AgentExecutions.outputTokens", "AgentExecutions.costUsd"],
    "dimensions": ["AgentExecutions.agent"],
    "limit": 100
  }
}
```

The synthetic E2E task's expected usage rows are:

```json
[
  {"agent": "analytics-worker", "runs": 1, "failedRuns": 0, "inputTokens": 137, "outputTokens": 41, "costUsd": 0.0123},
  {"agent": "reviewer", "runs": 1, "failedRuns": 1, "inputTokens": 23, "outputTokens": 7, "costUsd": 0.0045}
]
```

These are readable projections of expected semantic results; Cube's actual
responses use qualified member names such as `AgentExecutions.runs` and commonly
encode numeric values as strings. Filter by trace ID to inspect one task, or
by `kind = skill` and group by name/version to compare skill outcomes.

Inspect `/cubejs-api/v1/meta` before querying. The
[execution contract](https://github.com/sqe/cube-microk8s-operator/blob/main/docs/agent-executions.md)
has submission examples and the complete field contract. This is not automatic
agent discovery, a live workflow engine, or chain-of-thought collection; it
requires no Kafka or Temporal. The local shared-token endpoint is not a
multi-tenant security boundary: external use requires trusted identity,
server-side tenant enforcement, TLS, network restrictions, and rate limits.

## Agents consume governed analytics, not database credentials

A local read-only agent skill uses a short-lived Cube JWT supplied by a trusted
caller and calls the Cube Core REST contract. It first inspects `/cubejs-api/v1/meta`, then submits bounded semantic
queries to `/cubejs-api/v1/load`. This lets an agent use named measures and
dimensions without receiving PostgreSQL credentials or permission to execute
arbitrary SQL through the skill. Authentication, allowed models, and tenant
filters still require explicit server-side policy; the operator does not
configure OIDC or guarantee tenant isolation by itself.

Cube's hosted Chat API and official Cloud skills are a separate product
boundary. This project documents them as optional Cube Cloud integrations; it
does not claim those hosted features are part of open-source Cube Core.

## Operational and licensing boundaries

Before production use, test CRD upgrades, restore procedures, controller
failover, Cube Store recovery, database limits, and model changes under the
target workload. “Production-oriented” means these controls are represented;
it does not replace environment-specific qualification. The next catalog is
for fresh installations, not an advertised automatic upgrade from v0.1.0.

This is an independent community project, not an official Cube product or a
claim of Cube endorsement. It deploys upstream [Cube](https://github.com/cube-js/cube)
and Cube Store images; credit belongs to the Cube authors and contributors.
Original operator code is Apache-2.0. Cube Client is MIT licensed; Cube Backend
is Apache-2.0 licensed. Upstream licenses/notices remain separate and must be
preserved when redistributing those components.

**Explore the project:**
[GitHub repository](https://github.com/sqe/cube-microk8s-operator) ·
[Architecture](https://github.com/sqe/cube-microk8s-operator/blob/main/docs/architecture.md) ·
[Execution telemetry](https://github.com/sqe/cube-microk8s-operator/blob/main/docs/agent-executions.md) ·
[Agent boundary](https://github.com/sqe/cube-microk8s-operator/blob/main/docs/agent-integration.md)

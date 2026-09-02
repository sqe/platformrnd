Title: Building an Agentic Kubernetes Platform That Runs Anywhere
Date: 2026-09-02
Category: Open Source Projects
Tags: kubernetes, agents, kafka, cilium, gpu, knowledge-graph, aws, proxmox
Slug: agentic-kubernetes-platform
Summary: A deep dive into an event-driven, portable agent platform that combines Kafka coordination, Cilium networking, GPU model serving, governed analytics, knowledge graphs, and reproducible AWS, Proxmox, and Kind deployment paths.

The [Agentic Kubernetes Platform](https://github.com/sqe/agentic-kubernetes-platform)
is an Apache-2.0 reference architecture for running specialist agents, model
inference, and training without tying the application contract to one cloud. It
uses the same agent protocol on AWS EKS and Proxmox-hosted Kubernetes; only the
capacity, identity, load-balancing, and object-storage adapters change.

![Agentic Kubernetes Platform architecture]({static}/images/agentic-kubernetes-platform.png)

## The core design decision: events between agents

Direct HTTP calls produce a deceptively simple demo but tightly couple agent
availability, retry behavior, and scaling. Here, the supervisor discovers an
exact skill from an Agent Card, publishes a JSON-RPC 2.0 request to the agent's
Kafka topic, and correlates the response from `results.*` using the request ID.

```text
client → Cilium Gateway → supervisor → tasks.weather
                                      → weather worker
client ← supervisor ← results.weather ←┘
```

Workers publish their result before committing the input offset. That gives the
system an explicit at-least-once contract. It does not make an external weather
API, Neo4j, and Kafka one transaction, so each handler must use the request or
document ID as an idempotency key. This is a more useful production contract
than pretending distributed side effects are exactly once.

Every specialist owns a directory, versioned Agent Card, task/result topics,
domain implementation, container, and focused tests. The shared runtime owns
JSON-RPC validation, manual Kafka commits, Redis caching, Prometheus metrics,
and optional MLflow traces. Domain behavior remains outside the framework.

## Three specialists demonstrate different workloads

The weather agent is intentionally lightweight. It resolves imperfect location
phrasing through Open-Meteo, serves current conditions and forecasts, and caches
repeated reads. It demonstrates the minimum useful agent contract without
requiring an LLM.

The knowledge-graph agent demonstrates expensive asynchronous work. Its API
stores an uploaded PDF, text, or JSON document in S3 or RustFS and sends only a
durable URI and metadata through Kafka. A KEDA-scaled worker extracts bounded
chunks through an OpenAI-compatible model, validates entities and relationships
against a versioned ontology, writes graph truth to Neo4j, and indexes semantic
candidates in Qdrant. The included explorer renders the result in 2D or 3D and
traces shortest paths with evidence back to the source object.

The analytics agent delegates governed questions such as `analytics.usage` to
Cube Core. It never accepts arbitrary SQL. Instead it constructs a bounded
semantic query, adds the authenticated conversation owner as a tenant filter,
signs a short-lived Cube JWT, and returns both rows and the exact query for
reproduction. The sibling Cube operator owns Cube API, refresh worker, and Cube
Store lifecycle.

## Conversations, identity, and model routing

The minimal dashboard is deliberately not another runtime. It calls the same
supervisor API, persists user and pending assistant messages in PostgreSQL, and
polls until a correlated Kafka result completes the response. Read-only sharing
uses a rotatable 256-bit token; PostgreSQL stores only its SHA-256 digest.

Cognito is the managed AWS identity provider, while the bare-metal profile uses
the Keycloak Operator. APIs derive tenant identity from verified OIDC claims,
not request parameters. Redis remains disposable cache, PostgreSQL owns
relational workflow state, Neo4j owns explicit relationships, Qdrant owns
rebuildable vectors, and S3/RustFS owns durable source artifacts.

The supervisor's LLM gateway is a visible, replaceable component. A local Apple
Silicon environment can route prompts through an MLX-hosted Qwen 27B 4-bit
model; GPU clusters use an OpenAI-compatible endpoint such as vLLM. Named skills
still work when the router model is absent. Bring Your Own Agent requires only a
valid Agent Card and Kafka contract; Bring Your Own Model requires an internal
OpenAI-compatible endpoint and explicit registration.

## Portable infrastructure without pretending it is identical

The two targets share Cilium CNI, NetworkPolicy, Envoy, Gateway API, Kafka,
KEDA, Helm packaging, and agent contracts. Their infrastructure adapters differ:

| Concern | AWS | Bare metal |
|---|---|---|
| Kubernetes | EKS | K3s on Proxmox VMs |
| Identity | Cognito | Keycloak Operator |
| Public address | AWS load balancer | MetalLB |
| Durable objects | S3 | RustFS S3-compatible API |
| GPU capacity | Autoscaled NVIDIA nodes | Passed-through local NVIDIA cards |

Object storage is the durable source for models and datasets. An init container
hydrates a PVC or local NVMe cache concurrently and atomically, so restarts can
reuse warm files rather than repeatedly downloading from an external model
registry. This improves startup only when the cache is retained and networking
is appropriately provisioned; the project does not claim storage eliminates
model-loading time.

## Reproduce it locally

Docker Compose is the shortest application-level path:

```bash
git clone https://github.com/sqe/agentic-kubernetes-platform.git
cd agentic-kubernetes-platform
make install && make test
docker compose up --build
open http://localhost:8002/dashboard
```

Kind exercises the Kubernetes topology, including Cilium Gateway API,
Redpanda's Kafka-compatible API, KEDA, RustFS, PostgreSQL, Qdrant, Neo4j, Redis,
and operator-managed Keycloak:

```bash
make kind-up
make kind-status
curl --fail http://127.0.0.1:8080/knowledge/health
open http://127.0.0.1:8080/dashboard
make kind-down
```

The repository separates source checks from deployment evidence. Unit tests,
Helm rendering, Terraform validation, and Compose validation prove only their
stated scope. Runtime evidence should include request IDs, Kafka correlation,
Kubernetes status, redacted Hubble flows, and timestamps—not unsupported claims
about production availability, throughput, or savings.

**Explore the project:**
[GitHub repository](https://github.com/sqe/agentic-kubernetes-platform) ·
[Architecture](https://github.com/sqe/agentic-kubernetes-platform/blob/main/docs/ARCHITECTURE.md) ·
[Adding an agent](https://github.com/sqe/agentic-kubernetes-platform/blob/main/docs/ADDING_AGENTS.md)

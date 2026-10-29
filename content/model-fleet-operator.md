Title: Model Fleet: Declarative GPU Inference, Training, and Agent Operations
Date: 2026-09-02
Modified: 2026-10-18
Category: Open Source Projects
Tags: kubernetes, operator, gpu, inference, training, keda, cilium, slack, kafka
Slug: model-fleet-operator
Summary: A deep technical look at a Kubernetes operator that converts model intent into standard inference, training, networking, scaling, dataset, GPU-placement, observability, and agent-control resources.

The [Model Fleet Operator](https://github.com/sqe/model-fleet-operator) provides
one declarative API for containerized inference, training, immutable datasets,
and managed agents. The central principle is deliberately conservative: custom
resources express intent, while the resulting workloads remain ordinary
Kubernetes Deployments, Services, Jobs, KEDA scalers, and Cilium routes.

![Model Fleet Operator architecture]({static}/images/model-fleet-operator.png)

**Release status:** v0.1.0 is an alpha release candidate. The controller-only
OLM catalog has passed a fresh local installation test; the expanded GitHub
Actions matrix and public-image release verification remain separate gates.
An OperatorHub listing is not available yet. The repository's
[dated status record](https://github.com/sqe/model-fleet-operator/blob/main/status.md)
tracks the actual release and upstream-review outcome.

## Four APIs divide ownership cleanly

`InferenceService` describes a model-serving container, resource requests,
accelerator fit, scaling policy, Service, and optional Gateway API route.
`TrainingRun` creates one immutable Job attempt with datasets, storage,
deadlines, retries, parallelism, suspension, and cancellation. `Dataset`
registers immutable version metadata, named splits, an access allowlist, and an
optional read-only PVC. `AgentRegistration` links a versioned Agent Card to its
runtime and operational state.

This avoids model-specific shell scripts while preserving Kubernetes debugging:

```bash
kubectl apply -f examples/inference-vllm.yaml
kubectl get isvc,deploy,service,scaledobject,httproute -n models

kubectl apply -f examples/training-pytorch.yaml
kubectl get trun,job -n models
```

The controller never downloads model data into its own pod and never reads a
Hugging Face token. An init container can prefetch into a shared volume using a
Secret reference; the inference container sees only the resulting model files.
Training outputs and checkpoints belong in durable object storage, not the Job's
ephemeral filesystem.

## GPU fit is a scheduling input, not a performance promise

Requesting one GPU says nothing about whether a model fits. Model Fleet accepts
module-level budgets split into sharded and replicated memory. Sharded weights
are divided across the requested GPU count; runtime libraries and other
replicated allocations are added per device, then a safety margin is applied:

```text
required per GPU = ceil((Σ sharded / GPU count + Σ replicated) × (1 + margin))
```

For 90 GiB of sharded allocations, 4 GiB replicated per device, two GPUs, and a
10% margin, each GPU needs `ceil((90 / 2 + 4) × 1.10) = 54 GiB`. The operator
maps that requirement to a portable GPU-memory capacity label and can also add
required affinity for specific NVIDIA products.

This is admission and placement guidance—not dynamic VRAM bin packing and not a
throughput guarantee. Kubernetes still allocates whole GPU devices. Drivers,
device plugins, MIG configuration, and node labels remain infrastructure
responsibilities, owned by cloud images or the NVIDIA GPU Operator.

AMD placement uses `spec.accelerator.vendor: amd` and `amd.com/gpu`; NVIDIA
remains the default. Both inference and training validate vendor/count conflicts
in resource requests and limits. AMD workloads require compatible drivers, an
AMD device plugin and a tested ROCm container. Local tests verify generated
resources and Kubernetes admission, not live AMD inference or GPU throughput.

## Pod scaling and node capacity are different control loops

KEDA decides how many model pods are needed. A cloud or bare-metal capacity
provider decides whether nodes exist to run pending pods. Keeping those loops
separate makes the workload API portable:

- EKS can use Karpenter NodePools;
- GKE can use managed node-pool autoscaling; and
- bare metal uses existing NVIDIA nodes or an external machine provider.

True scale-to-zero requires a signal that exists while the model pod is absent,
such as Kafka lag, gateway backlog, SQS, or Pub/Sub. A Prometheus metric emitted
only by the sleeping model cannot wake itself. This detail is why the operator
passes through external KEDA triggers rather than inventing a misleading
“automatic” scaler.

## Cilium networking and secure workload boundaries

An `InferenceService` creates an `HTTPRoute`; the platform administrator owns
the shared Cilium Gateway, listener policy, certificates, and public DNS. This
keeps model authors from silently creating load balancers. Dedicated service
accounts and Secret references keep provider, registry, and repository
credentials outside the operator and custom-resource status.

The same chart runs on Kind, MicroK8s, EKS, and GKE when Cilium owns Gateway API.
Kind intentionally uses an echo workload because Docker nodes do not expose a
GPU by default; it verifies controller reconciliation and L7 routing without
pretending to benchmark inference.

```bash
git clone https://github.com/sqe/model-fleet-operator.git
cd model-fleet-operator
make kind-up
kubectl --context kind-model-fleet apply -f examples/inference-kind.yaml
curl -H 'Host: model.localhost' http://127.0.0.1:8080/
make kind-down
```

## Install the controller without a complete platform

You do not need Kafka, Slack, GPUs, KEDA or Cilium to try the CPU-only controller
examples. Those integrations become prerequisites only when their features are
enabled. Choose **one** controller installation method per cluster.

For an existing Kubernetes cluster, clone the repository and install the Helm
chart with its shared Gateway disabled:

```bash
git clone https://github.com/sqe/model-fleet-operator.git
cd model-fleet-operator
helm upgrade --install model-fleet charts/model-fleet-operator \
  --namespace model-fleet-system --create-namespace \
  --set gateway.enabled=false --wait
kubectl create namespace models
kubectl -n models apply -f config/olm/examples.yaml
kubectl -n models rollout status deployment/model-echo
kubectl -n models wait --for=condition=complete job/cpu-smoke-test --timeout=5m
kubectl -n models get inferenceservices,trainingruns,datasets,agentregistrations
```

The chart needs its configured controller image to be publicly available or
accessible through your image-pull credentials. See the
[installation documentation](https://github.com/sqe/model-fleet-operator/blob/main/docs/installation.rst)
for Kubernetes prerequisites and optional integrations.

The OLM alternative targets Kubernetes 1.34+ with **classic OLM** installed in
namespace `olm`. Once the verified v0.1.0 release is available, its `install.yaml`
asset installs the versioned project catalog, OperatorGroup and Subscription:

```bash
kubectl apply -f https://github.com/sqe/model-fleet-operator/releases/download/v0.1.0/install.yaml
kubectl -n model-fleet-system wait --for=create csv/model-fleet-operator.v0.1.0 --timeout=5m
kubectl -n model-fleet-system wait --for=jsonpath='{.status.phase}'=Succeeded \
  csv/model-fleet-operator.v0.1.0 --timeout=5m
```

This project catalog is **not** an OperatorHub listing. The OLM package installs
the controller and four CRDs, not Slack/Kafka, the agent supervisor, model
gateway, or `AgentTask`. Use Helm for those optional companions; never install
a second controller alongside the OLM installation.

## What the controller actually creates

The CPU example is deliberately small enough to inspect:

```yaml
apiVersion: fleet.sqe.io/v1alpha1
kind: InferenceService
metadata:
  name: model-echo
  namespace: models
spec:
  model: {name: local-smoke-test}
  container: {image: ealen/echo-server:0.9.2, port: 80}
  replicas: 1
  service: {port: 80}
  gateway: {enabled: false}
```

It produces a `model-echo` Deployment and Service. A `TrainingRun` named
`cpu-smoke-test` produces a Job with that name. The Dataset and AgentRegistration
examples register metadata: the placeholder S3 URI is not downloaded, and an
agent endpoint does not cause an agent to be deployed.

| Input | Reconciled artifact or status |
|---|---|
| InferenceService | Deployment, Service, observed readiness; optional KEDA scaler and HTTPRoute |
| TrainingRun | Job, completion/failure status, dataset-version and access checks |
| Dataset | Immutable version metadata, classification, owner and ServiceAccount allowlist |
| AgentRegistration | Registered Agent Card; optional replica management of an explicitly annotated existing Deployment |

```bash
kubectl -n models get deployment model-echo -o yaml
kubectl -n models get service model-echo -o yaml
kubectl -n models logs job/cpu-smoke-test
kubectl -n models port-forward service/model-echo 18080:80
# In another terminal:
curl http://127.0.0.1:18080/olm-smoke
```

In the local OLM verification, the training resource reached `Succeeded`, both
metadata resources reached `Registered`, and inference returned to `Ready`
after suspension and resumption. The HTTP echo response contained
`http.originalUrl: /olm-smoke` and `environment.MODEL_NAME: local-smoke-test`.
These are controller-and-network checks, not a claim that an LLM ran on a GPU.

## The agent and operations control plane

The optional registry persists Agent Cards as `AgentRegistration` resources.
The supervisor resolves an exact skill or asks an allowlisted LLM gateway to
choose among registered skills, then publishes JSON-RPC through Kafka. Workers
publish a correlated result before committing the task. A built-in operations
agent can inspect fleet state and request explicit inference or training
actions using the same contract.

Slack uses Socket Mode, so the bot needs no public callback ingress. Read-only
inventory is the safe default. Mutating operations require user/channel
allowlists, and quota requests are disabled until a reviewed provider policy is
attached. Sensitive commands require explicit confirmation rather than treating
natural language as authorization.

Operational visibility combines Prometheus, Grafana, Hubble, DCGM GPU metrics,
OpenCost, cloud billing exports, and MLflow. Billing and OpenCost can overlap,
so the reporting path presents them separately instead of adding them into a
misleading total. Grafana snapshots can stream to Slack without writing PNGs to
the bot filesystem.

## Concrete Qwen patterns

Apple Silicon development follows a separate execution boundary: MLX runs
natively on macOS, because Linux kind nodes cannot access Metal. An allowlisted
gateway route can target `host.docker.internal` while Kubernetes inference
routes target ordinary Services. The operator does not manage the native MLX
process. The
[accelerator guide](https://github.com/sqe/model-fleet-operator/blob/main/docs/ACCELERATOR_INFERENCE.md)
includes the guarded launcher and Helm values.

Existing secured OpenAI-compatible endpoints on Windows or phones can also be
explicit gateway routes. This is model-neutral: Gemma, Qwen, Phi, SmolLM and
small Llama variants are candidate families, subject to device memory, runtime,
quantization and model licensing—not a claim that every model works on every
phone. The
[phone SLM values example](https://github.com/sqe/model-fleet-operator/blob/main/examples/phone-slm-values.yaml)
routes to an existing endpoint; it does not install an app or manage the device.
A browser inference worker does not automatically become an HTTP model server.

The separate Open Compute companion explores opt-in browser/desktop workers,
durable task leases and an adapter for existing Slurm clusters. It is not
bundled with Model Fleet, does not turn phones into native Slurm nodes, and
does not automatically bridge its jobs into Kubernetes custom resources.

Gateway request/error counters and latency histograms carry a `runtime` label,
so Grafana can distinguish MLX development traffic from Kubernetes model
services. Token and estimated-cost counters use the upstream usage payload and
configured prices, not a measurement of electrical consumption or a cloud bill.
For example, Prometheus can query request rate by runtime:

```promql
sum by (runtime, result) (
  rate(model_fleet_upstream_requests_total[5m])
)
```

The examples include a quantized Qwen 27B inference/gateway profile and a
Qwen3-VL image LoRA training shape. Quantization reduces weight memory but does
not make KV cache, activations, runtime allocations, context length, or training
memory disappear. A 24 GiB target is a testable fit hypothesis; production
capacity must be measured on the exact GPU, driver, serving build, sequence
length, and concurrency. The operator captures those requirements without
hard-coding one model family.

## CI and release verification are part of the contract

Pull requests and main-branch changes run independent checks for:

- Python 3.11, 3.13 and 3.14 tests with coverage and JUnit artifacts;
- Ruff, ShellCheck and actionlint; Sphinx documentation and Python package builds;
- Helm profiles for kind, MicroK8s, AWS and GCP, plus optional companion routes;
- Go SDK race tests and vet, protobuf lint/generation and Terraform validation;
- native amd64/arm64 image builds and packaged-service import smoke tests; and
- a real CatalogSource/Subscription installation on kind/Kubernetes 1.34,
  checking all four bundled CRDs across namespaces, training completion,
  inference suspend/resume and an HTTP response through the generated Service.

The release workflow reuses CI, builds multi-architecture controller, bundle
and catalog images, then verifies anonymous pulls and installation through the
published catalog before creating a GitHub alpha release. Release assets include
Python distributions, the Helm archive, the OLM bundle archive, a digest-pinned
installation manifest, image references and SHA-256 checksums. OLM diagnostics
are retained when verification fails.

This does not certify GPU throughput, live Slack/Kafka delivery, cloud machine
provisioning or every optional integration. OperatorHub acceptance is a separate
upstream review, not an automatic consequence of a green release workflow.

The result is a control plane with clear boundaries: model authors declare
workloads and immutable inputs, Kubernetes reconciles pods and Jobs, KEDA owns
replica demand, infrastructure owns nodes, Cilium owns ingress, and observability
systems provide evidence. Each component can be replaced without rewriting the
custom-resource contract.

**Explore the project:**
[GitHub repository](https://github.com/sqe/model-fleet-operator) ·
[GPU capacity](https://github.com/sqe/model-fleet-operator/blob/main/docs/GPU_CAPACITY.md) ·
[Agent control plane](https://github.com/sqe/model-fleet-operator/blob/main/docs/AGENT_CONTROL_PLANE.md)

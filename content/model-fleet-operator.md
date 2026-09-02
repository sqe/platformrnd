Title: Model Fleet: Declarative GPU Inference, Training, and Agent Operations
Date: 2026-09-02
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

The examples include a quantized Qwen 27B inference/gateway profile and a
Qwen3-VL image LoRA training shape. Quantization reduces weight memory but does
not make KV cache, activations, runtime allocations, context length, or training
memory disappear. A 24 GiB target is a testable fit hypothesis; production
capacity must be measured on the exact GPU, driver, serving build, sequence
length, and concurrency. The operator captures those requirements without
hard-coding one model family.

The result is a control plane with clear boundaries: model authors declare
workloads and immutable inputs, Kubernetes reconciles pods and Jobs, KEDA owns
replica demand, infrastructure owns nodes, Cilium owns ingress, and observability
systems provide evidence. Each component can be replaced without rewriting the
custom-resource contract.

**Explore the project:**
[GitHub repository](https://github.com/sqe/model-fleet-operator) ·
[GPU capacity](https://github.com/sqe/model-fleet-operator/blob/main/docs/GPU_CAPACITY.md) ·
[Agent control plane](https://github.com/sqe/model-fleet-operator/blob/main/docs/AGENT_CONTROL_PLANE.md)

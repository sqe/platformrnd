Title: A Kubernetes Operator for Self-Hosted Cube Core
Date: 2026-09-02
Category: Open Source Projects
Tags: kubernetes, operator, cube, analytics, golang, kopf, kind, microk8s
Slug: cube-microk8s-operator
Summary: How a declarative CubeCluster API, interchangeable Go and Python controllers, storage-aware Cube Store topology, and a Kind telemetry demo turn self-hosted Cube Core into an operable Kubernetes workload.

The [Cube Core MicroK8s Operator](https://github.com/sqe/cube-microk8s-operator)
encodes self-hosted Cube Core as a declarative Kubernetes API. A `CubeCluster`
describes API replicas, refresh workers, Cube Store topology, model and Secret
references, storage, and service exposure. The controller continuously turns
that intent into standard Kubernetes resources and reports readiness back to
the custom resource.

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

```bash
# Go/controller-runtime, the default
kubectl apply -k config/default
kubectl -n cube-system rollout status deployment/cube-operator

# Alternative Kopf controller: stop Go first
kubectl -n cube-system delete deployment cube-operator --wait=true
kubectl apply -k config/kopf
kubectl -n cube-system rollout status deployment/cube-operator-kopf
```

This dual implementation is useful beyond language preference: it documents
which behavior belongs to the API contract and which belongs to a particular
framework.

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

Images in the examples are digest-pinned. Workload identity is preferable for
S3; a referenced Secret is available where static credentials are unavoidable.
Containers drop Linux capabilities and disallow privilege escalation, while
Cube Store accepts only the component traffic selected by NetworkPolicy.

## A telemetry demo that tests more than installation

The included Kind environment creates PostgreSQL, a collector with scoped
Kubernetes read access, a semantic telemetry model, and Cube Core. The collector
writes point-in-time pod observations. The E2E script verifies liveness,
readiness, metadata compilation, and a real semantic query rather than stopping
at “the pod is Running.”

```bash
git clone https://github.com/sqe/cube-microk8s-operator.git
cd cube-microk8s-operator

make verify
make kind-up       # Go controller
make kind-e2e
make kind-down

# The same demo through the Python implementation
make kind-up-kopf
make kind-e2e
make kind-down
```

The Kind scripts detect amd64 versus Apple Silicon arm64 nodes and select the
matching digest-pinned Cube Store image. The demo API is mapped only to the
local machine. Production DNS, certificates, firewall rules, backups, and
public ingress remain explicit operator responsibilities.

## Agents consume governed analytics, not database credentials

A local agent skill mints a short-lived Cube JWT and calls the Cube Core REST
contract. It first inspects `/cubejs-api/v1/meta`, then submits bounded semantic
queries to `/cubejs-api/v1/load`. This lets an agent use named measures and
dimensions without receiving PostgreSQL credentials or permission to execute
arbitrary SQL.

Cube's hosted Chat API and official Cloud skills are a separate product
boundary. This project documents them as optional Cube Cloud integrations; it
does not claim those hosted features are part of open-source Cube Core.

## Publication and operational boundaries

The repository includes an OperatorHub/OLM path: bundle and catalog metadata,
CSV install modes, validation, scorecard, Kind+OLM testing, image signing, and
the community-operators pull-request workflow. Documentation states whether a
release has actually been published rather than treating packaging instructions
as publication evidence.

Before production use, test CRD upgrades, restore procedures, controller
failover, Cube Store recovery, database limits, and model changes under the
target workload. “Production-oriented” means these controls are represented;
it does not replace environment-specific qualification.

**Explore the project:**
[GitHub repository](https://github.com/sqe/cube-microk8s-operator) ·
[Architecture](https://github.com/sqe/cube-microk8s-operator/blob/main/docs/architecture.md) ·
[Agent boundary](https://github.com/sqe/cube-microk8s-operator/blob/main/docs/agent-integration.md)

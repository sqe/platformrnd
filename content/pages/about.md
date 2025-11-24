Title: About
Date: November 2025
Slug: about

## Aziz Kurbanov

**Principal Platform Architect & Open Source Author**

- Specialized expertise in production-grade platform engineering, MLOps systems, AI infrastructure, distributed robotics, and enterprise cloud-native solutions. 
- Proven track record architecting and delivering mission-critical infrastructure at scale, leading high-performing teams, and building self-service platform ecosystems that accelerate engineering velocity.

---

## Professional Highlights

### Agentic AI & MLOps Systems

- Architected, created, and productionized Agentic AI systems integrated with Kubernetes and ArgoCD. 
  - Encompassed designing Multi-Agent Architectures, deploying GPU-accelerated LLMs, and managing Qdrant/Redis memory. 
- Implemented Apache Kafka for agent communication and orchestrated complex workflows with Argo Workflows, optimizing performance. 
  - Ensured robust security with RBAC, established Prometheus monitoring, and led automated Canary and Blue-Green deployments with agent state migration.

- Additionally, architected and delivered an MLOps-driven agentic quality engineering platform orchestrating distributed AI agents for web state capture, LLM-powered change detection, and RAG-enabled test generation.
- Engineered robust infrastructure integrating PostgreSQL, MinIO, Qdrant, Redis, and Kafka for scalable MLOps workflows, persistent artifact storage, semantic search, and real-time agent orchestration.

### Distributed Robotics & Edge Computing

- Engineered production-grade infrastructure for containerized robotics applications on Kubernetes, featuring KubeEdge, ROS2, and multi-domain DDS networking. 
- Designed eBPF-based datapaths with Cilium CNI enabling seamless ROS2 FastDDS interoperability for UDP multicast discovery. 
- Built CLI tooling for dynamic edge node management, automated ROS2 deployment, and real-time resource monitoring.

### Cloud Infrastructure & Platform Engineering

- Architected and led migration of thousands of Kubernetes clusters (EKS to AKS) using Terraform, GitOps, and Velero
- Managed high-volume workloads exceeding 10 petabytes in traffic; optimized infrastructure using AWS Graviton instances for energy efficiency and cost savings while maintaining performance SLAs
- Automated provisioning and decommissioning of thousands of self-hosted MySQL servers to Azure Database for MySQL via IaC
- Designed comprehensive Datadog and Grafana monitoring solutions with custom dashboards, SLO tracking, and real-time alerting
- Built DNS record management CLI utilities for Cloudflare and AWS Route53, including Dynamic DNS, automating customer onboarding/offboarding
- Expertise in VPC/subnet architecture, load balancing strategies, VPN configurations, and network segmentation across cloud providers
- Implemented Just-In-Time Access to Azure MySQL infrastructure using Britive, reducing access overhead by 40%+

### Kubernetes & Container Orchestration

- Expert in designing, scaling, and operating production Kubernetes clusters across AWS (EKS), Azure (AKS), and GCP (GKE). Deep expertise in ArgoCD, Flux CD, Helm, Kustomize, Argo Workflows, multi-tenancy patterns, namespace isolation, and cost optimization. 
- Proficient in Kubernetes operators (kopf-based), custom resource definitions, and RBAC security models.

### Bare Metal & Edge Infrastructure

- Architect of bare-metal Kubernetes clusters using microk8s and kind with automated provisioning and lifecycle management. 
- Implemented MetalLB and advanced load balancing solutions for bare-metal environments, enabling production-grade service exposure. 
- Deep expertise in OSI model, BGP routing, L2/L3 networking, and network protocols enabling seamless inter-cluster communication. 
- Expert in KubeEdge for edge computing at the network periphery, supporting distributed and hybrid cloud/edge deployments with real-time data processing capabilities.

### Infrastructure as Code & GitOps

- Champion of Everything-as-Code culture—Terraform, Ansible, GitHub Actions, CI/CD pipelines following 12 Factor Manifesto principles. 
- Designed and implemented GitOps workflows enabling reproducible, auditable cluster provisioning and lifecycle operations. 
- AWS Organizations automation and multi-account infrastructure governance with automated compliance frameworks
  - Reduced MTTR (Median Time To Release) by 98.96% through GitOps automation.

### Observability & Monitoring

- Built comprehensive observability platforms across Datadog, Prometheus, Grafana, and ELK Stack. 
- Expertise in distributed tracing, SLO/SLA dashboards, synthetic transaction monitoring, real user monitoring (RUM), and proactive alerting. 
- Established monitoring standards and runbooks elevating operational maturity.

### AI/GPU Infrastructure

- GPU acceleration, CUDA, MIG (Multi-Instance GPU) configurations with production experience managing 500+ GPU nodes (8x H100s per node) in large-scale inference clusters
- LLM deployments (HuggingFace, TensorFlow, PyTorch, LM Studio) supporting Text, Audio, and Visual modalities with optimized KV cache management for throughput maximization
- RAG systems with vector databases (Qdrant, pgvector) and KV optimization for inference performance and memory efficiency
- Agentic system orchestration and A2A (Agent-to-Agent) workflows with persistence layers and state management across distributed GPU infrastructure
- SageMaker, Conversational AI, Pre-trained model containerization, and advanced inference optimization techniques (quantization, batching, dynamic scheduling)
- ML/AI compute workload optimization (Vercel → AWS ECS Fargate) and distributed inference scaling across multi-node GPU clusters

### Security & Compliance

- DevSecOps practices with automated OWASP ZAP dynamic testing and WAF (Web Application Firewall) deployment
- VPN/Wireguard tunnel configuration and encrypted network segmentation across hybrid infrastructures
- Lacework cloud security platform automation
- Keycloak SSO integration with MFA (AWS IAM, Azure AD, Okta via OIDC/SAML)
- Just-In-Time Access implementation and security policy enforcement
- ISO 27001 certification leadership and recertification
- SOC 2 Type II readiness and compliance architecture
- NIST SP 800-53 control implementation and continuous monitoring
- AWS Partner badge (AWS Foundational Technical Review)

### Test Automation & Quality Engineering

As first QA hire at multiple organizations, established QA processes, test infrastructure, and automation frameworks. Led test automation across E-commerce, mobile, firmware, IoT, and ERP integrations. Created comprehensive CI/CD testing pipelines with Kubernetes test pods, Datadog instrumentation, and PagerDuty incident triggers.

---

## Technology Stack

### Cloud Platforms
AWS (EKS, EC2, Lambda, ECS Fargate, Aurora, RDS, S3, Route53, ECR, Organizations automation, Auto Scaling, CloudWatch), Azure (AKS, Database Services, Network Watcher, Log Analytics, Autoscaling), GCP (GKE, Cloud Run, Cloud Build, Autoscaling)

### Kubernetes & Orchestration
Kubernetes, Helm, Kustomize, ArgoCD, Argo Workflows, Flux CD, KubeEdge, kopf-based operators, Istio, Cilium CNI

### Infrastructure as Code
Terraform, Ansible, GitHub Actions, GitOps, Everything-as-Code

### Databases & Data
PostgreSQL (pgvector), MySQL, Redis, Kafka, RabbitMQ, MinIO (object store), Qdrant, Pinecone, Redshift, BigQuery, Parquet, persistence layer optimization, KV stores

### AI/MLOps & LLMs
GPU acceleration, CUDA, LLMs, SLMs, RAG, AI Agents, SageMaker, HuggingFace, TensorFlow, PyTorch, Slurm, vLLM, Kubeflow, Metaflow, Custom Artifact versioning tooling

### Observability
Datadog, Prometheus, Grafana, ELK Stack, Netdata, CloudWatch, distributed tracing, SLO/SLA monitoring, log aggregation, alerting

### Security & Compliance
Lacework, OWASP ZAP, Keycloak, OIDC/SAML, Britive, IAM/RBAC, DevSecOps, ISO 27001, SOC 2 Type II, NIST SP 800-53, WAF, Wireguard, CloudTrail, GuardDuty

### Languages & Tools
Linux, Python, Django, Flask, Bash, Git, Docker, DockerHub, ECR, Terraform, Ansible, Selenium, Appium, JMETER, ROS2, FastDDS, Wireshark, TCP/IP, HTTP/MQTT

---

## Open Source Projects

### robotics-k8s-infra
Production-grade Kubernetes platform for cloud/edge robotics. Features KubeEdge, ROS2, ArgoCD, multi-domain DDS networking, eBPF-based Cilium CNI for UDP multicast discovery, CLI tools for edge node lifecycle management, and GitOps-first provisioning.

### AQE (Agentic Quality Engineering Platform)
MLOps-driven agentic platform orchestrating distributed AI agents for web state capture, LLM-powered change detection, and RAG-enabled Playwright test generation. Achieves reproducible end-to-end test automation for complex web applications.

### ESDDNS
Kubernetes kopf-based operator for automated IPv4 DNS A record drift detection and state management using finite state machine modeling. Includes Grafana Cloud monitoring, CI/CD pipelines with GitHub Actions, and bare-metal microk8s cluster automation.

### urlstatus
Fully agentic, A2A-compliant web crawler agent with Python, Flask, and modular async crawling logic. Exposes CLI and HTTP+JSON/JSON-RPC interfaces. Features Analyzer Agent (LLM-driven failure analysis) and GitHub Code Analysis Agent with seamless GitHub API integration.

### fizmatmod
Physics-based framework applying classical mechanics principles (Hamiltonian and Lagrangian formulations) to software project modeling. Enables predictive analysis of project trajectories, quantifies team momentum and project friction as measurable, optimizable values.

---

## Platform & SRE Leadership

As a platform architect and SRE systems leader, I've consistently championed infrastructure excellence and engineering velocity. My leadership philosophy centers on building self-service platform ecosystems that empower teams—eliminating toil, automating lifecycle operations, and establishing infrastructure as the foundation for organizational scaling. I maintain active technical roadmaps, anticipate future infrastructure trends, and architect platforms that scale ahead of organizational growth while leveraging best-in-class tooling and emerging technologies.

Key infrastructure initiatives include:

- Architected self-service platform strategies enabling product teams to move independently with centralized infrastructure guardrails
- Built and maintained high-reliability infrastructure across multi-cloud environments (AWS, Azure, GCP) with focus on resilience and fault tolerance
- Established comprehensive observability, security, and compliance standards across organizations including SLO definition, alerting hierarchies, and runbook automation
- Drove GitOps and Infrastructure-as-Code adoption company-wide, enabling reproducible, auditable deployments with full traceability
- Led ISO 27001 certification and AWS Partner review initiatives with security-first architecture patterns
- Mentored platform, infrastructure, and systems engineering teams across cloud-native and distributed systems domains
- Engineered automated provisioning, scaling, and decommissioning workflows eliminating manual operations overhead
- Implemented SRE best practices: on-call rotations, incident management, blameless postmortems, error budgets, chaos engineering, and continuous reliability testing

---

## Recognition & Major Initiatives

- AWS Partner badge (AWS Foundational Technical Review)
- ISO 27001 certification leadership
- Multi-cloud infrastructure migrations: Led EKS-to-AKS migrations across thousands of Kubernetes clusters; architected IaC for GCP MLOps infrastructure using Cloud Build, Cloud Run, and GKE with GPU inference
- Multiple Hackweek project winners: Agentic AI Platform on Kubernetes, Enterprise CLI tooling, GitOps automation (Flux, ArgoCD)
- Platform ecosystem initiatives: Established self-service strategies enabling product teams to accelerate time-to-market while maintaining security and compliance standards

---

## Contact

- **Email**: azizbek@gmail.com
- **GitHub**: [github.com/sqe](https://github.com/sqe)
- **Location**: Portland Oregon Metro Area (Remote)

---

**Open to discussing platform engineering challenges, infrastructure architecture, AI/MLOps systems, and open source collaboration.**

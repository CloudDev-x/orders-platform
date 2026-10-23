# orders-platform

Three FastAPI microservices (gateway, orders, notifications), each packaged as a Docker image. GitHub Actions builds and publishes them to Amazon ECR on every push to `main`.

## Services

| Service | Responsibility | Port |
|---|---|---|
| gateway | Public entry point. Routes `/orders` and `/notify` to internal services. | 8000 |
| orders | Order CRUD, stored in PostgreSQL via asyncpg. Emits order events. | 8000 |
| notifications | Receives order events and exposes `/notify` and `/notifications`. | 8000 |

Every service exposes `/healthz` (liveness) and `/readyz` (readiness) for Kubernetes.

## CI/CD

`.github/workflows/publish.yml` runs a matrix build over the three services. It authenticates to AWS with GitHub OIDC (no stored access keys), tags each image with the commit SHA, and pushes it to ECR.

## Related repositories

- **platform-infra**: Terraform that provisions the AWS foundation (VPC, EKS, ECR, IAM).
- **platform-gitops**: Helm charts and Argo CD configuration that deploy these images to the cluster.

## Run a service locally

From the service directory, install the requirements and start Uvicorn: `pip install -r requirements.txt`, then `uvicorn main:app --port 8000`. The orders service needs a `DATABASE_URL` environment variable pointing at PostgreSQL.

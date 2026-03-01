# Imbryk — Deployment Guide

This document covers the infrastructure setup, containerisation, and deployment procedures for all Imbryk services. See [ARCHITECTURE.md](ARCHITECTURE.md) for system design context and [PLAN.md](PLAN.md) for current progress.

---

## Infrastructure Overview

| Service | Platform | Trigger |
|---|---|---|
| Ingestion API | Cloud Run (service) | HTTP requests |
| Newsroom Director | Cloud Run (job) | Cloud Scheduler via Pub/Sub (daily) |
| Gazette | Cloudflare Pages | Rebuild after each edition |
| Prompt UI | Cloudflare Pages | Git push to main |
| Database | Cloud SQL (PostgreSQL 15) | Always-on |
| Object Storage | Cloudflare R2 | Written by Newsroom Director, read by Gazette |

---

## Prerequisites

### GCP Project Setup

```sh
# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  pubsub.googleapis.com \
  cloudscheduler.googleapis.com \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

### Service Account

Create a dedicated service account for the pipeline:

```sh
gcloud iam service-accounts create imbryk-pipeline \
  --display-name="Imbryk Pipeline"

# Grant roles
SA=imbryk-pipeline@$PROJECT_ID.iam.gserviceaccount.com

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" \
  --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" \
  --role="roles/pubsub.subscriber"
```

---

## Database (Cloud SQL)

### Provision

```sh
gcloud sql instances create imbryk-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-size=10GB \
  --storage-auto-increase

gcloud sql databases create imbryk --instance=imbryk-db

gcloud sql users set-password postgres \
  --instance=imbryk-db \
  --password="$DB_PASSWORD"
```

### Connection

Cloud Run services connect via the Cloud SQL Auth Proxy (built into Cloud Run's `--add-cloudsql-instances` flag). The `DATABASE_URL` follows the format:

```
postgresql+pg8000://postgres:PASSWORD@/imbryk?unix_sock=/cloudsql/PROJECT:REGION:imbryk-db/.s.PGSQL.5432
```

Store credentials in Secret Manager:

```sh
echo -n "$DATABASE_URL" | gcloud secrets create database-url --data-file=-
gcloud secrets add-iam-policy-binding database-url \
  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor"
```

### Migrations

Run Alembic migrations from a local machine with Cloud SQL Proxy or from a one-off Cloud Run job:

```sh
# Local with proxy
cloud-sql-proxy $PROJECT_ID:us-central1:imbryk-db &
DATABASE_URL="postgresql://postgres:$DB_PASSWORD@127.0.0.1:5432/imbryk" \
  uv run alembic upgrade head
```

---

## Edition JSON Storage — R2 vs GCS

The newsroom-director produces edition JSON (~50-200 KB per day). The gazette (on Cloudflare Pages) reads this JSON at build time to produce static HTML. The question: where should the intermediate JSON live?

**Decision: Cloudflare R2.**

| Factor | Cloudflare R2 | Google Cloud Storage |
|---|---|---|
| Storage | $0.015/GB/month (10 GB free) | $0.020/GB/month (5 GB free) |
| Writes | $0.36/M Class A (1M free) | $0.05/10K Class A |
| Reads | $0.036/M Class B (10M free) | $0.004/10K Class B |
| **Egress** | **$0 always** | **$0.12/GB to internet** |
| Gazette reads | Same network (Pages reads R2) | Cross-cloud (Pages fetches from GCS) |
| Director writes | Cross-cloud (Cloud Run writes via boto3) | Same network (native GCS SDK) |
| Auth | R2 credentials in GCP Secret Manager | Service account (zero config) |

At ~200 KB/day (~70 MB/year), both are effectively free for storage. The differentiator is the **read path**: the gazette builds daily on Cloudflare Pages. R2 reads are same-network with zero egress. GCS would charge egress on every build and add cross-cloud latency.

The cross-cloud write from Cloud Run to R2 is already implemented via boto3's S3-compatible API — a solved problem. GCS would only be cheaper if the gazette build also moved to GCP, which would add cost and complexity since the final HTML is served from Cloudflare Pages anyway.

If the project later needs the edition JSON publicly accessible (e.g., for a third-party API), R2's zero-egress policy means this costs nothing regardless of traffic.

## Cloudflare R2

### Bucket Setup

1. Create an R2 bucket named `imbryk-editions` in the Cloudflare dashboard
2. Generate an API token with read/write access to the bucket
3. Note the account ID, access key ID, and secret access key

### Store Credentials

```sh
gcloud secrets create r2-account-id --data-file=<(echo -n "$R2_ACCOUNT_ID")
gcloud secrets create r2-access-key-id --data-file=<(echo -n "$R2_ACCESS_KEY_ID")
gcloud secrets create r2-secret-access-key --data-file=<(echo -n "$R2_SECRET_ACCESS_KEY")
```

---

## Containerisation

### Ingestion API

```dockerfile
# apps/ingestion-api/Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY apps/ingestion-api/ .
RUN pip install --no-cache-dir uv && uv pip install --system .

EXPOSE 8080
CMD ["uvicorn", "ingestion_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Newsroom Director

The newsroom-director image is larger because it bundles the sentence-transformers model for local embedding.

```dockerfile
# apps/newsroom-director/Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY apps/newsroom-director/ .
RUN pip install --no-cache-dir uv && uv pip install --system .

# Pre-download the embedding model into the image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

CMD ["python", "-m", "newsroom_director.main"]
```

### Build and Push

```sh
# Artifact Registry repository
gcloud artifacts repositories create imbryk \
  --repository-format=docker \
  --location=us-central1

# Build and push
REPO=us-central1-docker.pkg.dev/$PROJECT_ID/imbryk

docker build -f apps/ingestion-api/Dockerfile -t $REPO/ingestion-api:latest .
docker push $REPO/ingestion-api:latest

docker build -f apps/newsroom-director/Dockerfile -t $REPO/newsroom-director:latest .
docker push $REPO/newsroom-director:latest
```

---

## Cloud Run Deployments

### Ingestion API (Service)

```sh
gcloud run deploy ingestion-api \
  --image=$REPO/ingestion-api:latest \
  --region=us-central1 \
  --service-account=$SA \
  --add-cloudsql-instances=$PROJECT_ID:us-central1:imbryk-db \
  --set-secrets="DATABASE_URL=database-url:latest" \
  --set-env-vars="VERTEX_AI_PROJECT=$PROJECT_ID" \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --allow-unauthenticated
```

### Newsroom Director (Job)

```sh
gcloud run jobs create newsroom-director \
  --image=$REPO/newsroom-director:latest \
  --region=us-central1 \
  --service-account=$SA \
  --add-cloudsql-instances=$PROJECT_ID:us-central1:imbryk-db \
  --set-secrets="\
    DATABASE_URL=database-url:latest,\
    R2_ACCOUNT_ID=r2-account-id:latest,\
    R2_ACCESS_KEY_ID=r2-access-key-id:latest,\
    R2_SECRET_ACCESS_KEY=r2-secret-access-key:latest" \
  --set-env-vars="\
    VERTEX_AI_PROJECT=$PROJECT_ID,\
    VERTEX_AI_LOCATION=us-central1,\
    R2_BUCKET_NAME=imbryk-editions,\
    ENABLE_VALIDATION=true,\
    ENABLE_CACHING=true" \
  --memory=4Gi \
  --cpu=2 \
  --task-timeout=30m \
  --max-retries=1
```

The 4 GiB memory allocation accommodates the sentence-transformers model loaded into memory during embedding.

---

## Scheduling

### Pub/Sub Topic

```sh
gcloud pubsub topics create morning-press-trigger
```

### Cloud Scheduler

```sh
gcloud scheduler jobs create http morning-press \
  --schedule="0 6 * * *" \
  --time-zone="UTC" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/newsroom-director:run" \
  --http-method=POST \
  --oauth-service-account-email=$SA
```

This triggers the newsroom-director Cloud Run Job at 06:00 UTC daily.

---

## Cloudflare Pages

### Gazette (Static Newspaper Site)

1. Connect the repository to Cloudflare Pages
2. Configure build settings:
   - Build command: `npx nx build gazette`
   - Build output directory: `dist/apps/gazette`
   - Root directory: `/`
3. Set environment variable: `NODE_VERSION=20`

### Post-Edition Rebuild

After the newsroom-director job completes, trigger a Cloudflare Pages deploy hook:

```sh
# Create a deploy hook in Cloudflare Pages dashboard, then:
gcloud secrets create cf-deploy-hook-url --data-file=<(echo -n "$DEPLOY_HOOK_URL")
```

Add a final step to the newsroom-director pipeline (or a Cloud Run post-job hook) that calls the deploy hook URL:

```sh
curl -X POST "$DEPLOY_HOOK_URL"
```

### Prompt UI

1. Connect the repository to a second Cloudflare Pages project
2. Configure build settings:
   - Build command: `npx nx build imbryk`
   - Build output directory: `dist/apps/imbryk`
   - Root directory: `/`
3. Set environment variables:
   - `NODE_VERSION=20`
   - `VITE_API_URL=https://ingestion-api-HASH-uc.a.run.app`

---

## Environment Variables Reference

### Ingestion API

| Variable | Source | Description |
|---|---|---|
| `DATABASE_URL` | Secret Manager | PostgreSQL connection string |
| `VERTEX_AI_PROJECT` | Env var | GCP project for Gemini categorisation |
| `BRAINTREE_MERCHANT_ID` | Secret Manager | Braintree credentials |
| `BRAINTREE_PUBLIC_KEY` | Secret Manager | Braintree credentials |
| `BRAINTREE_PRIVATE_KEY` | Secret Manager | Braintree credentials |

### Newsroom Director

| Variable | Source | Description |
|---|---|---|
| `DATABASE_URL` | Secret Manager | PostgreSQL connection string |
| `VERTEX_AI_PROJECT` | Env var | GCP project for Gemini |
| `VERTEX_AI_LOCATION` | Env var | Vertex AI region (default: us-central1) |
| `R2_ACCOUNT_ID` | Secret Manager | Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | Secret Manager | R2 API token key |
| `R2_SECRET_ACCESS_KEY` | Secret Manager | R2 API token secret |
| `R2_BUCKET_NAME` | Env var | R2 bucket name (default: imbryk-editions) |
| `ENABLE_VALIDATION` | Env var | World coherence validation (default: true) |
| `ENABLE_CACHING` | Env var | Vertex AI context caching (default: true) |
| `TOTAL_BUDGET_TOKENS` | Env var | Token budget per newspaper (default: 800000) |
| `MAX_CLUSTERS` | Env var | Max clusters per newspaper (default: 30) |

---

## CI/CD Pipeline

The existing GitHub Actions workflow (`.github/workflows/ci.yml`) runs lint, test, build, and typecheck on every PR and push to main. Deployment is handled separately:

### Deployment Flow

1. **PR merged to main** -> CI runs all checks
2. **Manual or scheduled**: Push new container images and update Cloud Run
3. **Daily 06:00 UTC**: Cloud Scheduler triggers newsroom-director job
4. **Job completes**: Deploy hook triggers gazette rebuild on Cloudflare Pages

### Updating Deployed Services

```sh
# Rebuild and push images
docker build -f apps/ingestion-api/Dockerfile -t $REPO/ingestion-api:latest .
docker push $REPO/ingestion-api:latest
gcloud run services update ingestion-api --image=$REPO/ingestion-api:latest --region=us-central1

docker build -f apps/newsroom-director/Dockerfile -t $REPO/newsroom-director:latest .
docker push $REPO/newsroom-director:latest
gcloud run jobs update newsroom-director --image=$REPO/newsroom-director:latest --region=us-central1
```

---

## Manual Job Execution

To trigger the newsroom-director outside the daily schedule:

```sh
gcloud run jobs execute newsroom-director --region=us-central1
```

To run with overrides (e.g., disable validation for testing):

```sh
gcloud run jobs execute newsroom-director \
  --region=us-central1 \
  --update-env-vars="ENABLE_VALIDATION=false"
```

---

## Estimated Monthly Costs

| Component | Monthly Cost | Notes |
|---|---|---|
| Cloud SQL (db-f1-micro) | ~$8 | Always-on, the single largest fixed cost |
| Cloud Run (ingestion-api) | ~$0-2 | Scale to zero, pay per request |
| Cloud Run Job (newsroom-director) | ~$0.50 | One 4 GiB / 2 vCPU execution per day, ~10 min |
| Vertex AI (Gemini) | ~$18 | ~$3/newspaper x 6 newspapers/day |
| Vertex AI (validation + mutation) | ~$2-4 | Pro model for coherence + ledger updates |
| Cloudflare R2 | $0 | Free tier covers years of editions |
| Cloudflare Pages (gazette) | $0 | Free tier |
| Cloudflare Pages (prompt UI) | $0 | Free tier |
| Artifact Registry | ~$0.50 | Two container images |
| Cloud Scheduler | $0 | 3 free jobs |
| Secret Manager | ~$0.06 | 6 secrets, minimal access |
| **Total** | **~$30-35/month** | Dominated by Cloud SQL + Gemini |

The Gemini spend (~$20/month) is proportional to active newspapers and model tiers, not prompt volume. Cloud SQL is the main fixed cost — consider Neon or Supabase free tier as an alternative if budget is critical.

---

## Monitoring

### Key Metrics

- **Cloud Run**: request count, latency, error rate, memory usage
- **Cloud SQL**: connections, query latency, storage usage
- **Vertex AI**: token usage per model tier, API error rate
- **R2**: storage size, request count

### Logging

The newsroom-director outputs structured JSON logs with fields: `edition_id`, `newspaper_id`, `model_tier`, `latency_ms`, `cluster_count`, `step`. These are queryable in Cloud Logging:

```
resource.type="cloud_run_job"
resource.labels.job_name="newsroom-director"
jsonPayload.step="complete"
```

### Alerts

Set up alerts for:
- Newsroom director job failure (any execution with non-zero exit code)
- Gemini API error rate > 5% over 10 minutes
- Cloud SQL connection count approaching limit
- R2 write failures

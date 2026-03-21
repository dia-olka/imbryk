# Imbryk — Deployment Guide

A step-by-step guide to get Imbryk running in production. Written for people who are not software engineers — you only need a web browser and the ability to enter card details.

See [ARCHITECTURE.md](ARCHITECTURE.md) for how the system works and [PLAN.md](PLAN.md) for development progress.

---

## Table of Contents

1. [What You Will Set Up](#1-what-you-will-set-up)
2. [Accounts You Need](#2-accounts-you-need)
3. [Step 1 — Google Cloud (Backend Infrastructure)](#step-1--google-cloud-backend-infrastructure)
4. [Step 2 — Stripe (Payment Processing)](#step-2--stripe-payment-processing)
5. [Step 3 — Cloudflare (Websites & File Storage)](#step-3--cloudflare-websites--file-storage)
6. [Step 4 — Connect Everything](#step-4--connect-everything)
   - [Step 4.5 — Set Up Automatic Deployment](#45-set-up-automatic-deployment-github-actions)
7. [Step 5 — Deploy the Code](#step-5--deploy-the-code)
8. [Step 6 — Set Up the Daily Schedule](#step-6--set-up-the-daily-schedule)
9. [Day-to-Day Operations](#day-to-day-operations)
   - [Enabling Topic Research](#enabling-topic-research)
10. [Monthly Costs](#monthly-costs)
11. [Monitoring & Alerts](#monitoring--alerts)
12. [Troubleshooting](#troubleshooting)
13. [Environment Variables Reference](#environment-variables-reference)

---

## 1. What You Will Set Up

Imbryk is made of several pieces that work together. Here is what each piece does:

| Piece                 | What it does                                         | Where it runs             |
| --------------------- | ---------------------------------------------------- | ------------------------- |
| **Prompt UI**         | The website where users type their event and pay     | Cloudflare Pages (free)   |
| **Ingestion API**     | Receives prompts, categorises them, handles payments | Google Cloud Run          |
| **Newsroom Director** | The daily job that generates newspaper articles      | Google Cloud Run          |
| **Database**          | Stores prompts, payments, and the world state        | Google Cloud SQL          |
| **Gazette**           | The newspaper website readers see (rebuilt daily)    | Cloudflare Pages (free)   |
| **File Storage**      | Stores the generated article files                   | Cloudflare R2 (free tier) |
| **Payments**          | Processes credit card payments from users            | Stripe                    |

You do not need to understand how these work internally. Just follow the steps to create accounts, click through the setup screens, and paste in the values where indicated.

---

## 2. Accounts You Need

You will create accounts on four services. All have free tiers or trial credits.

| Service          | What it's for                           | Cost to start                                                      |
| ---------------- | --------------------------------------- | ------------------------------------------------------------------ |
| **Google Cloud** | Runs the backend (API, database, AI)    | **Free — $300 credit for 90 days** (no charge until you use it up) |
| **Cloudflare**   | Hosts the two websites and stores files | **Free** (the free plan covers everything Imbryk needs)            |
| **Stripe**       | Processes payments from users           | **Free to set up** — Stripe charges per transaction (2.9% + 30¢)  |
| **Tavily**       | Searches real-world news for gap filling| **Free tier: 1,000 API calls/month** (the News Scout uses ~60-90/day) |

You will need a credit or debit card for Google Cloud, but you will not be charged right away.

---

## Step 1 — Google Cloud (Backend Infrastructure)

Google Cloud runs the backend: the API that receives prompts, the database that stores them, and the AI that generates newspaper articles.

### 1.1 Create a Google Cloud Account (Free $300 Credit)

Google offers a free trial with **$300 in credits** that lasts **90 days**. This is more than enough to run Imbryk for the trial period (estimated cost is ~$30-35/month). You will not be charged until the credits run out, and even then only if you manually upgrade to a paid account.

1. Go to [cloud.google.com/free](https://cloud.google.com/free)
2. Click **"Get started for free"**
3. Sign in with your Google account (Gmail), or create one
4. Enter your country and accept the terms of service
5. Enter your credit or debit card details — **you will not be charged**. Google requires a card to verify you are a real person, but the free trial does not bill you. You can see a banner at the top of the console confirming your remaining credits.
6. Once signed in, you will see the **Google Cloud Console** — a dashboard for managing everything

> **Tip:** Look for the "Free trial status" banner at the top of the console. It shows your remaining credit and days left. If the $300 runs out or the 90 days expire, Google will ask if you want to upgrade. If you do nothing, your services will simply stop — you will never receive a surprise bill.

### 1.2 Create a Project

Everything in Google Cloud lives inside a "project." Think of it like a folder.

1. In the Google Cloud Console, click the project dropdown at the top of the page (it may say "Select a project" or show an existing project name)
2. Click **"New Project"**
3. Enter a name, for example: `imbryk`
4. Click **"Create"**
5. Make sure your new project is selected in the dropdown

Write down your **Project ID** — it appears under the project name during creation and looks something like `imbryk-123456`. You will need it throughout this guide. Everywhere you see `$PROJECT_ID` below, substitute your actual project ID.

### 1.3 Turn On the Required Services

Google Cloud has many services, and they are turned off by default. You need to turn on the ones Imbryk uses.

1. In the Cloud Console, go to **APIs & Services > Library** (use the search bar or the left-side menu)
2. Search for and enable each of these (click the service name, then click **"Enable"**):
   - **Cloud Run API** — runs the backend applications
   - **Cloud SQL Admin API** — manages the database
   - **Pub/Sub API** — internal messaging between services
   - **Cloud Scheduler API** — triggers the daily newspaper generation
   - **Vertex AI API** — the AI that writes articles and generates images
   - **Artifact Registry API** — stores the application container images
   - **Secret Manager API** — securely stores passwords and API keys
   - **IAM Service Account Credentials API** — required for service account authentication

> **Note:** Enabling an API does not cost anything. You are only charged when you actually use the service.

Alternatively, if you have the `gcloud` command-line tool installed (see Section 1.7), you can enable all at once:

```sh
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  pubsub.googleapis.com \
  cloudscheduler.googleapis.com \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  iamcredentials.googleapis.com
```

### 1.4 Create a Service Account

A service account is like a special user identity that the application uses to access Google Cloud services. The application logs in as this account instead of as you.

1. Go to **IAM & Admin > Service Accounts** in the Cloud Console
2. Click **"Create Service Account"**
3. Enter:
   - **Name:** `imbryk-pipeline`
   - **Description:** `Imbryk application service account`
4. Click **"Create and Continue"**
5. Add these roles (click "Add Another Role" for each one):
   - `Cloud Run Invoker` — lets it trigger Cloud Run services
   - `Cloud SQL Client` — lets it connect to the database
   - `Vertex AI User` — lets it use the AI
   - `Pub/Sub Subscriber` — lets it receive internal messages
   - `Secret Manager Secret Accessor` — lets it read stored passwords
6. Click **"Done"**

Write down the service account email — it looks like: `imbryk-pipeline@YOUR-PROJECT-ID.iam.gserviceaccount.com`

### 1.5 Create the Database

The database stores prompts, payment records, and the world state.

1. Go to **SQL** in the Cloud Console (search for "SQL" in the top search bar)
2. Click **"Create Instance"**
3. Choose **PostgreSQL**
4. Configure:
   - **Instance ID:** `imbryk-db`
   - **Password:** choose a strong password and **write it down** — you will need it later. This is the database administrator password.
   - **Database version:** PostgreSQL 15
   - **Region:** `us-central1` (Iowa) — this is a good default that keeps costs low
   - **Machine type:** under "Machine Configuration", pick **Shared core > db-f1-micro** (the cheapest option, ~$8/month)
   - **Storage:** 10 GB, enable auto-increase
   - **Flags:** click **"Add Flag"**, search for `cloudsql.iam_authentication`, set it to `on`
5. Click **"Create Instance"** — this takes a few minutes

Once the instance is ready:

6. Click on the instance name `imbryk-db`
7. Go to the **"Databases"** tab
8. Click **"Create Database"**
9. Enter name: `imbryk`
10. Click **"Create"**

### 1.5a Enable IAM Database Authentication

This lets your Google account (and the service account) log in to the database using Google credentials instead of a password — no password to manage or leak.

If you did not enable the flag during instance creation, enable it now:

1. Go to **SQL > imbryk-db > Edit**
2. Scroll to **Flags**
3. Click **"Add Flag"**, search for `cloudsql.iam_authentication`, set it to `on`
4. Click **"Save"** — the instance will restart (takes ~1 minute)

Or with `gcloud`:

```sh
gcloud sql instances patch imbryk-db \
  --database-flags=cloudsql.iam_authentication=on
```

#### Add Your Google Account as an IAM Database User

```sh
# Replace with your Google account email
gcloud sql users create YOUR_EMAIL@gmail.com \
  --instance=imbryk-db \
  --type=cloud_iam_user
```

Or in the Console:

1. Go to **SQL > imbryk-db > Users**
2. Click **"Add User Account"**
3. Select **"Cloud IAM"**
4. Enter your Google email address
5. Click **"Add"**

#### Add the Service Account as an IAM Database User

```sh
PROJECT_ID=imbryk
SA=imbryk-pipeline@$PROJECT_ID.iam.gserviceaccount.com

gcloud sql users create $SA \
  --instance=imbryk-db \
  --type=cloud_iam_service_account
```

#### Grant Database Permissions

Connect to the database once using the `postgres` password (Cloud Shell, see below) and run:

```sql
-- Grant your Google account access to the database
GRANT ALL PRIVILEGES ON DATABASE imbryk TO "YOUR_EMAIL@gmail.com";

-- Grant the service account access to the database
GRANT ALL PRIVILEGES ON DATABASE imbryk TO "imbryk-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com";
```

> **Important:** The grants above only allow connecting to the database. After running migrations (Step 5.2), you must also grant access to **tables and the schema**. Connect as `postgres` again and run:

```sql
-- Grant schema and table access to your Google account
GRANT USAGE ON SCHEMA public TO "YOUR_EMAIL@gmail.com";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "YOUR_EMAIL@gmail.com";

-- Ensure future tables (from new migrations) are also accessible
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  GRANT ALL PRIVILEGES ON TABLES TO "YOUR_EMAIL@gmail.com";

-- Same for the service account
GRANT USAGE ON SCHEMA public TO "imbryk-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "imbryk-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com";
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public
  GRANT ALL PRIVILEGES ON TABLES TO "imbryk-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com";
```

> Without these table-level grants, IAM users can connect but will not see or query any tables (e.g. Cloud SQL Studio will show "Tables 0").

#### Connecting via Cloud Shell (IAM)

1. Open **Cloud Shell** (the `>_` icon in the top-right of the Google Cloud Console)
2. Run:

```sh
# Authenticate (already done in Cloud Shell, but run if needed)
gcloud auth login

# Connect — Cloud Shell handles IAM token automatically
gcloud sql connect imbryk-db \
  --user=YOUR_EMAIL@gmail.com \
  --database=imbryk
```

> **No password prompt** — your Google identity is used automatically. If it asks for a password anyway, press **Enter** (blank) or check that `cloudsql.iam_authentication` is enabled.

#### Connecting Locally (IAM via Cloud SQL Proxy)

If you want to connect from your own machine without a password:

1. Install the Cloud SQL Auth Proxy: [cloud.google.com/sql/docs/postgres/connect-auth-proxy](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy)
2. Run:

```sh
# Start the proxy (uses your gcloud credentials automatically)
cloud-sql-proxy "$PROJECT_ID:us-central1:imbryk-db" --auto-iam-authn &

# Connect with psql — no password needed
psql "host=127.0.0.1 dbname=imbryk user=YOUR_EMAIL@gmail.com sslmode=disable"
```

#### Update the Database URL for the Service Account (IAM)

When the service account connects via IAM, the connection string in Secret Manager changes slightly — no password field:

```
postgresql+pg8000://imbryk-pipeline@YOUR_PROJECT_ID.iam.gserviceaccount.com@/imbryk?unix_sock=/cloudsql/YOUR_PROJECT_ID:us-central1:imbryk-db/.s.PGSQL.5432&enable_iam_auth=true
```

Update the `database-url` secret in Secret Manager with this value (see Step 1.6).

### 1.6 Store the Database Password Securely

Instead of putting passwords directly in configuration, Google Cloud has a "Secret Manager" that stores them securely.

The database connection string is a URL that tells the application how to connect. It looks like this (replace `YOUR_PASSWORD` and `YOUR_PROJECT_ID`):

```
postgresql+pg8000://postgres:YOUR_PASSWORD@/imbryk?unix_sock=/cloudsql/YOUR_PROJECT_ID:us-central1:imbryk-db/.s.PGSQL.5432
```

To store it:

1. Go to **Security > Secret Manager** in the Cloud Console
2. Click **"Create Secret"**
3. **Name:** `database-url`
4. **Secret value:** paste the connection string above (with your actual password and project ID filled in)
5. Click **"Create Secret"**

### 1.7 Install the Command-Line Tool (Optional but Recommended)

Some of the remaining steps are easier to do from a command line. Google provides a tool called `gcloud` for this.

1. Go to [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
2. Follow the instructions for your operating system (macOS, Windows, or Linux)
3. After installation, open your terminal (Terminal on macOS, Command Prompt on Windows) and run:

```sh
gcloud init
```

4. Follow the prompts to log in and select your project

### 1.8 Set Up the Container Image Registry

Container images are packaged versions of the application code, ready to run. They are stored in a registry.

```sh
gcloud artifacts repositories create imbryk \
  --repository-format=docker \
  --location=us-central1
```

Or in the Console:

1. Go to **Artifact Registry**
2. Click **"Create Repository"**
3. **Name:** `imbryk`, **Format:** Docker, **Region:** `us-central1`
4. Click **"Create"**

---

## Step 2 — Stripe (Payment Processing)

Stripe handles credit card payments. Users are redirected to a Stripe-hosted checkout page, and Imbryk never sees or stores their card details.

### 2.1 Create a Stripe Account

1. Go to [dashboard.stripe.com/register](https://dashboard.stripe.com/register)
2. Fill in your details and create an account
3. Once signed in, you will see the Stripe dashboard in **test mode** (toggle in the top right)

### 2.2 Find Your API Keys

1. In the Stripe dashboard, go to **Developers > API keys**
2. You will see two values:
   - **Publishable key** (`pk_test_...`) — used by browser-side integrations (not needed for Imbryk)
   - **Secret key** (`sk_test_...`) — used by the backend server (keep secret — click "Reveal" to see it)
3. Write down the **Secret key** — that is the only key Imbryk needs

> **Why not the Publishable key?** Imbryk uses Stripe Hosted Checkout: the server creates a checkout session and redirects the user to a Stripe-hosted page. The Publishable key is only needed when embedding Stripe's JavaScript directly in a webpage, which Imbryk does not do.

### 2.3 Going Live (When Ready for Real Payments)

When you are ready to accept real money (not just test transactions):

1. In the Stripe dashboard, click **Settings > Account details** and complete the activation form
2. Stripe will ask about your business — fill in the details and submit
3. Once approved, toggle **test mode off** in the dashboard to see your live API keys (`pk_live_...` and `sk_live_...`)
4. Replace the test keys with the live keys in Google Secret Manager (Step 2.4)

> **Note:** Keep using test mode for testing. Only switch to live keys when you are confident everything works. In test mode, you can use the test card number `4242 4242 4242 4242` with any future expiration date and any 3-digit CVC.

### 2.4 Store Stripe Keys in Google Cloud

Go to **Secret Manager** in the Google Cloud Console and create two secrets:

| Secret Name              | Value                              |
| ------------------------ | ---------------------------------- |
| `stripe-secret-key`      | Your Secret Key from Step 2.2      |
| `stripe-webhook-secret`  | Your Webhook Signing Secret (2.5)  |

> **Note:** Create the `stripe-webhook-secret` placeholder now (you can update its value after completing Step 2.5). Both secrets must exist in Secret Manager before deploying the Ingestion API.

For each one:

1. Click **"Create Secret"**
2. Enter the name and paste the value
3. Click **"Create Secret"**

### 2.5 Configure Stripe Webhooks

Stripe sends server-to-server webhook notifications when a checkout session completes and when disputes (chargebacks) occur. The Ingestion API has a `POST /payments/stripe-webhook` endpoint that listens for these.

1. In the Stripe dashboard, go to **Developers > Webhooks**
2. Click **"Add endpoint"**
3. **Endpoint URL:** `https://<YOUR-INGESTION-API-URL>/payments/stripe-webhook`
   - Replace `<YOUR-INGESTION-API-URL>` with the Cloud Run URL from Step 5, e.g. `https://ingestion-api-abc123-uc.a.run.app/payments/stripe-webhook`
4. Under **Events to send**, select these events:
   - `checkout.session.completed` — fires when a customer completes payment
   - `charge.dispute.created` — fires when a customer disputes a charge
   - `charge.dispute.closed` — fires when a dispute is resolved (won or lost)
5. Click **"Add endpoint"**
6. On the endpoint detail page, click **"Reveal"** under **Signing secret** — copy this value (`whsec_...`)
7. Store this signing secret in Google Secret Manager as `stripe-webhook-secret` (Step 2.4)

> **Note:** The webhook endpoint uses the signing secret to verify every incoming notification. This is separate from your API keys.

### 2.6 Enable Adaptive Pricing (Optional)

Stripe Adaptive Pricing automatically converts prices and displays local currencies to international customers on the checkout page.

1. In the Stripe dashboard, go to **Settings > Payments > Adaptive Pricing**
2. Toggle it on
3. No code changes are needed — Stripe handles everything on the hosted checkout page

> **Production:** When you switch to live keys (Step 2.3), repeat the webhook setup in the **live mode** dashboard with the same endpoint URL and events. You will get a new signing secret for live mode.

---

## Step 3 — Cloudflare (Websites & File Storage)

Cloudflare hosts the two websites (the prompt submission page and the newspaper reading site) and stores the generated article files. The free plan covers everything.

### 3.1 Create a Cloudflare Account

1. Go to [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up)
2. Enter your email and a password
3. You will be on the **Free plan** by default — that is all you need

### 3.2 Set Up R2 File Storage

R2 is Cloudflare's file storage. The daily newspaper generation job saves article files here, and the gazette website reads from it.

1. In the Cloudflare dashboard, click **"R2 Object Storage"** in the left sidebar
2. If prompted, add a payment method (you will not be charged — the free tier includes 10 GB storage and 10 million reads/month)
3. Click **"Create Bucket"**
4. **Bucket name:** `imbryk-editions`
5. **Location:** Automatic
6. Click **"Create Bucket"**
7. **Connect a custom domain** (so the gazette can read editions via a production-ready, cached URL):
   - Click on the `imbryk-editions` bucket
   - Go to **Settings > Public access**
   - Under **Custom Domains**, click **"Connect Domain"**
   - Enter a subdomain on your Cloudflare-managed domain, e.g. `editions.yourdomain.com`
   - Cloudflare will automatically create a CNAME record and enable caching
   - Write down the custom domain URL (e.g. `https://editions.yourdomain.com`) — you will need it when setting up the gazette (Step 3.6) and the newsroom director (Step 5.3)

> **Why a custom domain instead of the r2.dev URL?** The default `r2.dev` public URL is rate-limited and bypasses Cloudflare's CDN cache. A custom domain gives you production-grade performance, caching, and the ability to use Cloudflare Access if needed later.

### 3.3 Create R2 API Credentials

The backend (running on Google Cloud) needs credentials to write files to R2.

1. Go to **R2 Object Storage > Manage R2 API Tokens** (or go to **My Profile > API Tokens**)
2. Click **"Create API Token"**
3. **Permissions:** Object Read & Write
4. **Specify bucket:** select `imbryk-editions`
5. Click **"Create API Token"**
6. Write down:
   - **Access Key ID**
   - **Secret Access Key**
   - Your **Account ID** (shown at the top of the R2 page or in your Cloudflare dashboard URL)

### 3.4 Store R2 Credentials in Google Cloud

Go to **Secret Manager** in Google Cloud Console and create three secrets:

| Secret Name            | Value                               |
| ---------------------- | ----------------------------------- |
| `r2-account-id`        | Your Cloudflare Account ID          |
| `r2-access-key-id`     | The Access Key ID from Step 3.3     |
| `r2-secret-access-key` | The Secret Access Key from Step 3.3 |

### 3.4a Store Tavily API Key in Google Cloud

The News Scout uses [Tavily](https://tavily.com/) to search for real-world news. Store the API key in Secret Manager:

1. Sign up at [app.tavily.com](https://app.tavily.com/) and copy your API key
2. In **Secret Manager**, click **"Create Secret"**
3. **Name:** `tavily-api-key`
4. **Secret value:** paste your Tavily API key
5. Click **"Create Secret"**

### 3.4b Store Cloudflare Analytics Credentials in Google Cloud (Optional)

If you plan to use the **Reader Metrics** feature (the newsroom director fetches page-view data from Cloudflare to help AI editors learn what resonates with readers), store these credentials in Secret Manager:

1. In the Cloudflare dashboard, go to **My Profile > API Tokens**
2. Click **"Create Token"** and create a token with **Permissions:** `Analytics:Read` for your gazette zone
3. Copy the token value
4. Note your **Zone ID** — visible at the bottom of your zone's Overview page in the Cloudflare dashboard
5. In Google Cloud **Secret Manager**, click **"Create Secret"**:
   - **Name:** `cf-analytics-zone-id`
   - **Secret value:** your Zone ID
6. Click **"Create Secret"** again:
   - **Name:** `cf-analytics-api-token`
   - **Secret value:** the API token from step 3

### 3.5 Deploy the Prompt UI Website

1. Go to **Workers & Pages** in the Cloudflare dashboard
2. Click **"Create"**, then select the **"Pages"** tab
3. Click **"Connect to Git"**
4. Connect your GitHub account and select the Imbryk repository
5. Configure build settings:
   - **Project name:** `imbryk` (or any name you like — this becomes the URL)
   - **Production branch:** `main`
   - **Build command:** `npx nx build imbryk`
   - **Build output directory:** `dist/apps/imbryk`
   - **Root directory:** `/` (leave as default)
6. Add environment variables:
   - `NODE_VERSION` = `20`
   - `VITE_API_URL` = (you will fill this in after deploying the API in Step 5 — come back to this)
7. Click **"Save and Deploy"**

Your prompt UI will be live at `https://whisper.imbryk.news` (or whatever project name you chose).

### 3.6 Deploy the Gazette Website

1. Repeat the process from Step 3.5 but for a second Pages project:
   - **Project name:** `imbryk-gazette` (or whatever you prefer)
   - **Build command:** `npx nx build gazette`
   - **Build output directory:** `dist/apps/gazette`
   - `NODE_VERSION` = `20`
   - `R2_PUBLIC_URL` = the custom domain URL from Step 3.2 (e.g. `https://editions.yourdomain.com`)
   - `CF_WEB_ANALYTICS_TOKEN` = _(optional)_ your Cloudflare Web Analytics token (see Step 3.7)
2. Click **"Save and Deploy"**
3. Set up a **Deploy Hook** (for automatic rebuilds after each newspaper edition):
   - Go to the gazette project **Settings > Builds & Deployments**
   - Scroll to **Deploy Hooks**
   - Click **"Add Deploy Hook"**, give it a name like `newsroom-rebuild`, select the `main` branch
   - Copy the hook URL and save it as a secret in Google Cloud Secret Manager with the name `cf-deploy-hook-url`

> **How the deploy hook works:** After the newsroom director generates a new edition, it writes the edition JSON and an index manifest to R2, then automatically POSTs to this hook URL to trigger a gazette rebuild. The gazette build fetches edition data from R2 via the custom domain.

### 3.7 Set Up Cloudflare Web Analytics (Optional)

Cloudflare Web Analytics tracks reader engagement on the gazette — privacy-first, no cookies. The newsroom director can use this data to help AI editors learn what resonates with readers.

1. In the Cloudflare dashboard, go to **Analytics & Logs > Web Analytics**
2. Click **"Add a site"** and enter your gazette domain (e.g. `imbryk.news`)
3. Copy the **JS Snippet token** (a UUID that appears in the snippet code)
4. Go to your gazette Pages project (**Workers & Pages > imbryk-gazette**)
5. Go to **Settings > Environment Variables**
6. Add: `CF_WEB_ANALYTICS_TOKEN` = _(paste the token)_
7. Trigger a new deployment

The gazette already includes the Web Analytics beacon in its HTML — it activates automatically when this token is set.

> **For Reader Metrics backend integration:** If you also want the newsroom director to fetch page-view data and feed it into editorial reflections, see Step 3.4b for storing your Cloudflare API credentials in Secret Manager, and set `ENABLE_READER_METRICS=true` in the newsroom director configuration (Step 5.3).

---

## Step 4 — Connect Everything

Now you need to tell the backend services about each other. This is done by deploying the code with the right configuration.

### 4.1 Build and Upload the Application Images

After the initial deployment (Step 5), container images are built and pushed **automatically** by the CD workflow whenever you push to `main`. See [Step 4.5](#45-set-up-automatic-deployment-github-actions) to set this up.

For the **first deployment only**, you need to build and push the images manually so that the `gcloud run deploy` and `gcloud run jobs create` commands in Step 5 have an image to reference.

<details>
<summary>Manual build commands (first-time setup / fallback)</summary>

```sh
# Set your project and registry path
PROJECT_ID=your-project-id
REPO=us-central1-docker.pkg.dev/$PROJECT_ID/imbryk

# Generate Python data files from JSON (required before Docker build)
npx nx run-many --target=generate-data --projects=ingestion-api,newsroom-director

# Build and upload the Ingestion API
docker build -f apps/ingestion-api/Dockerfile -t $REPO/ingestion-api:latest apps/ingestion-api
docker push $REPO/ingestion-api:latest

# Build and upload the Newsroom Director
docker build -f apps/newsroom-director/Dockerfile -t $REPO/newsroom-director:latest apps/newsroom-director
docker push $REPO/newsroom-director:latest
```

> **Note:** You need Docker installed for this step. If you do not have Docker, download it from [docker.com/get-started](https://www.docker.com/get-started/). The newsroom-director image is large (~2 GB) because it includes the AI model for text processing. The upload may take several minutes depending on your internet speed.

</details>

---

### 4.5 Set Up Automatic Deployment (GitHub Actions)

After the initial manual deployment (Step 5), all subsequent deploys are handled automatically. Pushing code to `main` triggers a CD workflow that builds container images, deploys to Cloud Run, and runs database migrations.

The workflow uses **Workload Identity Federation** — a keyless authentication method where GitHub Actions proves its identity to Google Cloud without storing any credentials.

#### Create a Workload Identity Pool and Provider

Run these commands once (requires the `gcloud` CLI from Step 1.7):

```sh
PROJECT_ID=your-project-id
GITHUB_ORG=your-github-org   # e.g. "dia-olka"
GITHUB_REPO=your-repo-name   # e.g. "imbryk"

# Create the Workload Identity Pool
gcloud iam workload-identity-pools create github \
  --location=global \
  --display-name="GitHub Actions"

# Create the Provider (links GitHub OIDC tokens to the pool)
gcloud iam workload-identity-pools providers create-oidc github-actions \
  --location=global \
  --workload-identity-pool=github \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='$GITHUB_ORG/$GITHUB_REPO'"

# Allow the GitHub Actions provider to impersonate the service account
SA=imbryk-pipeline@$PROJECT_ID.iam.gserviceaccount.com

gcloud iam service-accounts add-iam-policy-binding $SA \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/github/attribute.repository/$GITHUB_ORG/$GITHUB_REPO"

# Grant the service account permissions to push images and deploy
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" \
  --role=roles/artifactregistry.writer

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA" \
  --role=roles/run.admin

gcloud iam service-accounts add-iam-policy-binding $SA \
  --role=roles/iam.serviceAccountUser \
  --member="serviceAccount:$SA"
```

#### Configure GitHub Repository Secrets and Variables

In your GitHub repository, go to **Settings > Secrets and variables > Actions** and add:

**Variables** (Settings > Variables > New repository variable):

| Variable                 | Value                                                     | Example                                                                                  |
| ------------------------ | --------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `GCP_PROJECT_ID`         | Your Google Cloud project ID                              | `imbryk-123456`                                                                          |
| `GCP_WIF_PROVIDER`       | The full Workload Identity provider resource name         | `projects/123456/locations/global/workloadIdentityPools/github/providers/github-actions` |
| `GCP_SERVICE_ACCOUNT`    | The service account email                                 | `imbryk-pipeline@imbryk-123456.iam.gserviceaccount.com`                                  |
| `GCP_REGION`             | Google Cloud region (optional, defaults to `us-central1`) | `us-central1`                                                                            |
| `VERTEX_AI_LOCATION`     | Vertex AI region for Gemini models (optional, defaults to `global`) | `global`                                                                           |
| `CATEGORISER_MODEL`      | Gemini model used to categorise prompts in ingestion-api  | `gemini-3.1-flash-lite-preview`                                                          |
| `GENERATION_MODEL_PRO`   | Gemini Pro model for The Sovereign, The Owner, Curator, validation, and ledger mutation | `gemini-3.1-pro-preview`              |
| `GENERATION_MODEL_FLASH` | Gemini Flash model for The Aspirant, The Moralist, The Radical, The Hedonist            | `gemini-3-flash-preview`              |
| `IMAGE_GENERATION_MODEL` | Vertex AI Imagen model for article and hero images        | `imagen-4.0-generate-001`                                                             |
| `IMAGE_GENERATION_LOCATION` | Region for Imagen (optional, defaults to `us-central1`; Imagen does not support `global`) | `us-central1`                                        |
| `SENTRY_DSN`             | Sentry error tracking URL (leave empty to disable)        | `https://abc123@o0.ingest.sentry.io/0`                                                   |
| `R2_PUBLIC_URL`          | Custom domain URL for the R2 bucket                       | `https://editions.yourdomain.com`                                                        |

To find the full `GCP_WIF_PROVIDER` value:

```sh
gcloud iam workload-identity-pools providers describe github-actions \
  --location=global \
  --workload-identity-pool=github \
  --format='value(name)'
```

**Secrets** (Settings > Secrets > New repository secret):

| Secret        | Value                               |
| ------------- | ----------------------------------- |
| `DB_PASSWORD` | The database password from Step 1.5 |

#### How It Works

The CD workflow (`.github/workflows/cd.yml`) runs after CI passes on `main`:

1. Detects which services changed (ingestion-api, newsroom-director, or both)
2. Builds and pushes Docker images to Artifact Registry
3. Deploys the ingestion-api to Cloud Run and runs database migrations
4. Updates the newsroom-director Cloud Run job

The newsroom-director build uses GitHub Actions cache for Docker layers, which significantly speeds up builds of the ~2 GB image.

---

## Step 5 — Deploy the Code

### 5.1 Deploy the Ingestion API

This is the backend that receives prompts, processes payments, and talks to the AI for categorisation.

```sh
# Replace with your actual Google Cloud project ID (lowercase, e.g. imbryk-123456)
# Run ALL lines below in the same terminal session
PROJECT_ID=imbryk
REPO=us-central1-docker.pkg.dev/$PROJECT_ID/imbryk
SA=imbryk-pipeline@$PROJECT_ID.iam.gserviceaccount.com

gcloud run deploy ingestion-api \
  --image=$REPO/ingestion-api:latest \
  --region=us-central1 \
  --service-account=$SA \
  --set-cloudsql-instances="${PROJECT_ID}:us-central1:imbryk-db" \
  --set-secrets=DATABASE_URL=database-url:latest \
  --set-secrets=STRIPE_SECRET_KEY=stripe-secret-key:latest \
  --set-secrets=STRIPE_WEBHOOK_SECRET=stripe-webhook-secret:latest \
  --set-env-vars=VERTEX_PROJECT="${PROJECT_ID}" \
  --set-env-vars=VERTEX_LOCATION=global \
  --set-env-vars=CORS_ALLOWED_ORIGINS=https://whisper.imbryk.news \
  --set-env-vars=SENTRY_DSN="" \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=5 \
  --allow-unauthenticated
```

After this command completes, it will print a URL like `https://ingestion-api-abc123-uc.a.run.app`. **Write this URL down** — this is your API address.

> **Important:** Go back to your Cloudflare Pages prompt UI project (Step 3.5) and set the `VITE_API_URL` environment variable to this URL. Then trigger a new deployment in Cloudflare Pages to apply the change.

Also update the `CORS_ALLOWED_ORIGINS` value to match your actual Cloudflare Pages URL if it differs from the example above.

> **Subsequent updates are automatic.** After setting up the CD workflow ([Step 4.5](#45-set-up-automatic-deployment-github-actions)), pushing changes to `main` will automatically build a new image and update this Cloud Run service.

### 5.2 Run Database Migrations

The database needs its tables set up before it can store anything. Run this manually for the **first deployment**. After that, migrations run automatically as part of the CD workflow ([Step 4.5](#45-set-up-automatic-deployment-github-actions)).

> **Recent migrations:** Migration **008** adds the `editorial_journal` table (Editorial Journal feature) and migration **009** adds the `edition_metrics` table (Reader Metrics feature). Both are safe to run — the tables are only populated when the respective features are enabled.

<details>
<summary>First-time setup / manual fallback</summary>

```sh
# Activate the Python virtual environment
source apps/ingestion-api/.venv/bin/activate

# Start the Cloud SQL proxy (connects your computer to the cloud database)
cloud-sql-proxy "${PROJECT_ID}:us-central1:imbryk-db" &

# Run the migration (creates all database tables)
cd apps/ingestion-api
DATABASE_URL="postgresql+pg8000://postgres:YOUR_DB_PASSWORD@127.0.0.1:5432/imbryk" \
alembic upgrade head
```

> **Note:** You need the `cloud-sql-proxy` tool for this. Install it from [cloud.google.com/sql/docs/postgres/connect-auth-proxy](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy). Replace `YOUR_DB_PASSWORD` with the password you set in Step 1.5.

</details>

### 5.3 Deploy the Newsroom Director

This is the daily job that generates newspaper articles.

```sh
PROJECT_ID=imbryk
REPO=us-central1-docker.pkg.dev/$PROJECT_ID/imbryk
SA=imbryk-pipeline@$PROJECT_ID.iam.gserviceaccount.com

gcloud run jobs create newsroom-director \
  --image=$REPO/newsroom-director:latest \
  --region=us-central1 \
  --service-account=$SA \
  --set-cloudsql-instances="${PROJECT_ID}:us-central1:imbryk-db" \
  --set-secrets=DATABASE_URL=database-url:latest \
  --set-secrets=R2_ACCOUNT_ID=r2-account-id:latest \
  --set-secrets=R2_ACCESS_KEY_ID=r2-access-key-id:latest \
  --set-secrets=R2_SECRET_ACCESS_KEY=r2-secret-access-key:latest \
  --set-secrets=CF_DEPLOY_HOOK_URL=cf-deploy-hook-url:latest \
  --set-secrets=TAVILY_API_KEY=tavily-api-key:latest \
  --set-env-vars=JOB_MODE=morning-press \
  --set-env-vars=VERTEX_AI_PROJECT=$PROJECT_ID \
  --set-env-vars=VERTEX_AI_LOCATION=global \
  --set-env-vars=R2_BUCKET_NAME=imbryk-editions \
  --set-env-vars=R2_PUBLIC_URL=https://editions.yourdomain.com \
  --set-env-vars=ENABLE_IMAGES=true \
  --set-env-vars=ENABLE_VALIDATION=true \
  --set-env-vars=NEWS_SCOUT_ENABLED=true \
  --set-env-vars=TAVILY_RPM=99 \
  --set-env-vars=TAVILY_MONTHLY_LIMIT=999 \
  --set-env-vars=NEWS_ITEM_BASE_WEIGHT=0.3 \
  --set-env-vars=NEWS_MUTATES_LEDGER=true \
  --set-env-vars=ENABLE_EDITORIAL_JOURNAL=true \
  --set-env-vars=JOURNAL_LOOKBACK_DAYS=7 \
  --set-env-vars=ENABLE_READER_METRICS=false \
  --set-env-vars=TOPIC_RESEARCH_ENABLED=false \
  --set-env-vars=TOPIC_RESEARCH_MAX_QUERIES=3 \
  --set-secrets=CF_ANALYTICS_ZONE_ID=cf-analytics-zone-id:latest \
  --set-secrets=CF_ANALYTICS_API_TOKEN=cf-analytics-api-token:latest \
  --set-env-vars=SENTRY_DSN="" \
  --memory=4Gi \
  --cpu=2 \
  --task-timeout=30m \
  --max-retries=1
```

Then create the **News Scout** job (same image, different `JOB_MODE`):

```sh
gcloud run jobs create newsroom-director-scout \
  --image=$REPO/newsroom-director:latest \
  --region=us-central1 \
  --service-account=$SA \
  --set-cloudsql-instances="${PROJECT_ID}:us-central1:imbryk-db" \
  --set-secrets=DATABASE_URL=database-url:latest \
  --set-secrets=TAVILY_API_KEY=tavily-api-key:latest \
  --set-env-vars=JOB_MODE=news-scout \
  --set-env-vars=VERTEX_AI_PROJECT=$PROJECT_ID \
  --set-env-vars=VERTEX_AI_LOCATION=global \
  --set-env-vars=NEWS_SCOUT_ENABLED=true \
  --set-env-vars=TAVILY_RPM=99 \
  --set-env-vars=TAVILY_MONTHLY_LIMIT=999 \
  --set-env-vars=TAVILY_SEARCH_DEPTH=basic \
  --set-env-vars=TAVILY_MAX_QUERIES_PER_CATEGORY=1 \
  --set-env-vars=SENTRY_DSN="" \
  --memory=4Gi \
  --cpu=2 \
  --task-timeout=30m \
  --max-retries=1
```

Then create the **Marketing Agent** job (same image, `JOB_MODE=marketing`):

```sh
gcloud run jobs create newsroom-director-marketing \
  --image=$REPO/newsroom-director:latest \
  --region=us-central1 \
  --service-account=$SA \
  --set-cloudsql-instances="${PROJECT_ID}:us-central1:imbryk-db" \
  --set-secrets=DATABASE_URL=database-url:latest \
  --set-secrets=BLUESKY_APP_PASSWORD=bluesky-app-password:latest \
  --set-secrets=CF_ANALYTICS_ZONE_ID=cf-analytics-zone-id:latest \
  --set-secrets=CF_ANALYTICS_API_TOKEN=cf-analytics-api-token:latest \
  --set-env-vars=JOB_MODE=marketing \
  --set-env-vars=VERTEX_AI_PROJECT=$PROJECT_ID \
  --set-env-vars=VERTEX_AI_LOCATION=global \
  --set-env-vars=R2_PUBLIC_URL=https://editions.yourdomain.com \
  --set-env-vars=MARKETING_ENABLED=true \
  --set-env-vars=BLUESKY_HANDLE=imbryk-gazette.bsky.social \
  --set-env-vars=SENTRY_DSN="" \
  --memory=2Gi \
  --cpu=1 \
  --task-timeout=10m \
  --max-retries=1
```

> **Three jobs, one image.** All Cloud Run Jobs use the same Docker image. The `JOB_MODE` env var selects the entry point via `newsroom_director/__main__.py`: `morning-press` (default) runs the full newspaper generation pipeline, `news-scout` runs the Tavily collection pre-batch job, and `marketing` runs the autonomous social media promotion agent.

> **Why 4 GB memory?** The newsroom director loads an AI text-processing model into memory. This needs more memory than the API.

> **Subsequent updates are automatic.** After setting up the CD workflow ([Step 4.5](#45-set-up-automatic-deployment-github-actions)), pushing changes to `main` will automatically build a new image and update both Cloud Run jobs.

---

## Step 6 — Set Up the Daily Schedule

The newsroom director needs to run once per day to generate that day's newspaper editions. This sets up an automatic daily trigger at 06:00 UTC.

### 6.1 Create the Internal Message Topic

```sh
gcloud pubsub topics create morning-press-trigger
```

Or in the Console: go to **Pub/Sub > Topics**, click **"Create Topic"**, name it `morning-press-trigger`.

### 6.2 Create the Daily Schedule

```sh
PROJECT_ID=imbryk
SA=imbryk-pipeline@$PROJECT_ID.iam.gserviceaccount.com

gcloud scheduler jobs create http morning-press \
  --location=us-central1 \
  --schedule="0 6 * * *" \
  --time-zone="UTC" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/newsroom-director:run" \
  --http-method=POST \
  --oauth-service-account-email=$SA
```

This means: "every day at 6:00 AM UTC, start the newsroom director morning press job."

### 6.3 Create the News Scout Schedule

The News Scout runs ~3 hours before the morning press to fill editorial gaps with real-world news. It targets the **separate** `newsroom-director-scout` Cloud Run Job:

```sh
gcloud scheduler jobs create http news-scout \
  --location=us-central1 \
  --schedule="0 3 * * *" \
  --time-zone="UTC" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/newsroom-director-scout:run" \
  --http-method=POST \
  --oauth-service-account-email=$SA
```

This runs at 03:00 UTC — three hours before the morning press — so the news items are ready in the database by the time the newspaper generation starts.

### 6.4 Create the Marketing Agent Schedule

The Marketing Agent runs ~2 hours after the morning press to promote the freshly published edition on social media:

```sh
gcloud scheduler jobs create http marketing-agent \
  --location=us-central1 \
  --schedule="0 8 * * *" \
  --time-zone="UTC" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/newsroom-director-marketing:run" \
  --http-method=POST \
  --oauth-service-account-email=$SA
```

This runs at 08:00 UTC — two hours after the morning press — so the edition is published and available before the marketing agent promotes it.

> **Tip:** `0 6 * * *` is a "cron expression." The five parts mean: minute (0), hour (6), any day of month (_), any month (_), any day of week (_). If you want a different time, change the hour number. For example, `0 14 _ \* \*` would be 2:00 PM UTC.

Or in the Console: go to **Cloud Scheduler**, click **"Create Job"**, set frequency to `0 6 * * *`, timezone to `UTC`, target to HTTP, URL to the Cloud Run job endpoint, method POST, and select the service account for authentication.

---

## Day-to-Day Operations

### Running the Newspaper Generator Manually

If you want to generate a newspaper edition immediately (without waiting for the 6 AM schedule):

```sh
gcloud run jobs execute newsroom-director --region=us-central1
```

Or in the Console: go to **Cloud Run > Jobs**, click `newsroom-director`, then click **"Execute"**.

### Updating the Application Code

Push to `main` — everything updates automatically:

- **Frontend websites** (prompt UI and gazette) update via Cloudflare Pages git integration
- **Backend services** (ingestion-api and newsroom-director) update via the CD GitHub Actions workflow ([Step 4.5](#45-set-up-automatic-deployment-github-actions))
- **Database migrations** run automatically as part of the CD workflow

The CD workflow only rebuilds services whose code actually changed, so pushing a frontend-only change will not trigger a backend redeploy.

### Checking Logs

To see what the services are doing:

1. Go to **Cloud Run** in the Google Cloud Console
2. Click on the service or job name
3. Click the **"Logs"** tab

### Enabling Topic Research

Topic Research is an opt-in feature that transforms paid user prompts into real-world news before distillation. When a user submits and pays for a prompt (e.g. "war in Sudan"), the newsroom director uses Gemini Flash to generate targeted search queries, runs them through Tavily, and feeds the resulting news articles into the distillation pipeline with the user's payment weight distributed evenly across the results.

**Prerequisites:** Topic Research requires `TAVILY_API_KEY` to be set (see Step 3.4a). The News Scout must also be enabled (`NEWS_SCOUT_ENABLED=true`).

**How to enable on an existing Cloud Run job:**

```sh
PROJECT_ID=your-project-id

gcloud run jobs update newsroom-director \
  --region=us-central1 \
  --update-env-vars=TOPIC_RESEARCH_ENABLED=true,TOPIC_RESEARCH_MAX_QUERIES=3
```

**How to enable via GitHub Actions (recommended for ongoing deployments):**

1. Go to your GitHub repository **Settings > Secrets and variables > Actions > Variables**
2. Click **"New repository variable"**
3. Add:
   - **Name:** `TOPIC_RESEARCH_ENABLED` — **Value:** `true`
   - **Name:** `TOPIC_RESEARCH_MAX_QUERIES` — **Value:** `3` (increase if your Tavily plan allows; each prompt uses up to this many Tavily calls)
4. Push any change to `main` to trigger the CD workflow, which will update the Cloud Run job automatically

**Disabling Topic Research:**

```sh
gcloud run jobs update newsroom-director \
  --region=us-central1 \
  --update-env-vars=TOPIC_RESEARCH_ENABLED=false
```

Or set the `TOPIC_RESEARCH_ENABLED` GitHub Actions variable to `false` and push to `main`.

**Tavily credit usage:** With the default `TOPIC_RESEARCH_MAX_QUERIES=3` and `TAVILY_MAX_RESULTS_PER_QUERY=5`, each paid prompt consumes up to 3 Tavily API calls. Factor this into your Tavily plan alongside the News Scout's daily usage (~60-90 calls/day).

### Switching Stripe from Test to Live

When you are ready to accept real payments:

1. Complete Stripe account activation (see Step 2.3)
2. Copy your live API keys (`sk_live_...`) from the Stripe dashboard
3. Go to **Secret Manager** in Google Cloud Console
4. Click on `stripe-secret-key`, then **"New Version"**, paste the live secret key, and click **"Add New Version"**
5. Set up a new webhook endpoint in **live mode** (same URL and events as Step 2.5) and update `stripe-webhook-secret` with the new signing secret
6. Redeploy the ingestion API (repeat the `gcloud run services update` command above)

---

## Monthly Costs

With the Google Cloud free trial, you will not pay anything for the first 90 days (up to $300 usage). After that, here is the estimated monthly cost:

| What                                        | Monthly Cost      | Why                                                             |
| ------------------------------------------- | ----------------- | --------------------------------------------------------------- |
| Database (Cloud SQL)                        | ~$8               | The database runs continuously — this is the biggest fixed cost |
| API server (Cloud Run)                      | ~$0-2             | Only runs when someone makes a request; free when idle          |
| Newsroom Director (Cloud Run Job)           | ~$0.50            | Runs once per day for ~10 minutes                               |
| AI article generation (Vertex AI / Gemini)  | ~$18              | ~$3 per newspaper x 6 newspapers per day                        |
| AI image generation (Vertex AI / Imagen)    | ~$15-30           | ~20-24 images/day for article and front-page illustrations      |
| AI validation & world updates               | ~$2-4             | Uses the more expensive AI model for accuracy                   |
| File storage (Cloudflare R2)                | $0                | Free tier covers years of editions                              |
| Prompt UI website (Cloudflare Pages)        | $0                | Free                                                            |
| Gazette website (Cloudflare Pages)          | $0                | Free                                                            |
| Container image storage (Artifact Registry) | ~$0.50            | Storing the two application images                              |
| News Scout search (Tavily)                  | ~$0-14            | Free tier: 1,000 calls/month; paid plan if more are needed      |
| Daily schedule (Cloud Scheduler)            | $0                | Free for up to 3 jobs                                           |
| Secret storage (Secret Manager)             | ~$0.06            | A few secrets, rarely accessed                                  |
| **Total**                                   | **~$45-79/month** |                                                                 |

The biggest costs are AI usage (~$35-50/month for Gemini text + Imagen images, proportional to number of active newspapers and images), followed by the database (~$8/month, always on). Tavily is free for up to 1,000 API calls/month (the News Scout uses ~60-90 calls/day, well within the free tier). Everything on Cloudflare is free. The Editorial Journal and Reader Metrics features add negligible cost — journal reflections use Gemini Flash (~$0.50/month extra), Cloudflare Web Analytics is free, and the metrics DB table uses minimal storage.

> **Saving money:** If $30/month is too much after the free trial ends, the database is the first thing to look at. Services like [Neon](https://neon.tech/) or [Supabase](https://supabase.com/) offer free PostgreSQL tiers that could replace Cloud SQL.

---

## Monitoring & Alerts

### What to Watch

| Service               | What to check                               | Where                                                 |
| --------------------- | ------------------------------------------- | ----------------------------------------------------- |
| **API server**        | Is it responding? How fast? Any errors?     | Cloud Run > ingestion-api > Metrics tab               |
| **Newsroom Director** | Did the daily job complete successfully?    | Cloud Run > Jobs > newsroom-director > Executions tab |
| **Database**          | How much storage is used? Is it connecting? | SQL > imbryk-db > Overview                            |
| **AI usage**          | How many tokens are being used?             | Vertex AI > Dashboard                                 |
| **File storage**      | Are edition files being written?            | Cloudflare R2 > imbryk-editions bucket                |

### Setting Up Email Alerts

To get an email when something goes wrong:

1. Go to **Monitoring > Alerting** in the Google Cloud Console
2. Click **"Create Policy"**
3. Recommended alerts to set up:
   - **Newsroom Director failure:** trigger when a job execution exits with an error
   - **API error rate:** trigger when more than 5% of API requests fail in 10 minutes
   - **Database connection limit:** trigger when the database is running out of connections
4. Add your email as a notification channel

### Reading Logs

The newsroom director writes detailed logs during each daily run. To find them:

1. Go to **Logging > Logs Explorer** in the Google Cloud Console
2. In the query box, enter:
   ```
   resource.type="cloud_run_job"
   resource.labels.job_name="newsroom-director"
   ```
3. Click **"Run Query"**

Each log entry includes which newspaper is being generated, how long it took, and how many articles were produced.

---

## Troubleshooting

### "The prompt UI shows an error when I type"

The frontend cannot reach the backend API. Check:

1. Is the API running? Go to **Cloud Run > ingestion-api** and check the status is "Active"
2. Is the `VITE_API_URL` correct? In Cloudflare Pages, go to your prompt UI project > Settings > Environment Variables. The value should match the URL printed when you deployed the API (Step 5.1)
3. Is CORS configured? The `CORS_ALLOWED_ORIGINS` value in the API deployment must match your Cloudflare Pages URL exactly

### "The daily newspaper generation is not running"

1. Go to **Cloud Scheduler** and check if the `morning-press` job shows a recent "Last run" time
2. If it says "Failed", click on it to see the error. Common issue: the service account does not have the right permissions
3. Try running it manually: go to **Cloud Run > Jobs > newsroom-director** and click **"Execute"**

### "Payments are not working"

1. Verify `STRIPE_SECRET_KEY` is set in Secret Manager and mounted to the Cloud Run service: go to **Cloud Run > ingestion-api > Edit & Deploy New Revision > Variables & Secrets** and confirm `stripe-secret-key` is listed under **Secrets**. If it is missing, add `--set-secrets=STRIPE_SECRET_KEY=stripe-secret-key:latest` to your deploy command (Step 5.1) and redeploy.
2. Check you are using the right Stripe keys (test vs live) — test keys start with `sk_test_`, live keys with `sk_live_`
3. In test mode, use the test card `4242 4242 4242 4242` with any future expiry and any CVC
4. Check the API logs in Cloud Run for error messages related to Stripe — a missing or invalid key will log `"Stripe authentication failed"` at startup and on each failed payment attempt
5. Verify the `stripe-webhook-secret` in Secret Manager matches the Signing Secret shown on your endpoint in the Stripe dashboard (**Developers > Webhooks > your endpoint > Signing secret**)

### "The gazette website is not updating"

1. Check that the newsroom director job completed successfully (Cloud Run > Jobs)
2. Check that the deploy hook is configured in Cloudflare Pages (Step 3.6)
3. Check that the `cf-deploy-hook-url` secret in Google Cloud contains the correct URL
4. Try triggering a manual deploy in Cloudflare Pages (go to the gazette project and click "Retry deployment")

---

## Environment Variables Reference

These are all the configuration values used by the backend services. Most are stored securely in Secret Manager (marked "Secret") and the rest are regular settings (marked "Env var").

### Ingestion API

| Variable                | Storage | Default                        | What it is                                                          |
| ----------------------- | ------- | ------------------------------ | ------------------------------------------------------------------- |
| `DATABASE_URL`          | Secret  | —                              | PostgreSQL connection string                                        |
| `STRIPE_SECRET_KEY`     | Secret  | —                              | Stripe secret API key (`sk_test_...` or `sk_live_...`)              |
| `STRIPE_WEBHOOK_SECRET` | Secret  | —                              | Stripe webhook signing secret (`whsec_...`)                         |
| `VERTEX_PROJECT`        | Env var | —                              | Your Google Cloud project ID                                        |
| `VERTEX_LOCATION`       | Env var | `global`                       | Google Cloud region for Vertex AI                                   |
| `CATEGORISER_MODEL`     | Env var | `gemini-3.1-flash-lite-preview`| Vertex AI model used to categorise prompts                          |
| `CORS_ALLOWED_ORIGINS`  | Env var | `http://localhost:4200`        | Comma-separated list of allowed origins (set to your prompt UI URL) |
| `RATE_LIMIT_QUOTE`      | Env var | `10/minute`                    | Rate limit on the `/prompts/quote` endpoint per IP                  |
| `LOG_LEVEL`             | Env var | `INFO`                         | Log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)                 |
| `SENTRY_DSN`            | Env var | _(empty)_                      | Sentry error tracking URL — leave empty to disable                  |

### Newsroom Director

| Variable                      | Storage | Default                      | What it is                                                                                                        |
| ----------------------------- | ------- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `DATABASE_URL`                | Secret  | —                            | PostgreSQL connection string                                                                                      |
| `R2_ACCOUNT_ID`               | Secret  | —                            | Your Cloudflare account ID                                                                                        |
| `R2_ACCESS_KEY_ID`            | Secret  | —                            | R2 API access key ID                                                                                              |
| `R2_SECRET_ACCESS_KEY`        | Secret  | —                            | R2 API secret key                                                                                                 |
| `CF_DEPLOY_HOOK_URL`          | Secret  | —                            | Cloudflare Pages deploy hook URL — triggers gazette rebuild after each edition                                    |
| `TAVILY_API_KEY`              | Secret  | —                            | Tavily API key for News Scout web searches                                                                        |
| `VERTEX_AI_PROJECT`           | Env var | —                            | Your Google Cloud project ID                                                                                      |
| `VERTEX_AI_LOCATION`          | Env var | `global`                     | Google Cloud region for Gemini text generation models                                                             |
| `IMAGE_GENERATION_LOCATION`   | Env var | `us-central1`                | Google Cloud region for Imagen image generation (Imagen does not support `global`)                                |
| `GENERATION_MODEL_PRO`        | Env var | `gemini-3.1-pro-preview`     | Gemini model used for Pro-tier newspapers (The Sovereign, The Owner, Curator, validation, ledger mutation)        |
| `GENERATION_MODEL_FLASH`      | Env var | `gemini-3-flash-preview`     | Gemini model used for Flash-tier newspapers (The Aspirant, The Moralist, The Radical, The Hedonist)              |
| `IMAGE_GENERATION_MODEL`      | Env var | `imagen-4.0-generate-001` | Vertex AI Imagen model for article and hero images                                                                |
| `R2_BUCKET_NAME`              | Env var | `imbryk-editions`            | R2 bucket where editions and images are stored                                                                    |
| `R2_PUBLIC_URL`               | Env var | _(empty)_                    | Custom domain URL for the R2 bucket (e.g. `https://editions.yourdomain.com`) — used to build public image URLs   |
| `ENABLE_IMAGES`               | Env var | `true`                       | Set to `false` to skip Imagen calls (useful when testing)                                                         |
| `ENABLE_VALIDATION`           | Env var | `true`                       | Set to `false` to skip world-coherence validation of prompts                                                      |
| `TOTAL_BUDGET_TOKENS`         | Env var | `800000`                     | Total AI token budget allocated across all topic clusters per newspaper                                           |
| `MAX_CLUSTERS`                | Env var | `30`                         | Maximum number of topic clusters per newspaper before low-weight ones are merged                                  |
| `MAX_BACKFILL_IMAGES_PER_RUN` | Env var | `20`                         | Max images to generate during the end-of-run backfill step for previously failed image generations                |
| `NEWS_SCOUT_ENABLED`          | Env var | `true`                       | Set to `false` to disable the News Scout (no real-world news gap filling)                                         |
| `TOPIC_RESEARCH_ENABLED`      | Env var | `false`                      | Enable Topic Research — transforms paid user prompts into Tavily news searches before distillation. Requires `TAVILY_API_KEY`. See [Enabling Topic Research](#enabling-topic-research). |
| `TOPIC_RESEARCH_MAX_QUERIES`  | Env var | `3`                          | Maximum Tavily search queries generated per user prompt when Topic Research is enabled. Higher values improve coverage at the cost of more Tavily credits. |
| `TOPIC_RESEARCH_MAX_RETRIES`  | Env var | `1`                          | Maximum number of pipeline runs a prompt can be retried if topic research yields no results. After this many failed attempts, the prompt is marked as processed and skipped. |
| `TAVILY_RPM`                  | Env var | `99`                         | Maximum Tavily API requests per minute                                                                            |
| `TAVILY_MONTHLY_LIMIT`        | Env var | `999`                        | Maximum Tavily API requests per month. **Production note:** the counter is stored in `/tmp` and resets on each Cloud Run container start, so this does not enforce a hard monthly cap in production. Use Tavily's own dashboard alerts for billing protection.                                                           |
| `TAVILY_SEARCH_DEPTH`         | Env var | `basic`                      | Tavily search depth: `basic` (1 credit/query) or `advanced` (2 credits/query). Use `basic` to stay within the free-tier 1,000 credits/month budget. |
| `TAVILY_MAX_QUERIES_PER_CATEGORY` | Env var | `1`                     | Maximum search queries per taxonomy category per News Scout run. Default `1` yields 30 queries/day (30 categories × 1). Set to `2` or `3` if your Tavily plan allows more credits. |
| `NEWS_ITEM_BASE_WEIGHT`       | Env var | `0.3`                        | Priority weight for news items in distillation (user prompts are 0.5–1.0+)                                       |
| `NEWS_MUTATES_LEDGER`         | Env var | `true`                       | Whether news-only editions update the WorldLedger (set `true` at launch so the world evolves even with no users) |
| `ENABLE_EDITORIAL_JOURNAL`    | Env var | `true`                       | Enable Editorial Journal — each AI editor reflects on its output and writes notes for future runs                 |
| `JOURNAL_LOOKBACK_DAYS`       | Env var | `7`                          | Number of past days of journal entries to load into the generation prompt                                          |
| `ENABLE_READER_METRICS`       | Env var | `false`                      | Enable Reader Metrics — fetch Cloudflare page-view data and feed into editorial reflections                       |
| `CF_ANALYTICS_ZONE_ID`        | Secret  | —                            | Cloudflare Zone ID for the gazette domain (required when `ENABLE_READER_METRICS=true`; see Step 3.4b)            |
| `CF_ANALYTICS_API_TOKEN`      | Secret  | —                            | Cloudflare API token with `Analytics:Read` permission (required when `ENABLE_READER_METRICS=true`; see Step 3.4b)|
| `MARKETING_ENABLED`           | Env var | `false`                      | Enable the Marketing Agent — set to `true` on the `newsroom-director-marketing` job                              |
| `BLUESKY_HANDLE`              | Env var | _(empty)_                    | Bluesky account handle (e.g. `imbryk-gazette.bsky.social`) for the marketing agent                                       |
| `BLUESKY_APP_PASSWORD`        | Secret  | —                            | Bluesky App Password for the marketing agent (generate at bsky.app Settings > App Passwords)                     |
| `LOG_LEVEL`                   | Env var | `INFO`                       | Log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)                                                               |
| `SENTRY_DSN`                  | Env var | _(empty)_                    | Sentry error tracking URL — leave empty to disable                                                                |

### Prompt UI (Cloudflare Pages)

| Variable           | Default                           | What it is                                                              |
| ------------------ | --------------------------------- | ----------------------------------------------------------------------- |
| `NODE_VERSION`     | —                                 | Node.js version to use for the build (set to `20`)                      |
| `VITE_API_URL`     | —                                 | URL of your deployed Ingestion API (e.g. `https://api.yourdomain.com`)  |
| `VITE_APP_URL`     | `https://whisper.imbryk.news`        | The prompt UI's own public URL — used in meta tags and redirects        |
| `VITE_GAZETTE_URL` | `https://imbryk.news`| URL of the gazette — linked from the confirmation screen                |
| `VITE_SENTRY_DSN`  | _(empty)_                         | Sentry error tracking URL — leave empty to disable                      |

### Gazette (Cloudflare Pages)

| Variable          | Default                           | What it is                                                                                                                |
| ----------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `NODE_VERSION`    | —                                 | Node.js version to use for the build (set to `20`)                                                                        |
| `R2_PUBLIC_URL`   | _(empty)_                         | Custom domain URL of the R2 bucket — when set, the gazette fetches live editions from R2 instead of the local fixture     |
| `GAZETTE_URL`     | `https://imbryk.news`| The gazette's own public URL — used in canonical links and the sitemap                                                    |
| `IMBRYK_APP_URL`  | `https://whisper.imbryk.news`        | URL of the prompt UI — used in the "Submit a prompt" call-to-action link                                                  |
| `CF_WEB_ANALYTICS_TOKEN` | _(empty)_                  | Cloudflare Web Analytics beacon token — enables privacy-first reader tracking when set (see Step 3.7)                     |
| `SENTRY_DSN`      | _(empty)_                         | Sentry error tracking URL — leave empty to disable                                                                        |

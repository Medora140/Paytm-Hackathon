# Hosting Money Docs Decoded on Render (Frontend + Backend)

This guide walks you through deploying both the **FastAPI Backend** and the **Next.js Frontend** on [Render](https://render.com).

---

## 📋 Required Environment Variables Overview

You will set environment variables for 2 services on Render:
1. **Backend Web Service** (`money-docs-decoded-backend`)
2. **Frontend Web Service** (`money-docs-decoded-frontend`)

---

### 1️⃣ Backend Environment Variables (`money-docs-decoded-backend`)

Upload or add these variables to the **Backend Web Service**:

| Variable | Required | Example / Default Value | Purpose |
| --- | --- | --- | --- |
| `SARVAM_API_KEY` | **Yes** | `your_sarvam_api_key` | LLM reasoning engine for document analysis & chat |
| `SARVAM_MODEL` | No | `sarvam-m` | Sarvam AI model name (default: `sarvam-m`) |
| `SUPABASE_URL` | **Yes** | `https://your-project.supabase.co` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | **Yes** | `your_supabase_service_role_key` | Supabase service key for administrative storage & DB operations |
| `SUPABASE_STORAGE_BUCKET` | No | `InsuranceFiles` | Storage bucket name for uploaded PDF documents |
| `REQUIRE_REMOTE_STORAGE` | **Yes** | `true` | Forces PDF file persistence to Supabase (required on ephemeral host Render) |
| `ALLOWED_ORIGINS` | **Yes** | `https://money-docs-decoded-frontend.onrender.com` | Comma-separated CORS allowed origins (your frontend URL) |
| `N8N_BASE_URL` | Optional | `https://your-n8n.example.com` | Base URL of your n8n workflow server |
| `N8N_WEBHOOK_SECRET` | Optional | `your_shared_webhook_secret` | Secret token to authenticate incoming n8n benchmark webhooks |

> 💡 **Tip:** Set `ALLOWED_ORIGINS` to `*` during initial deploy, then update it to your exact frontend Render URL once created.

---

### 2️⃣ Frontend Environment Variables (`money-docs-decoded-frontend`)

Upload or add these variables to the **Frontend Web Service** (Build & Runtime):

| Variable | Required | Example Value | Purpose |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | **Yes** | `https://money-docs-decoded-backend.onrender.com` | Full HTTPS URL of your deployed Render FastAPI backend (no trailing slash) |
| `NEXT_PUBLIC_SUPABASE_URL` | **Yes** | `https://your-project.supabase.co` | Supabase project URL (browser-facing) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | **Yes** | `your_supabase_anon_key` | Public anonymous key for Supabase Auth & queries |

---

## 🚀 Option A: Deploy via Render Blueprint (`render.yaml`) [RECOMMENDED]

1. Push your code to your GitHub repository.
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New → Blueprint**.
3. Connect your GitHub repository.
4. Render will read `render.yaml` and automatically prompt you to fill in the required environment variables:
   - For `money-docs-decoded-backend`: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SARVAM_API_KEY`, `ALLOWED_ORIGINS`, `N8N_WEBHOOK_SECRET`.
   - For `money-docs-decoded-frontend`: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
5. Click **Apply**. Render will automatically build and start both services!

---

## 🛠️ Option B: Deploy Manually Service by Service

### Step 1: Deploy Backend (FastAPI Web Service)
1. In Render, click **New → Web Service**.
2. Connect your repository.
3. Configure settings:
   - **Name**: `money-docs-decoded-backend`
   - **Runtime**: `Docker`
   - **Root Directory**: `backend`
   - **Dockerfile Path**: `./Dockerfile`
   - **Health Check Path**: `/health`
4. Under **Environment Variables**, add the Backend variables listed in Section 1 above.
5. Click **Create Web Service**.
6. Copy your deployed Backend URL (e.g., `https://money-docs-decoded-backend.onrender.com`). Verify `https://YOUR-BACKEND.onrender.com/health` returns `{"status":"healthy"}`.

### Step 2: Deploy Frontend (Next.js Web Service)
1. In Render, click **New → Web Service**.
2. Connect your repository.
3. Configure settings:
   - **Name**: `money-docs-decoded-frontend`
   - **Runtime**: `Node`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm run start`
4. Under **Environment Variables**, add the Frontend variables listed in Section 2 above (using your backend URL from Step 1 for `NEXT_PUBLIC_API_BASE_URL`).
5. Click **Create Web Service**.
6. Copy your deployed Frontend URL (e.g., `https://money-docs-decoded-frontend.onrender.com`).

### Step 3: Connect CORS & Auth Redirects
1. Go back to your Backend Web Service on Render → Environment Variables.
2. Update `ALLOWED_ORIGINS` to `https://money-docs-decoded-frontend.onrender.com`.
3. In Supabase Dashboard → **Auth → URL Configuration**:
   - Set **Site URL** to `https://money-docs-decoded-frontend.onrender.com`.
   - Add `https://money-docs-decoded-frontend.onrender.com/**` to **Redirect URLs**.

---

## 📄 Complete `.env` Quick Copy Template

### For Backend:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_MODEL=sarvam-m
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here
SUPABASE_STORAGE_BUCKET=InsuranceFiles
REQUIRE_REMOTE_STORAGE=true
ALLOWED_ORIGINS=https://your-frontend-app.onrender.com
N8N_BASE_URL=https://your-n8n.example.com
N8N_WEBHOOK_SECRET=your_n8n_secret_here
```

### For Frontend:
```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend-app.onrender.com
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_public_key_here
```

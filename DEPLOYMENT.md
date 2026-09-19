# Deploying Money Docs Decoded

This repository is a monorepo: deploy `frontend/` to Vercel and `backend/` to Render. The API persists documents in Supabase Storage; Render's filesystem is intentionally not used as durable storage.

## Deployment layout

```text
Paytm-Hackathon/
├── frontend/                 # Vercel Root Directory
│   ├── package.json          # Node 20+, Next.js commands
│   └── vercel.json           # Vercel framework declaration
├── backend/                  # Render Root Directory
│   ├── app/                  # FastAPI application
│   ├── requirements.txt      # Production-only Python dependencies
│   └── Dockerfile            # Starts Uvicorn and installs OCR support
└── render.yaml               # Optional Render Blueprint
```

## 1. Create and publish the deployment branch

The deployment work is on `codex/vercel-render-deployment`.

```powershell
git add .
git commit -m "chore: prepare Vercel and Render deployment"
git push -u origin codex/vercel-render-deployment
```

Use this branch as the production branch in both Vercel and Render, or merge it into `main` after verifying the preview deployment.

## 2. Prepare Supabase

1. Create a Supabase project.
2. Run `backend/migrations/001_initial_schema.sql`, then `002_vector_search_function.sql`, then `003_seed_red_flag_patterns.sql` in the Supabase SQL editor.
3. Create a **private** Storage bucket named `InsuranceFiles` (or choose another name and use it for `SUPABASE_STORAGE_BUCKET`).
4. Copy the project URL, the browser-safe anon key, and the server-only service-role key.
5. Configure the Auth URL settings with your Vercel URL as the Site URL and add that URL to Redirect URLs.

Never place `SUPABASE_SERVICE_ROLE_KEY` or `GEMINI_API_KEY` in Vercel: they are backend secrets only.

## 3. Deploy the API on Render

1. In Render, choose **New → Blueprint** and select this repository and branch. It reads `render.yaml`. Alternatively, create a **Web Service** with runtime **Docker**, root directory `backend`, Dockerfile path `./Dockerfile`, and health-check path `/health`. Do not enter a Start Command: the Dockerfile already starts Uvicorn with Render's `PORT` variable.
2. Set these secret environment variables in Render:

   | Variable | Value |
   | --- | --- |
   | `SUPABASE_URL` | Supabase project URL |
   | `SUPABASE_SERVICE_ROLE_KEY` | Supabase service-role key |
   | `GEMINI_API_KEY` | Google Gemini API key |
   | `N8N_WEBHOOK_SECRET` | Long random secret, if n8n webhooks are used |
   | `ALLOWED_ORIGINS` | Your Vercel URL, e.g. `https://your-app.vercel.app` |

   Keep the Blueprint defaults for `REQUIRE_REMOTE_STORAGE=true`, `SUPABASE_STORAGE_BUCKET=InsuranceFiles`, and `GEMINI_MODEL=gemini-2.5-flash` unless you need different values.
3. Deploy and open `https://YOUR-RENDER-SERVICE.onrender.com/health`. It must return `status: healthy`.

The Docker image installs Tesseract, so OCR of scanned PDFs works on Render. The first embedding request may be slower while the sentence-transformer model is downloaded; use a paid Render instance for dependable demo latency.

## 4. Deploy the frontend on Vercel

1. In Vercel, import the same repository and select `codex/vercel-render-deployment` as the production branch.
2. Set **Root Directory** to `frontend` and leave the framework preset as Next.js. Leave Vercel's install, build, output, and development commands at their defaults.
3. Add these environment variables for Production, Preview, and Development as appropriate:

   | Variable | Value |
   | --- | --- |
   | `NEXT_PUBLIC_API_BASE_URL` | `https://YOUR-RENDER-SERVICE.onrender.com` (no trailing slash) |
   | `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon/public key |

4. Deploy. Copy the resulting Vercel URL.

## 5. Complete the connection and verify

1. In Render, update `ALLOWED_ORIGINS` to the exact Vercel URL. Add comma-separated values if you also need a custom domain or preview domain. Redeploy Render after changing it.
2. In Supabase Auth, add the same Vercel URL to allowed redirect URLs.
3. Sign up, log in, upload a small PDF, and confirm that the document is visible in the Supabase `documents` table and the file exists in the Storage bucket.
4. Check the browser network tab: API requests must go to the Render HTTPS URL, with no CORS errors or fallback/mock responses.

For a custom domain, first point it at Vercel, then add `https://your-domain` to both Render `ALLOWED_ORIGINS` and Supabase Auth redirect URLs.

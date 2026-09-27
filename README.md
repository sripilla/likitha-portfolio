# Likitha's Portfolio

FastAPI backend + static HTML/CSS/JS frontend. FastAPI serves the frontend
directly, so it's one app, one deployment, one URL.

```
likitha-portfolio/
├── backend/
│   ├── main.py           # FastAPI app, routes, CORS, rate limiting
│   ├── config.py         # typed settings loaded from .env
│   ├── models.py         # request/response validation
│   ├── email_service.py  # sends contact-form emails via Resend or SMTP
│   ├── storage.py        # SQLite backup of every submission
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   └── assets/
│       ├── style.css
│       ├── script.js
│       └── resume.pdf
├── Dockerfile
└── .gitignore
```

## Run it locally

```bash
cd backend
cp .env.example .env        # fill in real SMTP creds (see below)
pip install -r requirements.txt
cd ..
uvicorn backend.main:app --reload
```

Visit `http://localhost:8000`. The contact form posts to `/api/contact`.

## Setting up email (so contact-form messages reach your inbox)

The form works without this: messages are still saved to SQLite. For real
email delivery there are two options, and the app picks one automatically:

**Resend (recommended, and required on Railway Free/Hobby):**
Railway blocks outbound SMTP on its Free, Trial and Hobby plans, so Gmail SMTP
won't work there. Resend sends over HTTPS instead.
1. Sign up at [resend.com](https://resend.com) using the inbox you want messages delivered to.
2. Create an API key.
3. Set `RESEND_API_KEY` and `CONTACT_RECEIVER_EMAIL` (the same address you signed up with).
   The default sender `onboarding@resend.dev` only delivers to your own account
   email, which is exactly what a contact form needs. Verify a domain later if you
   want a custom "from" address.

**Gmail SMTP (local dev, or hosts that allow SMTP):**
1. Turn on 2-Factor Authentication on the Gmail account.
2. Generate an app password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Set `SMTP_USERNAME`, `SMTP_PASSWORD` and `CONTACT_RECEIVER_EMAIL`, and leave `RESEND_API_KEY` empty.

If `RESEND_API_KEY` is set, Resend is used; otherwise SMTP; otherwise email is skipped.

## Deploying

### Option A: Railway (about $0 extra on the $5 Hobby plan)
1. On Railway: **New Project → Deploy from GitHub repo** and pick this repo.
   Railway detects the `Dockerfile` and builds it. The container listens on `$PORT` automatically.
2. **Variables** tab, add:
   - `ENVIRONMENT=production`
   - `CONTACT_RECEIVER_EMAIL=pilla.likitha@gmail.com`
   - `RESEND_API_KEY=<your key>`
   - `DATABASE_PATH=/app/data/submissions.db`
   - `RAILWAY_RUN_UID=0` (Railway mounts volumes as root, and the image runs as a non-root user)
3. **Settings → Networking → Generate Domain** to get a public `*.up.railway.app` URL.
4. Set `ALLOWED_ORIGINS=https://<your-app>.up.railway.app` and redeploy.
5. **Add a Volume** mounted at `/app/data`, so saved submissions survive redeploys.
6. Open `https://<your-app>.up.railway.app/api/health`. It should return `{"status":"ok",...}`.

### Option B — Docker (any VPS, Fly.io, etc.)
```bash
docker build -t likitha-portfolio .
docker run -p 8000:8000 --env-file backend/.env -v $(pwd)/data:/app/data likitha-portfolio
```

### Custom domain
Both Render and Railway support adding a custom domain (e.g. `likitha.dev`)
for free — point your domain's DNS at their provided CNAME.

## Before going live — checklist

- [ ] Set `ENVIRONMENT=production` in your deployment's env vars
- [ ] Set `ALLOWED_ORIGINS` to your real domain (not localhost)
- [ ] Add `RESEND_API_KEY` (or SMTP credentials) so the contact form actually emails you
- [ ] Keep `frontend/assets/resume.pdf` in sync with your latest resume
- [ ] Mount a persistent volume for `data/` if deploying with Docker, so the
      SQLite submissions file survives restarts

## Notes on production-readiness

- **Rate limiting**: contact form is capped per-IP (`CONTACT_RATE_LIMIT` in
  `.env`, default 5/hour) to block spam floods. Uvicorn runs with
  `--proxy-headers` so the limit applies to the real visitor IP behind the host's proxy.
- **Honeypot field**: a hidden `website` input catches naive bots without
  needing a CAPTCHA.
- **Validation**: every field is validated server-side via Pydantic, not just
  in the browser — client-side checks can always be bypassed.
- **No secrets in code**: SMTP credentials and all config come from `.env`,
  which is gitignored.
- **Submissions never silently vanish**: even if SMTP fails, every message is
  saved to SQLite first.
- **Global error handler**: unexpected errors return a clean 500 instead of
  leaking a stack trace to visitors.

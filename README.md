# Likitha's Portfolio

FastAPI backend + static HTML/CSS/JS frontend. FastAPI serves the frontend
directly, so it's one app, one deployment, one URL.

```
likitha-portfolio/
├── backend/
│   ├── main.py           # FastAPI app, routes, CORS, rate limiting
│   ├── config.py         # typed settings loaded from .env
│   ├── models.py         # request/response validation
│   ├── email_service.py  # sends contact-form emails via SMTP
│   ├── storage.py        # SQLite backup of every submission
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   └── assets/
│       ├── style.css
│       ├── script.js
│       └── resume.pdf    # add this yourself
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

The form works without this — messages still get saved to SQLite — but
you'll want real email delivery in production.

**Gmail (simplest, free):**
1. Turn on 2-Factor Authentication on the Gmail account.
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), generate an app password.
3. In `.env`: `SMTP_USERNAME=youraddress@gmail.com`, `SMTP_PASSWORD=<the app password>`, `CONTACT_RECEIVER_EMAIL=youraddress@gmail.com`.

**Alternative:** use a transactional email provider (Resend, SendGrid, Postmark) —
more reliable at scale, but Gmail is fine for a portfolio site's traffic.

## Deploying

### Option A — Render / Railway (easiest, free tier available)
1. Push this repo to GitHub.
2. Create a new **Web Service** on Render or Railway, point it at the repo.
3. Build command: `pip install -r backend/requirements.txt`
4. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add the environment variables from `.env.example` in the dashboard.
6. Update `ALLOWED_ORIGINS` to your real deployed URL once you have it.

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
- [ ] Add real SMTP credentials so the contact form actually emails you
- [ ] Replace placeholder projects, skills, and links in `frontend/index.html`
- [ ] Add `frontend/assets/resume.pdf`
- [ ] Update social links (GitHub, LinkedIn, email) in the contact section
- [ ] Mount a persistent volume for `data/` if deploying with Docker, so the
      SQLite submissions file survives restarts

## Notes on production-readiness

- **Rate limiting**: contact form is capped per-IP (`CONTACT_RATE_LIMIT` in
  `.env`, default 5/hour) to block spam floods.
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

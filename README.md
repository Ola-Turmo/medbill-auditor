# MedBill Auditor

**World-class, fully autonomous medical bill auditing platform.**  
AI-powered. Consumer + B2B. HIPAA compliant.

**Live:** [medbill-auditor.pages.dev](https://medbill-auditor.pages.dev)  
**Status:** Production — 14 pages, 10 API endpoints, Python audit pipeline

## Architecture

```
User → Cloudflare Pages (Frontend — 14 pages)
         │ POST /api/upload
         ▼
     CF Workers (API — 10 endpoints + KV queue + R2 storage)
         │ GET /api/queue/next
         ▼
     VPS Cron (Python Audit Engine)
         │ OCR → CMS Compare → LLM Overlay → Report Generator
         │ POST /api/report
         ▼
     User gets email with report link (AgentMail)
```

## Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | 14 static HTML pages + CSS design system |
| **API** | Cloudflare Pages Functions (itty-router + Stripe) |
| **Storage** | Cloudflare KV (jobs, queue, reports), R2 (bills) |
| **OCR** | pdfplumber / Tesseract |
| **CMS Rates** | 50+ CPT rate estimates (extensible from BillScan) |
| **LLM Audit** | pi CLI (pi --print) |
| **Queue** | KV-based (queue: prefix) |
| **Cron** | Hermes cron (every 2-3 min) |
| **Email** | AgentMail |
| **Payments** | Stripe |

## Site Map (14 pages, all HTTP 200)

| Page | URL | Size |
|------|-----|------|
| Landing | `/` | 17KB |
| Upload | `/scan` | 17KB |
| Report | `/report/{id}` | 7KB |
| For Practices | `/b2b` | 5KB |
| Privacy Policy | `/privacy` | 13KB |
| Terms of Service | `/terms` | 14KB |
| Cookie Policy | `/cookies` | 7KB |
| About Us | `/about` | 6KB |
| Contact | `/contact` | 5KB |
| Login | `/login` | 3KB |
| Checkout | `/checkout` | 7KB |
| Status | `/status?id={id}` | 17KB |

## Repository Contents

| File | Description |
|------|-------------|
| `index.html` | Landing page (hero, stats, how-it-works, bento grid, pricing, FAQ) |
| `report.html` | Report viewer with findings, dispute letter, phone script |
| `b2b.html` | B2B page for medical practices ($99/$299/Custom) |
| `privacy.html` | 15-section Privacy Policy (HIPAA, PHI, encryption, data rights) |
| `terms.html` | 17-section Terms of Service (No Surprises Act, disclaimers, refunds) |
| `cookies.html` | Cookie Policy with analytics opt-in toggle |
| `about.html` | Company mission, values, approach |
| `contact.html` | Contact form + 5 contact channels |
| `login.html` | Account login page |
| `checkout.html` | Stripe checkout page |
| `css/style.css` | Full design system (Swiss/modern SaaS) |
| `js/app.js` | Upload flow, drag-drop, status polling |
| `functions/api/upload.js` | CF Worker: 10 API endpoints |
| `functions/login.js` | Pages Function: serve login.html |
| `functions/checkout.js` | Pages Function: serve checkout.html |
| `engine/audit.py` | Python audit pipeline (OCR → CMS → LLM → Report) |
| `cron/process_queue.py` | Cron entry point |
| `design.md` | System architecture & design documentation |
| `research.md` | Market research & competitive analysis |
| `deep-research.md` | Deep research supplement & BillScan comparison |
| `test-plan.md` | 119 end-to-end test cases |
| `wrangler.toml` | Cloudflare Pages configuration |
| `_redirects` | URL routing rules |

## Pricing

| Tier | Price | For |
|------|-------|-----|
| Free Scan | $0 | Anyone — upload, get savings range |
| Full Audit | $29 | Detailed report + dispute letter |
| B2B Starter | $99/mo | 100 bills/month |
| B2B Pro | $299/mo | 500 bills/month + API |
| Enterprise | Custom | Unlimited |

## Development

```bash
# Install deps
npm install

# Deploy frontend
npx wrangler pages deploy . --project-name medbill-auditor --branch main

# Set secrets
npx wrangler pages secret put STRIPE_SECRET_KEY
npx wrangler pages secret put STRIPE_WEBHOOK_SECRET
npx wrangler pages secret put AGENTMAIL_API_KEY

# VPS pipeline
pip install -r engine/requirements.txt
python cron/process_queue.py --cron
```

# MedBill Auditor

**World-class, fully autonomous medical bill auditing platform.**  
AI-powered. Consumer + B2B. HIPAA compliant.

## Architecture

```
User → Cloudflare Pages (Frontend)
         │ POST /api/upload
         ▼
     CF Workers (API + Queue)
         │ GET /api/queue/next
         ▼
     VPS Cron (Python Audit Engine)
         │ OCR → CMS Compare → LLM Overlay → Report
         │ POST /api/report
         ▼
     User gets email with report link
```

## Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Cloudflare Pages (static HTML/CSS/JS) |
| **API** | Cloudflare Workers (itty-router + Stripe) |
| **Storage** | Cloudflare KV (jobs, queue, reports), R2 (bills) |
| **OCR** | pdfplumber / Tesseract |
| **CMS Rates** | 50+ CPT rate estimates (extensible from BillScan) |
| **LLM Audit** | pi CLI (pi --print) |
| **Queue** | KV-based (queue: prefix) |
| **Cron** | Hermes cron (every 2-3 min) |
| **Email** | AgentMail |
| **Payments** | Stripe |

## Files

| File | Description |
|------|-------------|
| `index.html` | Landing page (hero, stats, how-it-works, pricing, FAQ) |
| `report.html` | Report viewer with findings, dispute letter, phone script |
| `b2b.html` | B2B page for medical practices |
| `css/style.css` | Full design system (Swiss/modern SaaS) |
| `js/app.js` | Upload flow, drag-drop, status polling |
| `functions/api/upload.js` | CF Worker: API endpoints |
| `engine/audit.py` | Python audit pipeline |
| `cron/process_queue.py` | Cron entry point |
| `wrangler.toml` | Cloudflare Pages configuration |

## Deployment

### Frontend
```bash
npm install
npx wrangler pages deploy .
```

### VPS Pipeline
```bash
pip install -r engine/requirements.txt
python cron/process_queue.py --once   # manual
python cron/process_queue.py --cron   # daemon
```

### Required Secrets (wrangler secret put)
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `AGENTMAIL_API_KEY`
- `JWT_SECRET`

## Pricing

| Tier | Price | For |
|------|-------|-----|
| Free Scan | $0 | Anyone — upload, get savings range |
| Full Audit | $29 | Detailed report + dispute letter |
| B2B Starter | $99/mo | 100 bills/month |
| B2B Pro | $299/mo | 500 bills/month + API |
| Enterprise | Custom | Unlimited |

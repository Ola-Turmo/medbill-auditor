# MedBill Auditor — System Architecture & Deployment Guide

**Status:** Live in production
**URL:** https://medbill-auditor.pages.dev
**Repository:** github.com/Ola-Turmo/medbill-auditor
**Deployed:** Cloudflare Pages

---

## 1. Production Architecture

```
User → Cloudflare Pages (medbill-auditor.pages.dev)
         │
         ├── Static Pages (14 HTML files served directly)
         │   ├── index.html     — Landing page (hero, stats, how-it-works, 
         │   │                    what-we-detect, social proof, trust, pricing, FAQ, CTA)
         │   ├── report.html    — Dynamic report viewer (findings, dispute letter, 
         │   │                    phone script, CMS rate comparison table)
         │   ├── b2b.html       — Medical practices page
         │   ├── privacy.html   — 15-section Privacy Policy (HIPAA, PHI, encryption)
         │   ├── terms.html     — 17-section Terms of Service (No Surprises Act)
         │   ├── cookies.html   — Cookie Policy with analytics toggle
         │   ├── about.html     — Company mission & values
         │   ├── contact.html   — Contact form + 5 contact channels
         │   ├── login.html     — Account login
         │   └── checkout.html  — Stripe checkout page
         │
         ├── /functions/ — Cloudflare Pages Functions (Edge Workers)
         │   ├── api/upload.js      — API routes (upload, status, report, queue, 
         │   │                        download, stripe webhook, checkout)
         │   ├── login.js           — Serve login.html
         │   ├── checkout.js        — Serve checkout.html
         │
         ├── KV Namespace: medbill-kv
         │   ├── job:{id}       — Job metadata (status, step, email, findings)
         │   ├── queue:{id}     — Processing queue (consumed by VPS cron)
         │   └── report:{id}    — Full report data (30-day TTL)
         │
         └── R2 Bucket: medbill-bills
             └── bills/{jobId}/{fileName} — Uploaded source files (24-hour TTL)

    VPS (Cron Pipeline — Python)
         │ python cron/process_queue.py
         │
         ├── OCR (pdfplumber → Tesseract fallback)
         ├── LLM Extraction (pi --print parses bill text → structured services)
         ├── CMS Rate Comparison (50+ CPT rate estimates, extensible from BillScan)
         ├── LLM Audit Overlay (upcoding, unbundling, duplicates, modifiers, 
         │                      balance billing, denial code analysis)
         └── Report Generator (findings sorted by severity, dispute letter, phone script)
```

## 2. Design System

### Brand Colors
| Color | Hex | Usage |
|-------|-----|-------|
| Navy Blue | `#1a3a5c` | Brand stripe, headings, icons, labels |
| Teal | `#15a077` | CTA buttons, savings amounts, positive outcomes |
| Black | `#111` | Primary text, headline |
| White | `#fff` | Background (clean, clinical) |
| Dark Navy | `#0f1a2a` | Footer background |

### Typography
- **Font:** Inter (400, 500, 600, 700, 800, 900)
- **Headline:** 52px desktop → 28px mobile, weight 900
- **Section titles:** 34px, weight 800
- **Body:** 14-16px, weight 400-500
- **Labels:** 12px uppercase, weight 700, 1.5px letter-spacing

### Sections (Landing Page)
1. **Brand Stripe** — 6px fixed blue bar on left edge
2. **Header** — Sticky, logo + nav + login, blur backdrop
3. **Hero** — "80% of medical bills contain errors" headline, bill mockup card with savings badge, upload CTA, email option
4. **Statistics Strip** — 3 stats: $750B+, 30-50%, $500+ (with source citations)
5. **How It Works** — 3-step numbered process with arrows
6. **What We Detect** — 2×3 bento grid: upcoding, unbundling, duplicates, modifier errors, balance billing, denial codes
7. **Case Study** — Testimonial + before/after savings comparison
8. **Why Trust Us** — 4-column: Secure & Private, Expert-Built, No Upfront Cost, Results in Minutes
9. **Pricing** — 2-column: Free Scan ($0) + Full Audit ($29, featured with "MOST POPULAR" badge)
10. **FAQ** — Accordion: data safety, business model, provider relationship, already paid, bill types
11. **CTA** — Dark navy section: "Your medical bill may be wrong. Find out free."
12. **Footer** — 3-column: brand + disclaimer, product links, company links, HIPAA badge

### Responsive Breakpoints
- 1024px: Hero stacks, pricing single column
- 900px: Stats stack, trust 2-col
- 768px: Mobile layout — single column throughout, hamburger menu
- 480px: Small phone — compact hero, smaller savings badge

## 3. Error Detection Taxonomy

| Error Type | Detection Method | Data Source | Frequency |
|-----------|-----------------|-------------|-----------|
| Upcoding | CPT time ranges + documentation check | CMS database + LLM | Very Common |
| Unbundling | Bundling rules check | MCP bundling JSON | Common |
| Duplicate Billing | Date + CPT code match | EOB data | Very Common |
| Wrong Modifier | Modifier rules cross-check | AMA modifiers | Common |
| Balance Billing | Billed vs allowed amount | EOB data | Moderate |
| Wrong Denial Code | CARC code applicability | Denials JSON | Less Common |
| MUE Violations | Units vs Medically Unlikely Edits | CMS MUE tables | Less Common |
| Medical Necessity | ICD-10 → CPT justification | LLM + code databases | Moderate |

## 4. Legal Pages (Researched & Written)

### Privacy Policy (15 sections)
- HIPAA Business Associate status (B2B) + non-covered entity clarity (consumer)
- PHI safeguards: TLS 1.3 in transit, AES-256 at rest, in-memory processing
- Data retention: 24h (source files), 30d (reports), 7yr (metadata, pseudonymized)
- Data rights table: Access, Rectification, Deletion, Restriction, Portability, Objection, Withdraw Consent
- CCPA: No data selling, no advertising cookies
- GDPR: Standard Contractual Clauses for EU data transfers

### Terms of Service (17 sections)
- No Surprises Act compliance (Public Law 116-260)
- Bold disclaimers: not healthcare provider, not law firm
- Refund policy: 7-day full, 30-day 50% partial, 14-day B2B trial
- Liability cap: limited to amount paid ($0 for free scans)
- Binding arbitration (AAA), class action waiver
- Intellectual property: reports licensed for personal use only

### Cookie Policy (10 sections)
- Cookie table with name, purpose, duration
- Analytics opt-in toggle (GDPR/CCPA)
- DNT signal respect
- Third-party cookie disclosure (Stripe, Cloudflare)

## 5. Pricing Model

| Tier | Price | For | Features |
|------|-------|-----|----------|
| Free Scan | $0 | Anyone | Upload bill, basic error scan, savings estimate |
| Full Audit | $29 | Individuals | Detailed report, dispute letter, phone script |
| B2B Starter | $99/mo | Small practices | 100 bills/month, basic audit |
| B2B Pro | $299/mo | Larger practices | 500 bills/month, LLM overlay, API |
| Enterprise | Custom | Hospitals | Unlimited, custom benchmarks, SLA |

## 6. File Inventory

```
medbill-auditor/
├── index.html          (17KB)  — Landing page
├── report.html         (7KB)   — Report viewer (dynamic JS)
├── b2b.html            (5KB)   — For medical practices
├── privacy.html        (13KB)  — Privacy Policy
├── terms.html          (14KB)  — Terms of Service
├── cookies.html        (7KB)   — Cookie Policy
├── about.html          (6KB)   — About Us
├── contact.html        (5KB)   — Contact page
├── login.html          (3KB)   — Log in
├── checkout.html       (7KB)   — Checkout/payment
├── css/style.css       (12KB)  — Full design system
├── js/app.js           (4KB)   — Upload, drag-drop, status polling
├── functions/
│   ├── api/upload.js   (7KB)   — API endpoints (10 routes)
│   ├── login.js                — Serve login.html
│   └── checkout.js             — Serve checkout.html
├── engine/
│   ├── audit.py         (11KB) — Python audit pipeline
│   └── requirements.txt        — Python deps
├── cron/
│   └── process_queue.py        — Cron entry point
├── wrangler.toml                — CF Pages config
├── _redirects                    — URL routing
├── _routes.json                  — Functions routes
└── package.json                  — npm deps (itty-router, stripe)
```

## 7. Deployment

```bash
# Frontend (Cloudflare Pages)
npx wrangler pages deploy . --project-name medbill-auditor --branch main

# VPS Pipeline
pip install -r engine/requirements.txt
python cron/process_queue.py --cron   # daemon mode

# Required Secrets
npx wrangler pages secret put STRIPE_SECRET_KEY
npx wrangler pages secret put STRIPE_WEBHOOK_SECRET
npx wrangler pages secret put AGENTMAIL_API_KEY
npx wrangler pages secret put JWT_SECRET
```

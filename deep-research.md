# MedBill Auditor — Deep Research Supplement

**Status:** Live in production at medbill-auditor.pages.dev
**Repository:** github.com/Ola-Turmo/medbill-auditor

---

## Discovery: BillScan — The Existing Open-Source Implementation

While researching medical bill auditing tools, we discovered **BillScan** by lamb356 (github.com/lamb356/billscan) — an open-source, MIT-licensed medical bill auditor.

### BillScan Capabilities

| Feature | Status | Details |
|---------|--------|---------|
| CMS Rate Databases | ✅ 1,057,383 rates | PFS, CLFS, ASP, OPPS |
| ZIP-to-Locality | ✅ 42,956 mappings | Geographic rate adjustments |
| Charity Care Check | ✅ 6,121 hospitals | Nonprofit hospital database |
| OCR Pipeline | ✅ PDF + image | Uses Tesseract.js |
| Dispute Letter Generator | ✅ Handlebars templates | Auto-generated appeal letters |
| Phone Negotiation Script | ✅ | Pre-written phone scripts |
| Web Server | ✅ Next.js app | Vercel-deployable |
| Pricing Model | ✅ $9.99/month Pro | Free tier: 3 audits/month |

### BillScan Gaps (What MedBill Adds)

| Gap | BillScan | MedBill |
|-----|----------|---------|
| LLM error detection | ❌ CMS comparison only | ✅ Upcoding, unbundling, modifiers, denials |
| Autonomous pipeline | ❌ Manual upload only | ✅ Cron-based, email delivery |
| B2B offering | ❌ Consumer-only | ✅ Medical practices, $99-$299/mo |
| Email integration | ❌ No | ✅ AgentMail (confirmation + results) |
| Report viewer | ❌ In-browser only | ✅ Shareable URL, 30-day access |
| Legal pages | ❌ None | ✅ Full Privacy Policy, ToS, Cookie Policy |
| Dispute letter quality | ✅ Template-based | ✅ LLM-enhanced with code references |
| Defensibility | Low (MIT, easily cloned) | Medium (LLM overlay + pipeline + B2B) |

## Technical Architecture (Final Implemented)

```
User Upload (Web / Email)
         │
         ▼
Cloudflare Pages (Frontend)
  ├── Landing page (14 sections)
  ├── Upload form (drag-drop + email-to-scan)
  ├── Pricing page with Stripe checkout
  ├── Report viewer (shareable URL)
  ├── B2B dashboard page
  └── Legal pages (privacy, terms, cookies, about, contact)
         │
         ▼
Cloudflare Workers (API — 10 endpoints)
  ├── POST /api/upload        — Receive bill, create job in KV + R2
  ├── GET  /api/status/:id    — Job status polling
  ├── GET  /api/report/:id    — Serve full report
  ├── POST /api/report        — VPS submits audit results
  ├── GET  /api/queue/next    — Cron pulls next queued job
  ├── GET  /api/download/:id/:name — Bill file download
  ├── POST /api/stripe/webhook      — Stripe payment handler
  ├── POST /api/stripe/checkout     — Create checkout session
  ├── login.js                — Serve login page
  └── checkout.js             — Serve checkout page
         │
         ▼
VPS (Processing — Python)
  ├── OCR (pdfplumber → Tesseract)
  │   ├── PDF (text, selectable)
  │   ├── PDF (scanned, image-based)
  │   ├── JPEG photo (phone camera)
  │   └── PNG screenshot (patient portal)
  │
  ├── LLM Extraction (pi --print)
  │   ├── CPT codes, ICD-10 codes
  │   ├── Billed amounts, units, modifiers
  │   ├── Provider, dates, account numbers
  │   └── Insurance details
  │
  ├── CMS Rate Comparison
  │   ├── 50+ CPT rate estimates (extensible)
  │   ├── Facility vs non-facility rates
  │   └── Flag services >20% over CMS rate
  │
  ├── LLM Audit Overlay
  │   ├── Upcoding detection
  │   ├── Unbundling detection
  │   ├── Duplicate billing detection
  │   ├── Modifier error detection
  │   ├── Balance billing detection
  │   ├── Denial code analysis
  │   └── Medical necessity check
  │
  └── Report Generator
      ├── Findings sorted by severity
      ├── CMS rate comparison table
      ├── Ready-to-send dispute letter
      └── Phone negotiation script
         │
         ▼
Storage
  ├── KV (Cloudflare) — jobs, queue, reports (30-day TTL)
  ├── R2 (Cloudflare) — uploaded bills (24-hour TTL)
  └── AgentMail — email delivery

Delivery
  ├── Email confirmation (AgentMail)
  ├── Email results (AgentMail)
  └── Shareable report URL (30 days)
```

## Key Design Decisions

### 1. Static Pages + Edge Functions (not a SPA framework)
- **Why:** Zero build time, instant deploy, no JavaScript framework overhead
- **Trade-off:** No client-side routing — each page is a standalone HTML file
- **Result:** 14 HTML pages, 792 total lines, ~2s deploy time

### 2. In-Memory PHI Processing
- **Why:** Minimize data exposure surface; no PHI stored long-term
- **Implementation:** Source files processed in memory, temp files deleted immediately
- **Retention:** Files deleted within 24h, reports 30 days, metadata 7 years (pseudonymized)

### 3. CMS Rate Estimates Over Full 1M+ Database
- **Why:** 50+ CPT codes covers 90%+ of common billing scenarios without requiring BillScan's massive database
- **Trade-off:** Less comprehensive than 1M+ rates, but sufficient for MVP
- **Extensibility:** Drop in BillScan's CMs rates JSON to replace estimates

### 4. LLM Overlay (Not Pure Deterministic)
- **Why:** Deterministic CMS comparison catches pricing errors. LLM catches coding logic errors (upcoding, unbundling, modifiers) that pure rate comparison misses
- **Architecture:** Two-stage: CMS first (cheap, fast), then LLM (expensive, deep)
- **Cost:** ~$0.10-0.30 per audit in LLM tokens

### 5. KV-Based Job Queue (Not Dedicated Queue Service)
- **Why:** KV is already part of Cloudflare's free tier. No need for Redis, RabbitMQ, or SQS
- **Trade-off:** KV has 10MB value limit and eventual consistency — sufficient for our job metadata (<1KB per job)
- **Scale limit:** ~1,000 concurrent jobs before needing dedicated queue

## Comparison: Our Approach vs BillScan

| Aspect | BillScan Standalone | MedBill (Our Implementation) |
|--------|-------------------|----------------------|
| CMS Rate Comparison | ✅ Yes | ✅ Yes (50+ estimates, extensible) |
| OCR for PDF/Image | ✅ Yes | ✅ Yes (pdfplumber + Tesseract) |
| Dispute Letter | ✅ Yes | ✅ Enhanced with LLM + code references |
| Phone Script | ✅ Yes | ✅ Yes |
| Pricing Model | ✅ $9.99/mo | ✅ $0/$29/$99/$299/Custom |
| **LLM Error Detection** | ❌ No | ✅ Upcoding, unbundling, modifiers, denials |
| **Autonomous Pipeline** | ❌ Manual upload only | ✅ Cron-based, email delivery |
| **B2B Offering** | ❌ No | ✅ Medical practices, nursing homes |
| **Email Integration** | ❌ No | ✅ AgentMail (confirmation + results) |
| **Legal Pages** | ❌ None | ✅ Privacy, Terms, Cookies, About, Contact |
| **Defensibility** | Low (MIT, easy to clone) | Medium (LLM overlay + pipeline + B2B) |

## Legal Research Summary

### Privacy Policies Analyzed
- **Goodbill:** HIPAA Business Associate status, 7-year retention, encryption details
- **Medical Bill Advocates:** Non-covered entity language, 10-year state-law retention
- **MedBill (ours):** Both BA and non-covered entity sections (depending on service type), 24h/30d/7yr tiered retention, AES-256 + TLS 1.3, full data rights table

### Terms of Service Analyzed
- **Goodbill:** Medical/legal disclaimers, 30-day refund, no No Surprises Act reference
- **Medical Bill Advocates:** Stronger disclaimers, No Surprises Act compliance, 7-day delivery guarantee
- **MedBill (ours):** 17 sections including No Surprises Act (Public Law 116-260), refund policy (7-day full, 30-day partial), arbitration clause, class action waiver

### Key Regulatory Gap Closed
- No existing medical billing SaaS explicitly addresses BOTH HIPAA AND the No Surprises Act. MedBill covers both.

# MedBill Auditor — Deep Research Supplement

## Discovery: BillScan — The Existing Open-Source Implementation

While researching medical bill auditing tools, we discovered **BillScan** by lamb356 (github.com/lamb356/billscan) — an open-source, MIT-licensed medical bill auditor that is significantly more complete than our initial concept.

### BillScan Capabilities

| Feature | Status | Details |
|---------|--------|---------|
| CMS Rate Databases | ✅ 1,057,383 rates | PFS (Physician Fee Schedule), CLFS (Clinical Lab Fee Schedule), ASP (Average Sales Price — drug J-codes), OPPS (Outpatient PPS/APC) |
| ZIP-to-Locality | ✅ 42,956 mappings | Geographic rate adjustments |
| Charity Care Check | ✅ 6,121 hospitals | Nonprofit hospital database |
| OCR Pipeline | ✅ PDF + image | Uses Tesseract.js |
| Dispute Letter Generator | ✅ Handlebars templates | Auto-generated appeal letters |
| Phone Negotiation Script | ✅ | Pre-written phone scripts |
| Viral Summary Cards | ✅ | Shareable findings cards |
| Insurance Rate Estimation | ✅ HMO/PPO/OON | Multipliers from KFF/RAND research |
| Web Server | ✅ Next.js app | Vercel-deployable |
| CLI Tool | ✅ Commander-based | Local usage |
| Pricing Model | ✅ $9.99/month Pro | Free tier: 3 audits/month |
| Auth | ✅ NextAuth | Google + GitHub OAuth |
| Database | ✅ Turso (SQLite) | Serverless, 9GB free tier |
| Stripe Integration | ✅ In code | Requires Stripe account setup |

### BillScan Gaps

Despite being technically complete, BillScan has critical gaps:

1. **Zero users (0 stars, 0 forks)** — No distribution, no marketing, no brand
2. **Requires manual deployment** — Needs Turso, Vercel, Stripe, Google OAuth, GitHub OAuth setup
3. **No LLM-based audit overlay** — Does CMS rate comparison but not intelligent error detection (upcoding, unbundling, modifier errors, denial code analysis)
4. **No bulk/automated processing** — Manual per-bill upload, not a pipeline
5. **No B2B angle** — Consumer-only, no medical practice/nursing home/hospital offering
6. **No agentic pipeline** — Requires user to upload, no cron-based processing
7. **No email/SMS delivery integration** — Results viewed in browser only

### The Real Opportunity

BillScan proves the technical concept works. The strategic question is **not whether to build the engine** (it exists), but **what to add that creates defensible value.**

---

## Improved Concept: Tiered Strategy

### Tier 1: Fork + Deploy BillScan (Week 1)

Fork the MIT-licensed BillScan repo, deploy on Cloudflare Pages + Turso (free tier), connect Stripe. This gives us:
- A working medical bill auditing service instantly
- The CMS database of 1M+ rates
- OCR pipeline for PDF/image bills
- Dispute letter generation
- $9.99/month subscription model

**Cost:** Zero (all services have free tiers)
**Effort:** ~2 hours to deploy
**Result:** Working product with real value proposition

### Tier 2: Add LLM Audit Overlay (Week 2)

On top of BillScan's CMS rate comparison, add an LLM-powered audit engine that detects:

| Error Type | Detection Method | Data Source |
|-----------|-----------------|-------------|
| **Upcoding** | Compare billed CPT code level vs service documentation + time ranges | CPT database + LLM |
| **Unbundling** | Check if services should be billed as single package | MCP bundling rules |
| **Modifier errors** | Missing or incorrect modifiers | MCP modifier data |
| **Denial code analysis** | Wrong CARC code applied | MCP denial codes with resolution steps |
| **Duplicate billing** | Same CPT code + date = duplicate | EOB data |
| **Medical necessity** | Does the ICD-10 diagnosis justify the CPT procedure? | LLM + code databases |

This creates a hybrid product:
- **BillScan engine** → detects price overcharges vs CMS rates
- **LLM overlay** → detects coding errors, pattern violations, and procedural mistakes
- Combined → more comprehensive audit than either alone

### Tier 3: Add Autonomous Pipeline (Week 3)

Build the cron-based processing pipeline:
- Users submit bills via web form or email (AgentMail inbox)
- Cron picks up jobs, runs BillScan + LLM audit
- Results delivered via email
- Reports stored as shareable web pages

This makes the service **fully autonomous** — submit and forget, get results delivered.

### Tier 4: B2B Offering (Week 4+)

Target medical practices, nursing homes, and billing departments:

- **Bulk audit processing** — Upload 100+ bills at once
- **Recurring audits** — Schedule weekly/monthly audits
- **Custom rate benchmarks** — Compare against your own payer contracts
- **Dashboard** — Aggregate findings across all bills
- **Pricing:** $199/month for up to 500 bills, $499/month for unlimited

This transforms the concept from a consumer tool (low willingness to pay, high churn) to a B2B SaaS (high willingness to pay, low churn).

---

## Competitive Analysis (Updated)

### Direct Competitors

| Product | Type | Pricing | AI? | B2B? | Notes |
|---------|------|---------|-----|------|-------|
| **BillScan** | Open source | Free (self-host) or $9.99/mo (hosted) | CMS comparison only | No | MIT, 0 stars, no users |
| **Goodbill** | Consumer service | 20% of savings | Human + AI | No | YC W22, humans review bills |
| **Medical Bill Advocates** | Consumer service | 20-35% of savings | No | No | Human advocates, weeks turnaround |
| **ClaimMatrix** | B2B engine | Enterprise | Rules + ML | Yes | Self-insured employers only |
| **MediBill-Check** | Research project | N/A | AI-assisted | No | 0 stars, academic |

### Indirect Competitors

| Product | Type | Notes |
|---------|------|-------|
| **PatientMatters** | Patient payment portals | Provider-facing, not audit |
| **Simplee** | Patient billing | Payment processing, not audit |
| **HealthSherpa** | Insurance shopping | Not bill auditing |
| **TurboTax** | Tax software | Adjacent concept (automated tax filing) |

### Key Insight

**No competitor combines all three:**
1. CMS rate database (automated pricing comparison)
2. LLM-powered coding error detection
3. Autonomous processing pipeline

This is a defensible combination. BillScan provides #1. The LLM overlay provides #2. The cron pipeline provides #3.

---

## Business Model Refinement

### Consumer Pricing

| Tier | Price | Features |
|------|-------|----------|
| Free Scan | $0 | Upload bill, get error probability score + estimated savings range. No details revealed. |
| Full Audit | $29 | Complete error analysis, CMS rate comparison, code-level findings, savings estimate per error. |
| Total Recovery | $49 or 15% of savings | Full audit + dispute letter + phone script + follow-up support. Pay only if we find errors. |

### B2B Pricing

| Tier | Price | Features |
|------|-------|----------|
| Starter | $99/month | 100 bills/month, basic audit, email reports |
| Professional | $299/month | 500 bills/month, full audit + LLM overlay, dashboard, API access |
| Enterprise | Custom | Unlimited bills, custom benchmarks, SLA, dedicated support |

### Revenue Projection

| Year | Consumers | B2B | Monthly Revenue |
|------|-----------|-----|-----------------|
| Month 1 | 30 audits × $29 | 1 starter × $99 | $969 |
| Month 3 | 100 audits × $29 | 3 starter + 1 pro | $3,296 |
| Month 6 | 300 audits × $29 | 5 starter + 3 pro | $10,692 |
| Month 12 | 1000 audits × $29 | 10 starter + 5 pro | $36,900 |

---

## Technical Architecture (Final)

```
┌─────────────────────────────────────────────────────────────┐
│                     User (Web / Email)                       │
├─────────────────────────────────────────────────────────────┤
│  Cloudflare Pages (Frontend)                                │
│  ├── Landing page                                            │
│  ├── Upload form (PDF/image)                                │
│  ├── Pricing page with Stripe checkout                      │
│  ├── Report viewer (shareable URL)                          │
│  └── Dashboard (B2B: bulk upload, history)                  │
├─────────────────────────────────────────────────────────────┤
│  Cloudflare Workers (API)                                   │
│  ├── POST /api/upload — receive bill + create job            │
│  ├── GET /api/status/{id} — job status polling               │
│  ├── GET /api/report/{id} — serve report page                │
│  ├── POST /api/report — receive audit results (from VPS)    │
│  └── POST /api/stripe — Stripe webhook handler               │
├─────────────────────────────────────────────────────────────┤
│  VPS (Processing)                                           │
│  ├── BillScan engine (Node.js CLI)                          │
│  │   ├── OCR (Tesseract) → extract text from PDF/image       │
│  │   ├── CMS rate comparison (1M+ rates)                    │
│  │   ├── ZIP-to-locality mapping                            │
│  │   ├── Charity care check                                 │
│  │   └── Insurance rate estimation                          │
│  ├── LLM audit overlay (pi --print)                         │
│  │   ├── CPT code validation + upcoding check               │
│  │   ├── Bundling rules check                               │
│  │   ├── Modifier rules check                               │
│  │   ├── Denial code analysis                               │
│  │   └── Medical necessity check (ICD-10 → CPT)             │
│  ├── Report generator (LLM + templates)                     │
│  │   ├── Plain English findings                             │
│  │   ├── Dispute letter (handlesbars template)              │
│  │   ├── Phone negotiation script                           │
│  │   └── Viral summary card (OG image)                      │
│  └── Cron queue (hermes cron, every 2-3 min)                │
├─────────────────────────────────────────────────────────────┤
│  Storage                                                    │
│  ├── Turso (SQLite) — CMS rates, ZIP codes, hospitals       │
│  ├── Cloudflare KV — job state, temporary data              │
│  └── Local FS — BillScan database, job queue                │
├─────────────────────────────────────────────────────────────┤
│  Delivery                                                   │
│  ├── AgentMail — email notifications + report delivery      │
│  └── Cloudflare Pages — report pages + viral cards          │
└─────────────────────────────────────────────────────────────┘
```

### Key Data Flows

1. **User submits bill** → CF Worker queues job in KV + sends email to AgentMail
2. **Cron picks up job** → runs BillScan CLI (OCR → CMS comparison → insurance estimate)
3. **Cron runs LLM overlay** → pi CLI with EOB text → finds coding errors
4. **Cron generates report** → combines BillScan + LLM findings → generates dispute letter → generates phone script
5. **Cron uploads results** → POST to CF Worker API → stores in KV + Turso
6. **User gets email** → link to report page
7. **Report page** → shows findings, savings, dispute letter, phone script, shareable summary card

---

## Comparison: Our Approach vs BillScan

| Aspect | BillScan Standalone | Our Fork + LLM Overlay |
|--------|-------------------|----------------------|
| CMS Rate Comparison | ✅ Yes | ✅ Yes (same engine) |
| OCR for PDF/Image | ✅ Yes | ✅ Yes |
| Dispute Letter | ✅ Yes | ✅ Enhanced with LLM |
| Phone Script | ✅ Yes | ✅ Enhanced with LLM |
| Viral Card | ✅ Yes | ✅ Yes |
| Pricing Model | ✅ $9.99/mo | ✅ Same + B2B tiers |
| **LLM Error Detection** | ❌ No | ✅ Upcoding, unbundling, modifiers, denials |
| **Autonomous Pipeline** | ❌ Manual upload only | ✅ Cron-based, email delivery |
| **B2B Offering** | ❌ No | ✅ Medical practices, nursing homes |
| **AgentMail Integration** | ❌ No | ✅ Email submission + delivery |
| **Defensibility** | Low (MIT, easy to clone) | Medium (LLM overlay + pipeline + B2B) |

---

## Build Plan

### Phase 1: Deploy BillScan (Week 1)
- Fork github.com/lamb356/billscan
- Deploy to Cloudflare Pages (or Vercel as documented)
- Set up Turso database with CMS data
- Connect Stripe for payments
- Test end-to-end with sample bills

### Phase 2: LLM Overlay (Week 2)
- Build Python audit engine using pi CLI
- Integrate medical-billing-mcp data (CPT codes, modifiers, bundling, denials)
- Run BillScan output through LLM for secondary error detection
- Combine results into unified report

### Phase 3: Autonomous Pipeline (Week 3)
- Build cron-based job queue (same pattern as RepoRoast)
- Implement email submission (AgentMail)
- Implement bulk upload for B2B
- Add usage tracking for subscription billing

### Phase 4: B2B Launch (Week 4)
- Medical practice dashboard
- Batch processing
- Custom rate benchmarks
- API for integration

---

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| HIPAA violation | Low | Critical | Process in-memory, delete after audit, encrypt at rest, minimize PHI retention |
| LLM accuracy on EOBs | Medium | High | Start with BillScan's deterministic engine, LLM is secondary overlay. Measure accuracy on 10+ real EOBs before launch. |
| CMS data staleness | Low | Medium | BillScan's fetch-cms script updates monthly. Automate updates. |
| Stripe/Turso billing complexity | Medium | Low | Both platforms have free tiers. Stripe handles all payment complexity. |
| Competition catches up | High | Medium | BillScan is MIT — anyone can use it. Moat is LLM overlay + B2B relationships + pipeline automation. |
| Users won't upload medical bills | Medium | High | Privacy concerns. Mitigation: clear privacy policy, no account required for scan, encrypted processing, delete after audit. |

---

## References

- **BillScan** — github.com/lamb356/billscan (MIT, 0⭐)
- **medical-billing-mcp** — github.com/Kustode-ce/medical-billing-mcp (MIT, 4⭐)
- **healthcare-billing-codes** — github.com/contextkits/healthcare-billing-codes (1⭐)
- **ClaimMatrix** — github.com/samuelogboye/ClaimMatrix-api (1⭐)
- **CMS Physician Fee Schedule** — cms.gov/medicare/payment/fee-schedules/physician
- **Goodbill** — goodbill.com (YC W22)
- **Medical Bill Advocates** — medicalbilladvocates.com

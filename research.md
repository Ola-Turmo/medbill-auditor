# Medical Bill Auditor — Research & Architecture

**Status:** Pre-build research phase
**Date:** June 2026
**Market:** Automated medical bill auditing for consumers

---

## Executive Summary

Medical billing errors affect 30-50% of all US medical bills, costing patients hundreds of billions per year. Existing solutions are either manual (human advocates charging 20-35% of savings, weeks turnaround) or enterprise-only (B2B claims audit tools for self-insured employers). **No consumer-facing automated medical bill auditor exists.**

Open-source medical billing knowledge layers (ICD-10, CPT, denial codes, bundling rules, modifiers) are available as MCP servers. The technical building blocks for a fully automated consumer audit product are all in place — the gap is the product layer.

---

## Market Analysis

### Problem Size
- 300M insured Americans receive 3-5 medical bills per year = ~1.2B bills/year
- 30-50% contain at least one billing error (sources: JAMA, AHIP, consumer reports)
- Average overcharge per error: $200-$1,000+
- Total US healthcare billing waste: $100B-$750B/year (varies by source, includes fraud, abuse, overcharging, admin waste)

### Existing Solutions

| Competitor | Model | Price | Consumer-facing? | AI-native? |
|-----------|-------|-------|-----------------|------------|
| Medical Bill Advocates | Human advocates | 20-35% of savings | Yes | No |
| Goodbill (YC W22) | Bill review + negotiation | 20% of savings | Yes | Hybrid |
| ClaimMatrix | B2B audit engine | Enterprise | No | Hybrid (rules + ML) |
| Patient Advocate | Human advocates | $100-200/hr | Yes | No |
| Simplee/HealthSherpa | Payment portals | Free (for providers) | Indirect | No |

**Key finding:** No fully automated consumer medical bill audit product exists. Goodbill is the closest — they still use humans and take weeks.

---

## Technical Landscape

### Open Source Building Blocks (discovered via research)

#### medical-billing-mcp (4⭐)
- MCP server with structured medical billing knowledge
- Data files: ICD-10 codes, CPT codes with time ranges + documentation requirements, modifiers (25, 59, etc.), denial codes (CARC with resolution steps), payer-specific rules, bundling rules
- MIT license
- Available as Docker or pip install
- Repository: github.com/Kustode-ce/medical-billing-mcp

#### healthcare-billing-codes (1⭐)
- MCP server for lookup and search of CPT, ICD-10, HCPCS codes
- Tools: `lookup_billing_code`, `search_codes_by_description`
- Repository: github.com/contextkits/healthcare-billing-codes

#### ClaimMatrix-ui/api (1⭐)
- AI-powered medical claims audit engine for self-insured employers
- Rule-based checks + ML anomaly detection (IsolationForest)
- Detects: duplicates, upcoding, unbundling, price outliers, missing 501(r) screening
- Built with FastAPI, PostgreSQL, Pandas, scikit-learn
- Repository: github.com/samuelogboye/ClaimMatrix-api

#### Medical-Claims-Audit-AI (0⭐)
- LangGraph-powered workflow demonstrating automated medical claims audit
- Repository: github.com/Tuhin-thinks/Medical-Claims-Audit-AI

---

## Billing Error Types (Detectable)

| Error Type | Description | Detection Method | Data Needed |
|-----------|-------------|-----------------|-------------|
| **Upcoding** | Billed a more expensive CPT code than service warranted | Cross-check CPT time ranges + documentation requirements | CPT database |
| **Unbundling** | Services that should be bundled as single package are split | Check bundling rules in MCP data | Bundling JSON |
| **Duplicate billing** | Same service billed twice on same date | Date + CPT code match | EOB data |
| **Incorrect modifier** | Missing necessary modifier or using wrong one | Cross-check modifier rules | Modifiers JSON |
| **Balance billing** | In-network provider billed above allowed amount | Compare billed vs allowed | EOB data |
| **Wrong patient responsibility** | Deductible/coinsurance calculated incorrectly | Check deductible status + plan terms | EOB data |
| **Denial code errors** | Incorrect CARC code applied | Cross-check denial code applicability | Denials JSON |
| **MUE violations** | Units exceed Medically Unlikely Edit limits | Check CMS MUE tables | MUE data |
| **Timely filing** | Claim submitted beyond filing deadline | Check dates + payer rules | Payer JSON |

---

## Proposed Architecture

```
User uploads EOB PDF + itemized bill
         │
         ▼
    OCR Layer (pdfplumber / Tesseract)
    Extracts raw text from PDFs + scanned images
         │
         ▼
    LLM Extraction (pi --print)
    Extracts structured data: CPT codes, ICD-10 codes, 
    billed amounts, paid amounts, adjustment codes,
    patient responsibility, dates, provider info
         │
         ▼
    Audit Engine
    ├── 1. CPT time/documentation check → upcoding
    ├── 2. Bundling rules check → unbundling  
    ├── 3. Modifier rules check → modifier errors
    ├── 4. Denial code resolution check → incorrect denials
    ├── 5. Price outlier detection → overcharging
    ├── 6. Duplicate detection → double billing
    └── 7. MUE limit check → excessive units
         │
         ▼
    Report Generator (LLM)
    ├── Plain English findings summary
    ├── Savings estimate (total overcharge)
    ├── Ready-to-send appeal letter  
    └── Specific arguments with code references
         │
         ▼
    Delivery (Email / Web page)
```

### Data Flow
1. User uploads via web form (Cloudflare Pages)
2. CF Worker stores job in KV, sends to processing queue
3. VPS cron picks up job, runs audit pipeline
4. Results stored, report page generated
5. User gets email notification + shareable report URL

### Stack
- **Frontend:** Cloudflare Pages (static site, design-taste-frontend principles)
- **API:** CF Workers (job submission, status polling, report serving)
- **OCR:** pdfplumber (Python, server-side)
- **LLM:** pi CLI (for extraction + report generation)
- **Code database:** medical-billing-mcp data files (local JSON)
- **Queue:** flat JSON file on VPS (same pattern as RepoRoast)
- **Cron:** Hermes cron (process queue every 2-3 minutes)
- **Email:** AgentMail (delivery + notifications)

---

## Business Model

### Recommended: Hybrid Model

**Tier 1 — Free Scan ($0)**
- Upload EOB
- Get error probability score + estimated savings range
- No specific findings revealed
- Captures email for followup

**Tier 2 — Full Audit ($39)**
- Complete error analysis with code-level specificity
- Plain English summary of each error
- Savings estimate per error type
- Ready-to-send appeal letter

**Tier 3 — Concierge ($79 or 20% of savings)**
- Everything in Tier 2
- LLM-generated appeal letter addressed to specific payer
- Follow-up if denied (second-level appeal)
- Escalation support

### Unit Economics
- LLM cost per audit: ~$0.10-0.30 (pi CLI, short prompts)
- OCR cost: $0 (pdfplumber is free)
- Storage: ~$0.001/audit
- Hosting: already paid for (VPS + CF Pages free tier)
- **Gross margin: 99%+** on Tier 2, ~90% on Tier 3

### Revenue Projection
- Conservative: 100 audits/month × $39 = $3,900/month
- Moderate: 500 audits/month × $39 = $19,500/month
- Aggressive: 2,000 audits/month × $39 = $78,000/month

---

## Regulatory Analysis

### HIPAA
- EOBs and medical bills contain Protected Health Information (PHI)
- Requirements: encryption at rest + transit, minimal data retention, no logging of raw PHI
- Single-person operation with encrypted storage: low risk
- Recommendation: process in-memory only, delete source files after audit, never log PHI

### Not Practicing Medicine or Law
- The tool generates "suggestion letters" — not legal advice or medical diagnosis
- Same model as TurboTax (tax software) or LegalZoom (legal document generation)
- Add disclaimer: "This is not legal advice. Consult an attorney for your specific situation."

### No Insurance License Required
- We audit bills. We do not sell insurance.
- No state licensing needed.

---

## Competitive Moat

1. **Speed:** AI processes in 2 minutes vs human advocates taking 2-6 weeks
2. **Cost:** $39 flat fee vs 20-35% of savings (which can be $1,000+ on large bills)
3. **Data:** The open-source billing code databases + our audit rules engine
4. **Automation:** Fully unattended — submit and forget, get email when done
5. **Scale:** Can handle unlimited concurrent audits (VPS + cron)

---

## Next Steps to Ship

1. [ ] Set up Stripe/Gumroad payment link
2. [ ] Build OCR + LLM extraction pipeline (test on real EOBs)
3. [ ] Load CPT/ICD-10/denial/bundling data from open-source MCP repos
4. [ ] Implement audit rules engine
5. [ ] Build web frontend (Cloudflare Pages)
6. [ ] Deploy cron processing pipeline
7. [ ] Test on 10 real EOBs, measure accuracy
8. [ ] Launch

---

## References

- medical-billing-mcp: github.com/Kustode-ce/medical-billing-mcp
- healthcare-billing-codes: github.com/contextkits/healthcare-billing-codes
- ClaimMatrix: github.com/samuelogboye/ClaimMatrix-api
- Goodbill (YC W22): goodbill.com
- CMS MUE tables: cms.gov/medicare/coding/national-correct-coding-initiative-ncci-medically-unlikely-edits

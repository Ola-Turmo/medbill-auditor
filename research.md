# MedBill Auditor — Market Research & Competitive Analysis

**Status:** Live in production at medbill-auditor.pages.dev
**Date:** June 2026
**Market:** Automated medical bill auditing for consumers + medical practices

---

## Executive Summary

Medical billing errors affect 30-50% of all US medical bills, costing patients hundreds of billions per year. Existing solutions are either manual (human advocates charging 20-35% of savings, weeks turnaround) or enterprise-only (B2B claims audit tools for self-insured employers). **No consumer-facing automated medical bill auditor existed before MedBill.**

## Market Analysis

### Problem Size
- 300M insured Americans receive 3-5 medical bills per year = ~1.2B bills/year
- 30-50% contain at least one billing error (sources: JAMA, AHIP, Consumer Reports)
- Average overcharge per error: $200-$1,000+
- Total US healthcare billing waste: $100B-$750B/year (varies by source)

### Existing Solutions

| Competitor | Model | Price | Consumer-facing? | AI-native? |
|-----------|-------|-------|-----------------|------------|
| Medical Bill Advocates | Human advocates | 20-35% of savings | Yes | No |
| Goodbill (YC W22) | Bill review + negotiation | 20% of savings | Yes | Hybrid |
| ClaimMatrix | B2B audit engine | Enterprise | No | Hybrid (rules + ML) |
| Patient Advocate | Human advocates | $100-200/hr | Yes | No |
| Simplee/HealthSherpa | Payment portals | Free (for providers) | Indirect | No |

**Key finding:** No fully automated consumer medical bill audit product existed before MedBill. Goodbill is the closest — they still use humans and take weeks.

## Competitive Moat

1. **Speed:** AI processes in 2-5 minutes vs human advocates taking 2-6 weeks
2. **Cost:** $29 flat fee vs 20-35% of savings (which can be $1,000+ on large bills)
3. **Data:** CMS rate database + CPT coding rules + AI pattern recognition
4. **Automation:** Fully unattended — submit and forget, get email when done
5. **Scale:** Can handle unlimited concurrent audits (VPS + cron)

## Billing Error Types (Detectable)

| Error Type | Description | Detection Method | Frequency |
|-----------|-------------|-----------------|-----------|
| **Upcoding** | Billed more expensive CPT code than warranted | Cross-check CPT time ranges + documentation | Very Common |
| **Unbundling** | Services billed separately that should be bundled | Check bundling rules | Common |
| **Duplicate billing** | Same service billed twice on same date | Date + CPT code match | Very Common |
| **Incorrect modifier** | Missing or wrong CPT modifier | Cross-check modifier rules | Common |
| **Balance billing** | In-network provider billed above allowed amount | Compare billed vs allowed | Moderate |
| **Wrong denial code** | Incorrect CARC code applied | Cross-check denial code applicability | Less Common |
| **MUE violations** | Units exceed Medically Unlikely Edit limits | Check CMS MUE tables | Moderate |
| **Medical necessity** | ICD-10 diagnosis doesn't justify CPT procedure | LLM + code databases | Moderate |

## Legal & Regulatory Analysis

### HIPAA
- MedBill acts as a **HIPAA Business Associate** when serving healthcare providers (B2B)
- Direct-to-consumer: not a covered entity, but follows HIPAA best practices
- PHI encrypted in transit (TLS 1.3) and at rest (AES-256)
- In-memory processing, source files deleted within 24 hours
- Reports retained 30 days, metadata pseudonymized for 7 years

### No Surprises Act
- MedBill's dispute letter service complies with Public Law 116-260
- Balance billing violations identified in audit reports
- CMS No Surprises Help Desk referenced in Terms of Service

### Disclaimer
- MedBill is NOT a healthcare provider, medical professional, or law firm
- Audit reports are informational — not medical or legal advice
- Savings estimates are illustrative, not guaranteed

## Business Model

| Tier | Price | For | Features |
|------|-------|-----|----------|
| Free Scan | $0 | Anyone | Upload bill, get error probability + savings range |
| Full Audit | $29 | Individuals | Line-by-line audit report, dispute letter, phone script |
| B2B Starter | $99/mo | Small practices | 100 bills/month, basic CMS rate audit |
| B2B Professional | $299/mo | Larger practices | 500 bills/month, LLM overlay, dashboard, API |
| Enterprise | Custom | Hospitals | Unlimited, custom benchmarks, SLA |

### Unit Economics
- LLM cost per audit: ~$0.10-0.30 (pi CLI)
- OCR cost: $0 (pdfplumber is free)
- Storage: ~$0.001/audit
- Hosting: Cloudflare free tier + existing VPS
- **Gross margin: 99%+** on Full Audit, ~90% on B2B

### Revenue Projection
- Conservative: 100 audits/month × $29 = $2,900/month
- Moderate: 500 audits/month × $29 = $14,500/month
- Aggressive: 2,000 audits/month × $29 = $58,000/month
- Plus B2B: $99-$299/mo per practice

## References
- CMS Physician Fee Schedule: cms.gov/medicare/payment/fee-schedules/physician
- BillScan: github.com/lamb356/billscan (MIT, 0⭐)
- medical-billing-mcp: github.com/Kustode-ce/medical-billing-mcp
- Goodbill: goodbill.com (YC W22)
- Medical Bill Advocates: medicalbilladvocates.com
- No Surprises Act: cms.gov/nosurprises

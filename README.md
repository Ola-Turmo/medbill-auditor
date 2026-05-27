# MedBill Auditor

**Concept research for an autonomous medical bill auditing service.**

Medical billing errors affect 30-50% of US medical bills. Existing solutions are human-powered (slow, expensive) or enterprise-only. This repo explores a fully automated, AI-native alternative.

## Key Findings

- Open-source billing code databases already exist (CPT, ICD-10, modifiers, denial codes, bundling rules)
- BillScan (github.com/lamb356/billscan) is a complete MIT-licensed implementation with 1M+ CMS rates, OCR pipeline, dispute letter generation, and a $9.99/month pricing model — but has 0 stars and 0 users
- LLMs can detect upcoding, unbundling, duplicate billing, modifier errors, and denial code errors on top of rate comparisons
- No consumer-facing automated audit product exists
- Unit economics are favorable (99%+ gross margin)
- Buildable within 1-2 weeks by forking BillScan and adding an LLM audit overlay + autonomous pipeline

## Repository Contents

| File | Description |
|------|-------------|
| `design.md` | Full visual design concept: layout, color system, typography, conversion strategy, section-by-section walkthrough of the landing page |
| `research.md` | Initial market analysis: problem sizing, competitor landscape, billing error taxonomy (10 detectable types), business model options, regulatory analysis |
| `deep-research.md` | Deep dive: BillScan discovery (complete open-source implementation), competitive landscape update, tiered build strategy (fork -> LLM overlay -> pipeline -> B2B), improved technical architecture, risk analysis |
| `test-plan.md` | End-to-end test plan with 71 test cases across 12 categories: landing page, free scan flow, full audit flow, report consumption, action taking, billing, B2B, edge cases, mobile, security, and post-launch verification |

## Build Strategy

1. **Week 1** — Fork BillScan, deploy as hosted service, connect Stripe
2. **Week 2** — Add LLM audit overlay for coding error detection (upcoding, unbundling, modifiers, denials)
3. **Week 3** — Add autonomous cron-based processing pipeline with email delivery
4. **Week 4** — Launch B2B tier for medical practices and nursing homes

## Pricing Model

| Tier | Price | For whom |
|------|-------|----------|
| Free Scan | $0 | Anyone — upload bill, get error probability + savings range |
| Full Audit | $29 | Individuals — complete analysis + dispute letter + phone script |
| Starter (B2B) | $99/mo | Small practices — 100 bills/month |
| Professional (B2B) | $299/mo | Larger practices — 500 bills/month + API |
| Enterprise | Custom | Hospitals and billing departments |

## Status

Pre-build research phase. Ready to prototype when payment infrastructure (Stripe) is connected. All technical building blocks exist as open source.

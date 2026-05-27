# MedBill Auditor

**Concept research for an autonomous medical bill auditing service.**

Medical billing errors affect 30-50% of US medical bills. Existing solutions are human-powered (slow, expensive) or enterprise-only. This repo explores a fully automated, AI-native alternative.

## Key Findings

- Open-source billing code databases already exist (CPT, ICD-10, modifiers, denial codes, bundling rules)
- LLMs can reliably parse EOBs and detect upcoding, unbundling, duplicate billing, and other errors
- No consumer-facing automated audit product exists
- Unit economics are favorable (99%+ gross margin)
- Buildable within 1-2 weeks with existing infrastructure

## Contents

- `research.md` — Full market analysis, technical architecture, competitive landscape, regulatory concerns
- `audit-engine/` — Prototype audit engine (planned)

## Status

Pre-build research phase. Ready to prototype when payment infrastructure is available.

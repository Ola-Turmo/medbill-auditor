# MedBill Auditor — End-to-End Test Plan

**Version:** 1.0
**Scope:** Full consumer journey from discovery to outcome
**Environment:** Production
**Test Data:** Sample EOB PDFs + itemized hospital bills with known errors
**Role:** End user (patient who received a medical bill)

---

## Table of Contents

1. [Pre-Flight: Test Data Preparation](#1-pre-flight-test-data-preparation)
2. [Landing Page Experience](#2-landing-page-experience)
3. [Free Scan Flow](#3-free-scan-flow)
4. [Full Audit Flow](#4-full-audit-flow)
5. [Report Consumption](#5-report-consumption)
6. [Action Taking](#6-action-taking)
7. [Account & Billing](#7-account--billing)
8. [B2B Flow](#8-b2b-flow)
9. [Error & Edge Cases](#9-error--edge-cases)
10. [Mobile & Responsive](#10-mobile--responsive)
11. [Security & Privacy](#11-security--privacy)
12. [Post-Launch Verification](#12-post-launch-verification)

---

## 1. Pre-Flight: Test Data Preparation

### 1.1 Source Test Bills

Acquire 10+ real or realistically synthesized medical bills covering:

| # | Bill Type | Error Type | Complexity | Source |
|---|-----------|------------|------------|--------|
| 1 | ER visit (hospital) | Upcoding (99284 billed, 99283 performed) | Medium | Generate from CMS public data |
| 2 | Routine checkup + lab work | Unbundling (lab panel split into individual tests) | High | Synthesize from CPT bundling rules |
| 3 | Surgery (knee arthroscopy) | Duplicate charge (same CPT code, same date, two line items) | Low | Duplicate a line item in a real bill |
| 4 | MRI with contrast | Balance billing (in-network facility, out-of-network radiologist) | High | Medicare AoD data |
| 5 | Physical therapy (6 sessions) | Units exceed MUE limits (8 units billed, max 2 per day) | Medium | CMS MUE table |
| 6 | Emergency room + doctor | Modifier 25 missing (ER copay + separate procedure) | High | AMA modifier guidelines |
| 7 | Prescription (Part B drug) | Incorrect J-code (higher reimbursement code used) | Medium | ASP pricing data |
| 8 | Urgent care visit | No errors — clean bill | Low | Generate clean bill |
| 9 | Outpatient surgery | Wrong patient responsibility (deductible already met) | Medium | EOB with accumulator tracking |
| 10 | Nursing home stay | Denial code error (CO-50 applied, should be PR-2) | High | Medicare denial code guide |

### 1.2 Test Bill Format Matrix

Each test bill must exist in these formats:

| Format | File Type | Size Limit | Notes |
|--------|-----------|------------|-------|
| PDF (text) | .pdf | 10MB max | Digitally created, selectable text |
| PDF (scanned) | .pdf | 10MB max | Printed then scanned, image-based |
| JPEG photo | .jpg | 10MB max | Phone camera photo of printed bill |
| PNG screenshot | .png | 10MB max | Screenshot from patient portal |
| Email forward | .eml | 5MB max | Forwarded bill from insurance portal |

### 1.3 Known Error Injections

For each test bill, document:

```yaml
bill_id: "ER-01"
description: "Emergency room visit with laceration repair"
expected_errors:
  - type: upcoding
    severity: high
    detail: "CPT 99284 (high severity ER visit) billed but notes indicate 99283 (moderate severity)"
    expected_savings: "$180-320"
    confidence: "high"
  - type: unbundling
    severity: medium
    detail: "Suture removal (CPT 20670) billed separately from ER visit (CPT 99283) — should be bundled"
    expected_savings: "$80-150"
    confidence: "medium"
  - type: duplicate
    severity: low
    detail: "Tetanus vaccine (CPT 90718) billed twice on same date"
    expected_savings: "$45"
    confidence: "high"
no_error_services:
  - "CBC lab work — CPT 85025, correctly coded"
  - "Chest X-ray — CPT 71045, correctly coded"
total_expected_savings: "$305-515"
total_billed_amount: "$4,237.50"
insurance_paid: "$2,890.00"
patient_responsibility: "$1,347.50"
```

---

## 2. Landing Page Experience

### 2.1 First Visit — Desktop (1920x1080)

**Test ID: LP-01**
**Title:** Page loads correctly
**Steps:**
1. Navigate to https://medbill.ai
2. Observe page load
3. Verify HTTPS (padlock icon)
**Expected:**
- Page loads in < 2.5 seconds (LCP)
- URL shows https://medbill.ai
- SSL certificate is valid
- No console errors

**Test ID: LP-02**
**Title:** Above-the-fold content renders correctly
**Steps:**
1. Load page at 1920x1080
2. Observe what is visible without scrolling
**Expected:**
- Logo visible in top-left
- "Log in" link visible in top-right (not "Sign up")
- Headline visible: "80% of medical bills contain errors. You are probably paying too much."
- Subtext visible: "Upload your bill and find out for free. No account needed. 2 minutes. HIPAA compliant."
- Upload button visible and fully within viewport
- Option to email bill visible: "or email it to scan@medbill.ai"
- Social proof quote visible (partial)
- No scroll cue, no version label, no eyebrow, no multiple CTAs
- Headline is max 2 lines at this width
- Subtext is max 3 lines at this width
- CTA button text does not wrap

**Test ID: LP-03**
**Title:** Upload button is primary CTA
**Steps:**
1. Examine the upload button
2. Check its appearance and behavior
**Expected:**
- Button has high contrast against background (WCAG AA 4.5:1)
- Button label is 3 words or fewer
- Button is clickable
- Hover state changes button appearance
- Active state shows tactile feedback
- Focus state is visible (keyboard users)

**Test ID: LP-04**
**Title:** Navigation renders on one line
**Steps:**
1. Check nav bar at 1920px width
**Expected:**
- Logo + "Log in" fit on a single line
- Nav height is 64-72px
- No hamburger menu at this width

**Test ID: LP-05**
**Title:** All sections render
**Steps:**
1. Scroll through entire page
**Expected:**
- Hero section (visible first)
- Stat bar (3 columns: $750B/year, 30-50% errors, $500+ average error)
- How it works (3 step cards, no eyebrow)
- What we detect (2x3 bento grid, 6 error types)
- Case study / social proof (quote with before/after comparison)
- Why trust us (4 columns)
- Pricing (2 column: Free Scan $0, Full Audit $29)
- FAQ (3-4 expandable questions)
- Footer (logo, source citations, contact)
- No section has an eyebrow label
- No two consecutive sections use the same layout family
- No section has a split-header

### 2.2 Tablet (768x1024)

**Test ID: LP-06**
**Title:** Responsive at tablet width
**Steps:**
1. Resize browser to 768x1024
2. Scroll through entire page
**Expected:**
- Navigation collapses to logo + hamburger (or Login fits)
- Hero stacks vertically
- Headline font-size reduces appropriately
- Stat bar collapses to single column or 2 columns
- How it works becomes vertical stack
- Bento grid becomes single column
- Pricing cards stack vertically
- No horizontal scroll
- No layout breaks

### 2.3 Phone (375x667)

**Test ID: LP-07**
**Title:** Responsive at phone width
**Steps:**
1. Resize browser to 375x667 (iPhone SE)
2. Scroll through entire page
**Expected:**
- Hero fits viewport height
- Headline readable at native font size
- Upload button full-width
- All sections single-column
- Touch targets at least 44x44px
- No content cut off
- FAQ accordions work via touch
- Pricing CTA buttons tappable

### 2.4 Reduced Motion

**Test ID: LP-08**
**Title:** Reduced motion respected
**Steps:**
1. Enable prefers-reduced-motion: reduce in OS/browser
2. Reload and interact
**Expected:**
- No CSS animations run
- No scroll-triggered reveals
- No parallax
- No hover animations
- All content visible and functional

### 2.5 Dark Mode

**Test ID: LP-09**
**Title:** Dark mode renders correctly
**Steps:**
1. Enable prefers-color-scheme: dark
2. Reload, scroll all sections
**Expected:**
- All sections use dark theme consistently
- No light-mode section appears mid-page
- Text contrast meets WCAG AA in both modes
- Accent color consistent across themes
- Upload button visible (not dark-on-dark)

---

## 3. Free Scan Flow

### 3.1 Upload

**Test ID: FS-01**
**Title:** Upload valid PDF via drag-and-drop
**Steps:**
1. Drag er-bill-overcharge.pdf onto drop zone
2. Enter email: test-user@example.com
3. Click "Scan my bill"
**Expected:**
- Upload area shows file name and size after drop
- Progress indicator appears during upload
- Submit button changes to "Scanning..." with skeleton loader
- User redirected to status page with job ID, estimated time, email notification note
- Progress bar visible (no generic circular spinner)
- Confirmation email within 1 minute

**Test ID: FS-02**
**Title:** Upload JPEG photo via click-to-browse
**Steps:**
1. Click upload area, select er-bill-photo.jpg
2. Enter email, submit
**Expected:**
- File accepted (JPEG)
- Same flow as FS-01
- Processing may take longer (OCR needed)

**Test ID: FS-03**
**Title:** Email submission works
**Steps:**
1. Email scan@medbill.ai with bill PDF attached
**Expected:**
- Auto-reply within 2 minutes with job ID and status link
- Job visible in system

### 3.2 Processing

**Test ID: FS-04**
**Title:** BillScan engine processes correctly (CMS rate comparison)
**Steps:**
1. Submit er-bill-overcharge.pdf
2. Examine internal audit log
**Expected:**
- OCR extracts all line items
- Each CPT code matched against CMS Physician Fee Schedule
- Facility vs non-facility rates correctly applied
- ZIP code matched to locality
- No fabricated rates
- Output includes: each line item with CPT, description, billed, CMS allowed, difference
- Flagged lines where billed > CMS allowed by > 20%

**Test ID: FS-05**
**Title:** LLM overlay processes correctly (coding error detection)
**Steps:**
1. Same submission as FS-04
2. Examine LLM audit output
**Expected:**
- LLM extracts CPT codes, ICD-10 codes, modifiers, denial codes
- Each CPT code checked against time ranges + documentation requirements
- Upcoding detected where appropriate
- Unbundling checked
- Modifier correctness checked
- Denial codes checked against expected usage
- Duplicate line items detected
- LLM outputs confidence levels, does not fabricate findings

**Test ID: FS-06**
**Title:** Free scan result with errors found
**Steps:**
1. Submit er-bill-overcharge.pdf
2. Wait for completion
3. View results
**Expected:**
- Report page at unique URL (/report/{uuid})
- Shows: error probability score, estimated savings range, error count by severity, error types by category
- No specific error details revealed
- Page is shareable (no login required)
- Email notification with savings range and CTA to upgrade
- Page loads in < 2 seconds

**Test ID: FS-07**
**Title:** Free scan result with no errors (clean bill)
**Steps:**
1. Submit urgent-care-clean.pdf
2. View results
**Expected:**
- Shows: "Low — no errors detected", savings: $0
- Breakdown of checks performed
- No false-upsell CTA
- Option to upload another bill

**Test ID: FS-08**
**Title:** Email delivery timing
**Steps:**
1. Submit 3 bills simultaneously
2. Measure time to email receipt
**Expected:**
- All results delivered within 5 minutes
- Emails not in spam folder

### 3.3 Upgrade Funnel

**Test ID: FS-09**
**Title:** Upgrade from free scan to full audit
**Steps:**
1. Complete free scan with errors (FS-06)
2. Click "Upgrade to full audit"
3. Complete Stripe checkout for $29
4. Return to report page
**Expected:**
- Stripe checkout shows $29 Full Audit
- After payment, same report URL shows full details
- No re-processing needed
- Confirmation email sent

**Test ID: FS-10**
**Title:** Clean free scan — no deceptive upsell
**Steps:**
1. Complete clean scan (FS-07)
2. Observe page messaging
**Expected:**
- No "Upgrade to see details" CTA
- Honest message: "Our system found no errors. Try another bill or get a second opinion."

---

## 4. Full Audit Flow

**Test ID: FA-01**
**Title:** Purchase full audit directly from pricing
**Steps:**
1. Click "Start full audit" on pricing page
2. Complete Stripe checkout for $29
3. Upload bill after payment
**Expected:**
- Stripe shows $29 one-time payment
- After payment, upload flow same as FS-01
- Results include full details (no upgrade gate)
- Confirmation emails: receipt + processing + results

**Test ID: FA-02**
**Title:** Full audit with all error types
**Steps:**
1. Purchase full audit
2. Submit surgery-bundle-duplicate.pdf
3. View full report
**Expected:**
- Every finding includes: error type, severity, specific CPT code(s), billed vs correct, dollar impact, plain English explanation, supporting citation, confidence level
- Total savings estimate at top
- Breakdown by error type
- Original vs adjusted patient responsibility

**Test ID: FA-03**
**Title:** Multiple bills in one audit
**Steps:**
1. Purchase full audit
2. Upload 3 bills at once (batch)
3. Wait for processing
**Expected:**
- All 3 processed
- Per-bill breakdown + aggregate savings
- Batch upload via ZIP or multi-select

**Test ID: FA-04**
**Title:** Bill with balance billing (out-of-network)
**Steps:**
1. Submit mri-balance-bill.pdf
**Expected:**
- In-network facility charges correctly identified
- Out-of-network radiologist flagged
- No Surprises Act protections noted if applicable

**Test ID: FA-05**
**Title:** Bill with MUE limit violation
**Steps:**
1. Submit pt-excessive-units.pdf
**Expected:**
- MUE violation detected
- CMS MUE table reference cited
- Overcharge calculated from excess units

**Test ID: FA-06**
**Title:** Bill with missing modifier
**Steps:**
1. Submit er-modifier-missing.pdf
**Expected:**
- Missing modifier 25 detected
- AMA guideline cited
- Impact explained

**Test ID: FA-07**
**Title:** Bill with wrong denial code
**Steps:**
1. Submit nursing-denial-error.pdf
**Expected:**
- Denial code CO-50 flagged as incorrect
- Correct code PR-2 suggested
- Resolution steps shown
- Appeal argument generated

---

## 5. Report Consumption

**Test ID: RP-01**
**Title:** Report page layout
**Steps:**
1. Open full audit report URL
**Expected:**
- URL format: /report/{uuid}
- Summary card at top
- Findings list sorted by severity
- Dispute letter section
- Phone script section
- Share card section
- Action buttons
- No loading spinners, no scroll-triggered animations

**Test ID: RP-02**
**Title:** Report loads without authentication
**Steps:**
1. Open report in incognito window
**Expected:**
- Full report renders
- No login wall
- URL is the only access mechanism

**Test ID: RP-03**
**Title:** Report mobile
**Steps:**
1. Open at 375px wide
**Expected:**
- Stacks vertically, findings fill width, buttons full-width and tappable

**Test ID: RP-04**
**Title:** Report prints correctly
**Steps:**
1. Ctrl+P on report page
**Expected:**
- Print stylesheet removes interactive elements
- All content prints on white background
- Header and footer present

**Test ID: RP-05**
**Title:** Combined report accuracy vs standalone BillScan
**Steps:**
1. Run same bill through BillScan CLI and MedBill
2. Compare
**Expected:**
- MedBill finds all BillScan findings plus coding errors
- No contradictions between engines
- False positives flagged with low confidence

---

## 6. Action Taking

**Test ID: AT-01**
**Title:** Dispute letter is actionable
**Steps:**
1. Click "Send dispute letter"
**Expected:**
- Opens email client with pre-filled draft
- To, subject, body all correct
- No placeholder text
- Professional, factual tone
- No em-dashes

**Test ID: AT-02**
**Title:** PDF download
**Steps:**
1. Click "Download PDF report"
**Expected:**
- PDF downloads within 5 seconds, under 2MB
- Contains all sections, properly formatted

**Test ID: AT-03**
**Title:** Phone script usability
**Steps:**
1. Read phone script section
**Expected:**
- Sections: before you call, opening, key arguments, expected pushback, closing, call notes template
- No em-dashes
- Realistic pushback responses

**Test ID: AT-04**
**Title:** Share card
**Steps:**
1. Click "Share report"
**Expected:**
- OG meta tags generate correct social preview
- No PHI in share card
- Share-to-Twitter and Share-to-LinkedIn buttons work

---

## 7. Account & Billing

**Test ID: BI-01**
**Title:** Successful payment
**Steps:**
1. Checkout with card 4242 4242 4242 4242
**Expected:**
- Redirect to upload page
- Receipt email from Stripe
- Can upload immediately

**Test ID: BI-02**
**Title:** Declined card
**Steps:**
1. Checkout with card 4000 0000 0000 0002
**Expected:**
- Decline message shown on Stripe page
- No charge made
- Can try another card

**Test ID: BI-03**
**Title:** Free scan requires no payment
**Steps:**
1. Upload without payment step
**Expected:**
- Accepted and processed
- No Stripe interaction

**Test ID: BI-04**
**Title:** Account creation after audit
**Steps:**
1. Complete free scan
2. Create account via email + password or Google OAuth
**Expected:**
- No payment info required
- Past audit linked to account
- Account page shows history

**Test ID: BI-05**
**Title:** Delete account
**Steps:**
1. Settings > Delete account
**Expected:**
- Confirmation dialog
- All data deleted
- Confirmation email
- Cannot log in again

---

## 8. B2B Flow

**Test ID: B2B-01**
**Title:** B2B pricing page
**Steps:**
1. Navigate to /business
**Expected:**
- Tiers: Starter $99/mo, Professional $299/mo, Enterprise custom
- Feature comparison table
- Direct signup for Starter/Pro
- "Schedule a demo" for Enterprise

**Test ID: B2B-02**
**Title:** Bulk upload 10 bills
**Steps:**
1. Sign up Starter plan
2. Upload 10 PDFs
**Expected:**
- All 10 uploaded and processed
- Dashboard shows aggregate stats
- CSV export available

**Test ID: B2B-03**
**Title:** Dashboard overview
**Steps:**
1. After B2B-02, view dashboard
**Expected:**
- Usage widget (10/100 bills)
- Subscription status
- Recent audits list
- Upload button

---

## 9. Error & Edge Cases

**Test ID: ER-01**
**Title:** Unsupported file type
**Steps:**
1. Upload .txt, .heic, .docx
**Expected:**
- Rejected with clear error message
- No crash, no silent failure

**Test ID: ER-02**
**Title:** File over size limit
**Steps:**
1. Upload 12MB file (limit 10MB)
**Expected:**
- Rejected: "File too large. Maximum size: 10MB"

**Test ID: ER-03**
**Title:** Corrupted file
**Steps:**
1. Upload truncated PDF, 0-byte JPEG
**Expected:**
- Error: "Unable to read this file"
- Email notification
- Can re-upload
- No charge

**Test ID: ER-04**
**Title:** Non-medical document
**Steps:**
1. Upload restaurant receipt
**Expected:**
- No CPT/ICD-10 codes found
- Message: not a medical bill, try again

**Test ID: ER-05**
**Title:** Non-US provider
**Steps:**
1. Upload UK NHS bill
**Expected:**
- Detected as non-US
- Message: US bills only

**Test ID: ER-06**
**Title:** Submit without email
**Steps:**
1. Leave email blank
**Expected:**
- Validation prevents submission
- "Email is required"

**Test ID: ER-07**
**Title:** Invalid email format
**Steps:**
1. Enter "not-an-email"
**Expected:**
- Validation: "Please enter a valid email address"

**Test ID: ER-08**
**Title:** OCR fails on low-quality image
**Steps:**
1. Upload blurry photo
**Expected:**
- OCR confidence below threshold
- Message: trouble reading, suggestions to improve

**Test ID: ER-09**
**Title:** LLM extraction fails
**Steps:**
1. Upload unusually formatted bill
**Expected:**
- BillScan engine still runs
- CMS rate comparison still provided
- LLM section shows unavailable message
- Partial result delivered

**Test ID: ER-10**
**Title:** Queue backlog
**Steps:**
1. Submit 50 bills simultaneously
**Expected:**
- All accepted
- Processing at 2-3 min per bill
- All completed within 3 hours
- No jobs lost

**Test ID: ER-11**
**Title:** Large file timeout
**Steps:**
1. Upload 500-page PDF
**Expected:**
- First N pages processed
- Warning about truncated analysis
- Partial results

**Test ID: ER-12**
**Title:** Stripe session expires
**Steps:**
1. Start checkout, navigate away
**Expected:**
- No charge
- Can restart checkout

**Test ID: ER-13**
**Title:** Stripe webhook failure
**Steps:**
1. Complete payment, simulate webhook failure
**Expected:**
- Stripe retries 3 times
- Recovery path via support

**Test ID: ER-14**
**Title:** B2B monthly limit
**Steps:**
1. Upload 101st bill on Starter (100 limit)
**Expected:**
- Rejected with upgrade CTA

**Test ID: ER-15**
**Title:** B2B payment failure
**Steps:**
1. Subscription card expires
**Expected:**
- Warning email
- 5-day grace period
- Then downgrade to free
- Data preserved 30 days

---

## 10. Mobile & Responsive

**Test ID: MO-01**
**Title:** All pages on mobile (375px)
**Steps:**
1. Test landing, pricing, FAQ, report, account, B2B dashboard, upload
**Expected:**
- No horizontal scroll
- Touch targets >= 44x44px
- Forms usable on iOS
- No content overlap

**Test ID: MO-02**
**Title:** File upload on mobile Safari
**Steps:**
1. Tap upload on iPhone
2. Select photo, take photo, pick from Files
**Expected:**
- iOS file picker opens
- All sources work

**Test ID: MO-03**
**Title:** Phone number tappable
**Steps:**
1. Open report on mobile
2. Tap billing department number
**Expected:**
- iOS dialer opens with number

**Test ID: MO-04**
**Title:** No viewport jump on iOS
**Steps:**
1. Scroll on iOS Safari
**Expected:**
- Uses min-height: 100dvh
- No layout jump when address bar retracts

---

## 11. Security & Privacy

**Test ID: SE-01**
**Title:** Files not stored on disk
**Steps:**
1. Submit a bill
2. Check VPS filesystem
**Expected:**
- No bill files remain
- No bill content in logs

**Test ID: SE-02**
**Title:** Report URLs unguessable
**Steps:**
1. Examine report URL
**Expected:**
- UUID v4 format
- Cannot enumerate
- No access without valid UUID

**Test ID: SE-03**
**Title:** No PHI in emails
**Steps:**
1. Check all notification emails
**Expected:**
- No patient name, provider, CPT codes, dollar amounts, diagnosis
- Only job ID and report link

**Test ID: SE-04**
**Title:** No PHI in share cards
**Steps:**
1. Check OG tags, share image, tweet text
**Expected:**
- No PHI — only savings amounts

**Test ID: SE-05**
**Title:** HTTPS enforced
**Steps:**
1. Navigate to http://medbill.ai
**Expected:**
- 301 redirect to https
- HSTS header present

**Test ID: SE-06**
**Title:** B2B data isolation
**Steps:**
1. Two accounts, upload under one
**Expected:**
- No cross-tenant data access

---

## 12. Post-Launch Verification

**Test ID: PV-01**
**Title:** Core metrics tracked
**Steps:**
1. Enable Plausible analytics
2. Run all major flows
**Expected:**
- Page views, uploads, conversions tracked
- No PHI in analytics

**Test ID: PV-02**
**Title:** Cron processes queue reliably
**Steps:**
1. Submit 5 bills, check 24h logs
**Expected:**
- Cron runs every 2-3 min
- All processed within 15 min
- No crashes, no queue corruption

**Test ID: PV-03**
**Title:** Email delivery reliability
**Steps:**
1. Submit 10 bills over 24h
**Expected:**
- All emails sent within 1 min of trigger
- Zero in spam
- SPF + DKIM configured

---

## Appendix: Test Pass Criteria

| Category | Total Tests | Must Pass | Pass Rate |
|----------|-------------|-----------|-----------|
| Landing Page | 9 | 9 | 100% |
| Free Scan | 10 | 9 | 90% |
| Full Audit | 7 | 7 | 100% |
| Report Consumption | 5 | 5 | 100% |
| Action Taking | 4 | 4 | 100% |
| Account & Billing | 5 | 4 | 80% |
| B2B Flow | 3 | 2 | 67% |
| Error & Edge Cases | 15 | 12 | 80% |
| Mobile & Responsive | 4 | 4 | 100% |
| Security & Privacy | 6 | 6 | 100% |
| Post-Launch | 3 | 2 | 67% |
| **Total** | **71** | **64** | **90%** |

### Blocking Criteria

Must pass before launch:
- LP-01 through LP-05 (core landing page)
- FS-01, FS-04, FS-05, FS-06 (core free scan flow)
- FA-01, FA-02 (core full audit flow)
- RP-01, RP-02 (core report page)
- AT-01 (dispute letter)
- SE-01 through SE-05 (security & privacy)
- ER-01, ER-02, ER-03, ER-06, ER-07 (critical upload errors)

### Non-Blocking

Can ship with known issues, fix post-launch:
- MO-02 (mobile file upload — device-dependent)
- ER-10 (queue backlog — performance tuning)
- BI-05 (account deletion — low priority)
- B2B-03 (dashboard polish)

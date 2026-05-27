#!/usr/bin/env python3
"""MedBill Pipeline Cron — runs every 2-3 minutes via hermes cron.
Polls /api/queue/next, processes bills through audit engine, submits results.
"""
import sys, os, json, tempfile, urllib.request, time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from engine.audit import OCRProcessor, LLMExtractor, CMSComparator, LLMAuditor, ReportGenerator

API_BASE = os.environ.get('API_BASE', 'https://medbill-auditor.pages.dev')
MAX_PER_RUN = int(os.environ.get('MAX_CONCURRENT', '3'))

def run():
    ocr = OCRProcessor()
    extractor = LLMExtractor()
    cms = CMSComparator()
    auditor = LLMAuditor()
    reporter = ReportGenerator()
    processed = 0

    print(f"[MedBill Cron] Starting poll at {time.strftime('%H:%M:%S')}")

    while processed < MAX_PER_RUN:
        # Fetch next job
        try:
            req = urllib.request.Request(f"{API_BASE}/api/queue/next")
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
        except Exception as e:
            print(f"[Cron] Queue fetch failed: {e}")
            break

        if not data.get('job'):
            print(f"[Cron] No queued jobs")
            break

        job = data['job']
        jid = job['id']
        dl_url = data.get('download_url', '')
        print(f"[Cron] Processing job {jid}")

        if not dl_url:
            print(f"[Cron] No download URL for {jid}")
            continue

        # Download bill file
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=f".{job.get('fileType', 'pdf')}", delete=False)
            urllib.request.urlretrieve(dl_url, tmp.name)
            file_path = Path(tmp.name)
        except Exception as e:
            print(f"[Cron] Download failed for {jid}: {e}")
            continue

        # Run pipeline
        try:
            print(f"[Cron] OCR...")
            ocr_res = ocr.extract(file_path)
            if len(ocr_res.get('raw_text', '')) < 20:
                # Plain text file fallback
                with open(str(file_path)) as f:
                    ocr_res = {'raw_text': f.read()[:8000], 'pages': 1, 'is_scanned': False}

            print(f"[Cron] Extracting...")
            structured = extractor.extract(ocr_res)

            print(f"[Cron] CMS compare...")
            rates = cms.compare(structured.get('services', []))

            print(f"[Cron] LLM audit...")
            findings = auditor.audit(ocr_res.get('raw_text', ''), structured, rates)

            print(f"[Cron] Generating report...")
            report = reporter.generate(structured, rates, findings)

            # Clean up temp file
            file_path.unlink(missing_ok=True)

            # Submit results
            report['job_id'] = jid
            payload = json.dumps(report).encode()
            req = urllib.request.Request(
                f"{API_BASE}/api/report", data=payload,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                result = json.loads(r.read())
                print(f"[Cron] Job {jid} complete: {report['error_count']} errors, savings {report['savings_estimate']}")
                processed += 1

        except Exception as e:
            print(f"[Cron] Job {jid} failed: {e}")
            # Submit error result
            try:
                err_report = {
                    'job_id': jid,
                    'findings': [{'type': 'error', 'severity': 'low', 'amount': 0,
                                  'description': f'Pipeline error: {str(e)}'}],
                    'error_count': 0, 'savings_estimate': '$0'
                }
                urllib.request.urlopen(
                    urllib.request.Request(
                        f"{API_BASE}/api/report",
                        data=json.dumps(err_report).encode(),
                        headers={'Content-Type': 'application/json'}
                    ), timeout=10
                )
            except:
                pass
            file_path.unlink(missing_ok=True)

    print(f"[Cron] Done. Processed {processed} job(s).")

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--daemon', action='store_true', help='Run continuously')
    ap.add_argument('--once', action='store_true', help='Process one batch and exit')
    args = ap.parse_args()

    if args.daemon:
        while True:
            run()
            time.sleep(60)
    else:
        run()

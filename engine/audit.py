# MedBill Auditor — Audit Engine
# OCR → CMS compare → LLM overlay → Report generator
import os, sys, json, re, subprocess, tempfile, urllib.request, time
from pathlib import Path

CONFIG = {
    'api_base': os.environ.get('API_BASE', 'https://medbill.ai'),
    'llm_cli': os.environ.get('LLM_CLI', 'pi'),
    'max_concurrent': int(os.environ.get('MAX_CONCURRENT', '3')),
}

# --- CMS Rate Estimates (CPT → $) ---
CMS_RATES = {
    '99201':45,'99202':77,'99203':110,'99204':167,'99205':211,'99211':22,'99212':45,
    '99213':76,'99214':111,'99215':150,'99221':102,'99222':143,'99223':189,
    '99231':41,'99232':74,'99233':104,'99281':73,'99282':106,'99283':157,'99284':266,'99285':377,
    '93000':28,'71045':23,'71046':31,'72141':140,'72142':170,'74176':220,'74177':280,'74178':350
}

class OCRProcessor:
    def extract(self, path: Path) -> dict:
        ext = path.suffix.lower()
        if ext == '.pdf': return self._extract_pdf(path)
        elif ext in ('.jpg','.jpeg','.png'): return self._extract_image(path)
        raise ValueError(f"Unsupported: {ext}")

    def _extract_pdf(self, path: Path) -> dict:
        try:
            import pdfplumber
            texts = []
            with pdfplumber.open(str(path)) as pdf:
                for p in pdf.pages: texts.append(p.extract_text() or '')
            raw = '\n'.join(texts)
            return {'raw_text': raw, 'pages': len(texts), 'is_scanned': len(raw.strip()) < 50}
        except ImportError:
            try:
                r = subprocess.run(['pdftotext','-layout',str(path),'-'], capture_output=True, text=True, timeout=30)
                return {'raw_text': r.stdout, 'pages': r.stdout.count('\f')+1 if r.stdout else 0, 'is_scanned': len(r.stdout.strip()) < 50}
            except: return {'raw_text': '', 'pages': 0, 'is_scanned': True}

    def _extract_image(self, path: Path) -> dict:
        try:
            import pytesseract
            from PIL import Image
            raw = pytesseract.image_to_string(Image.open(str(path)))
            return {'raw_text': raw, 'pages': 1, 'is_scanned': True}
        except ImportError:
            try:
                r = subprocess.run(['tesseract',str(path),'stdout','-l','eng'], capture_output=True, text=True, timeout=60)
                return {'raw_text': r.stdout, 'pages': 1, 'is_scanned': True}
            except: return {'raw_text': '', 'pages': 0, 'is_scanned': True, 'error': 'OCR failed'}

class LLMExtractor:
    def __init__(self, cli=CONFIG['llm_cli']): self.cli = cli
    def extract(self, ocr: dict) -> dict:
        raw = ocr.get('raw_text','')
        if not raw.strip(): return {'services':[], 'total_billed':None}
        prompt = f"""Extract structured data from this medical bill. Return ONLY JSON.
Fields: services (array of {{description, cpt_code, icd10_code, modifier, billed_amount, units, date_of_service}}), total_billed, insurance_paid, patient_responsibility, provider_name, bill_date, account_number, payer_name.
Bill:\n---\n{raw[:8000]}\n---"""
        try:
            r = subprocess.run([self.cli,'--print',prompt], capture_output=True, text=True, timeout=60)
            m = re.search(r'\{.*\}', r.stdout.strip(), re.DOTALL)
            if m: return json.loads(m.group())
        except: pass
        return {'services':[], 'total_billed':None}

class CMSComparator:
    def compare(self, services: list) -> list:
        results = []
        for svc in services:
            cpt, billed, units = svc.get('cpt_code',''), svc.get('billed_amount',0), svc.get('units',1)
            if not cpt or not billed: continue
            rate = CMS_RATES.get(cpt)
            if rate is None: continue
            expected = rate * units; diff = billed - expected
            results.append({
                'service': svc.get('description','Unknown'), 'cpt': cpt,
                'billed': round(billed,2), 'cms_rate': round(expected,2),
                'difference': round(diff,2), 'pct_over': round(diff/expected*100 if expected>0 else 0, 1),
                'flagged': diff/expected > 0.2 if expected>0 else False
            })
        return results

class LLMAuditor:
    def __init__(self, cli=CONFIG['llm_cli']): self.cli = cli
    def audit(self, bill_text, structured, rate_comparisons):
        services = json.dumps(structured.get('services',[]), indent=2)
        flagged = json.dumps([r for r in rate_comparisons if r.get('flagged')], indent=2)
        prompt = f"""Analyze this medical bill for coding errors. Return ONLY a JSON array.
Each: {{"type":("upcoding"|"unbundling"|"duplicate"|"modifier_error"|"balance_billing"|"denial_code_error"|"medical_necessity"),"severity":"high"|"medium"|"low","code":str|null,"amount":float,"description":str,"detail":str,"citation":str|null}}
Bill:\n{bill_text[:4000]}\nServices:\n{services}\nFlagged rates:\n{flagged}"""
        try:
            r = subprocess.run([self.cli,'--print',prompt], capture_output=True, text=True, timeout=90)
            m = re.search(r'\[.*\]', r.stdout.strip(), re.DOTALL)
            if m:
                valid = {'upcoding','unbundling','duplicate','modifier_error','balance_billing','denial_code_error','medical_necessity','mue_violation'}
                return [f for f in json.loads(m.group()) if isinstance(f,dict) and f.get('type') in valid][:20]
        except: pass
        return []

class ReportGenerator:
    def generate(self, structured, rate_comparisons, findings):
        total = sum(f.get('amount',0) for f in findings if f.get('type')!='error') + sum(r.get('difference',0) for r in rate_comparisons if r.get('flagged'))
        all_f = findings + [{'type':'cms_overcharge','severity':'medium' if r.get('pct_over',0)>50 else 'low','code':r.get('cpt',''),'amount':round(r.get('difference',0),2),'description':f"Billed ${r['billed']:,.2f} for {r['service']} vs CMS ${r['cms_rate']:,.2f}",'detail':f"Over CMS rate by {r['pct_over']:.0f}%",'citation':'CMS Fee Schedule'} for r in rate_comparisons if r.get('flagged')]
        all_f.sort(key=lambda f: {'high':0,'medium':1,'low':2}.get(f.get('severity','low'),99))
        return {
            'findings': all_f, 'rate_comparisons': rate_comparisons,
            'dispute_letter': self._dispute_letter(structured, all_f) if all_f else None,
            'phone_script': self._phone_script(all_f) if all_f else None,
            'billed_amount': f"${structured.get('total_billed',0):,.2f}" if structured.get('total_billed') else None,
            'service_count': len(structured.get('services',[])), 'error_count': len(all_f),
            'savings_estimate': f"${max(0,total):,.0f}"
        }

    def _dispute_letter(self, s, findings):
        p = s.get('provider_name','[Provider]'); a = s.get('account_number','[Account #]'); t = s.get('total_billed',0)
        items = ''.join(f"{i}. {f['description']}\n   Code: {f.get('code','N/A')}\n   Impact: ${f['amount']:,.2f}\n   {f.get('detail','')}\n\n" for i,f in enumerate(findings,1) if f.get('type')!='error')
        return f"[Date]\n\n{p}\n[Address]\nRE: Dispute — Account #{a}\n\nTo Whom It May Concern:\n\nI am disputing charges on account #{a} in the amount of ${t:,.2f}. After audit:\n\n{items}Total disputed: ${sum(f.get('amount',0) for f in findings if f.get('type')!='error'):,.2f}\n\nUnder the No Surprises Act, I request a formal review. Please respond within 30 days.\n\nSincerely,\n[Your Name]"

    def _phone_script(self, findings):
        items = ''.join(f"- {f['description']} (${f['amount']:,.2f})\n  {f.get('detail','')}\n\n" for f in findings if f.get('type')!='error')
        return f"PHONE SCRIPT\n\n1. Call billing: 'Hello, I have questions about my bill.'\n2. Present findings:\n{items}3. Request correction.\n4. Escalate: 'Can I speak with a coding supervisor?'"

def run_cron():
    print(f"[Cron] Starting")
    ocr = OCRProcessor(); extractor = LLMExtractor(); cms = CMSComparator(); auditor = LLMAuditor(); reporter = ReportGenerator()
    processed = 0
    while processed < CONFIG['max_concurrent']:
        try:
            r = urllib.request.urlopen(f"{CONFIG['api_base']}/api/queue/next", timeout=10)
            data = json.loads(r.read())
        except: break
        if not data or not data.get('job'): break
        job = data['job']; jid = job['id']
        print(f"[Cron] Job: {jid}")
        if not data.get('download_url'): continue
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=f".{job.get('fileType','pdf')}", delete=False)
            urllib.request.urlretrieve(data['download_url'], tmp.name)
            file_path = Path(tmp.name)
            print(f"[Cron] OCR..."); ocr_result = ocr.extract(file_path)
            print(f"[Cron] Extract..."); structured = extractor.extract(ocr_result)
            print(f"[Cron] CMS..."); rates = cms.compare(structured.get('services',[]))
            print(f"[Cron] LLM..."); findings = auditor.audit(ocr_result.get('raw_text',''), structured, rates)
            print(f"[Cron] Report..."); report = reporter.generate(structured, rates, findings)
            file_path.unlink(missing_ok=True)
            payload = json.dumps({'job_id': jid, **report}).encode()
            req = urllib.request.Request(f"{CONFIG['api_base']}/api/report", data=payload, headers={'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                print(f"[Cron] Submitted ({resp.status})")
            processed += 1
        except Exception as e:
            print(f"[Cron] Failed: {e}")
            try:
                urllib.request.urlopen(urllib.request.Request(f"{CONFIG['api_base']}/api/report", data=json.dumps({'job_id':jid,'findings':[{'type':'error','severity':'low','amount':0,'description':f'Pipeline error: {e}'}],'error_count':0,'savings_estimate':'$0'}).encode(), headers={'Content-Type':'application/json'}), timeout=10)
            except: pass
    print(f"[Cron] Done. Processed {processed}.")

if __name__ == '__main__':
    import argparse; p=argparse.ArgumentParser()
    p.add_argument('--cron', action='store_true'); p.add_argument('--file', type=str); p.add_argument('--once', action='store_true')
    args = p.parse_args()
    if args.cron:
        while True:
            run_cron()
            time.sleep(int(os.environ.get('QUEUE_POLL_SECONDS','30')))
    elif args.once: run_cron()
    elif args.file: from pathlib import Path; ocr=OCRProcessor(); ext=LLMExtractor(); cms=CMSComparator(); aud=LLMAuditor(); rep=ReportGenerator(); o=ocr.extract(Path(args.file)); s=ext.extract(o); r=cms.compare(s.get('services',[])); f=aud.audit(o.get('raw_text',''),s,r); print(json.dumps(rep.generate(s,r,f),indent=2))
    else: p.print_help()

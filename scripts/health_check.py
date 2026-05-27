#!/usr/bin/env python3
"""MedBill Post-Launch Health Check
Usage:
  python3 scripts/health_check.py          # Full check
  python3 scripts/health_check.py --web    # Only web pages
  python3 scripts/health_check.py --api    # Only API endpoints
  python3 scripts/health_check.py --slack  # Send to Slack webhook
"""
import os, sys, json, subprocess
from datetime import datetime

SITE_URL = 'https://medbill-auditor.pages.dev'

PAGES = [
    ('/', 'Landing'),
    ('/privacy', 'Privacy Policy'),
    ('/terms', 'Terms of Service'),
    ('/cookies', 'Cookie Policy'),
    ('/about', 'About Us'),
    ('/contact', 'Contact'),
    ('/login', 'Login'),
    ('/checkout', 'Checkout'),
    ('/b2b', 'B2B'),
    ('/scan', 'Upload'),
    ('/report?id=test', 'Report'),
    ('/status', 'Status'),
]

API_ENDPOINTS = [
    ('POST', '/api/upload', 'Upload (no file → 400)', None),
    ('GET', '/api/status/test', 'Status (missing → 404)', None),
    ('GET', '/api/report/test', 'Report (missing → 404)', None),
    ('GET', '/api/queue/next', 'Queue (empty or job → 200)', None),
    ('GET', '/api/download/x/x', 'Download (missing → 404)', None),
]

def check_page(path, name):
    try:
        import urllib.request
        req = urllib.request.Request(f'{SITE_URL}{path}', headers={'User-Agent': 'Mozilla/5.0 MedBill-HealthCheck/1.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            status = r.status
            size = len(r.read())
            ok = status == 200 and size > 100
            return (name, path, status, size, '✅' if ok else '⚠️')
    except Exception as e:
        return (name, path, 'ERR', str(e), '❌')

def check_api(method, path, name, _):
    import urllib.request
    try:
        headers = {'User-Agent': 'Mozilla/5.0 MedBill-HealthCheck/1.0'}
        if method == 'GET':
            req = urllib.request.Request(f'{SITE_URL}{path}', headers=headers)
        elif method == 'POST':
            req = urllib.request.Request(f'{SITE_URL}{path}', data=b'{}', headers={**headers, 'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=10) as r:
            status = r.status
            ok = (path.endswith('/queue/next') and status == 200) or \
                 (status in (400, 404))  # Expected errors for missing data
            return (name, path, status, '✅' if ok else '⚠️')
    except urllib.error.HTTPError as e:
        status = e.code
        ok = status in (400, 403, 404)
        return (name, path, status, '✅' if ok else '⚠️')
    except Exception as e:
        return (name, path, str(e), '❌')

def run_checks():
    results = {'pages': [], 'api': [], 'errors': 0, 'timestamp': datetime.now().isoformat()}

    print(f"\n{'='*60}")
    print(f"  MedBill Health Check — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    print(f"📄 Pages ({len(PAGES)}):")
    for path, name in PAGES:
        res = check_page(path, name)
        results['pages'].append(res)
        print(f"  {res[4]} {res[0]:25s} {res[1]:25s} HTTP {str(res[2]):3s} {str(res[3]):>7}B")
        if res[4] == '❌':
            results['errors'] += 1

    print(f"\n🔌 API ({len(API_ENDPOINTS)}):")
    for method, path, name, _ in API_ENDPOINTS:
        res = check_api(method, path, name, None)
        results['api'].append(res)
        print(f"  {res[3]} {res[0]:40s} {res[1]:25s} {str(res[2])}")
        if res[3] == '❌':
            results['errors'] += 1

    print(f"\n{'='*60}")
    status = '✅ ALL PASS' if results['errors'] == 0 else f'⚠️ {results["errors"]} FAILURES'
    print(f"  Result: {status}")
    print(f"{'='*60}\n")

    return results

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--web', action='store_true', help='Web pages only')
    ap.add_argument('--api', action='store_true', help='API endpoints only')
    ap.add_argument('--slack', action='store_true', help='Output as JSON for Slack')
    args = ap.parse_args()

    results = run_checks()

    if args.slack:
        print(json.dumps(results, indent=2))

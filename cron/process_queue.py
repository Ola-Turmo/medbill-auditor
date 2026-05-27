#!/usr/bin/env python3
"""MedBill — Cron Queue Processor"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from engine.audit import run_cron; run_cron()

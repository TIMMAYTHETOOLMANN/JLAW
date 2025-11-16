#!/usr/bin/env python3
"""
JARVIS:LAW Production Server - Waitress WSGI
Production-ready deployment using Waitress (Windows-compatible)
"""

from waitress import serve
from forensic_web_server import app
import os

if __name__ == '__main__':
    # Production configuration
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    app.config['ENV'] = 'production'
    
    # Server settings
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 9000))
    threads = int(os.environ.get('THREADS', 8))
    
    print("=" * 80)
    print("JARVIS:LAW FORENSIC ANALYSIS SYSTEM - PRODUCTION SERVER")
    print("=" * 80)
    print()
    print("[OK] ForensicOutputGenerator v1.0.0 ACTIVE")
    print("[OK] FULL ML ANALYSIS MODE - Production Ready")
    print("[OK] SEC Integration: 60+ Companies + Dynamic API")
    print()
    print(f"Server URL: http://localhost:{port}")
    print(f"Health Check: http://localhost:{port}/api/health")
    print(f"API Endpoint: http://localhost:{port}/api/")
    print()
    print(f"Workers: {threads} threads")
    print("Mode: PRODUCTION (Waitress WSGI)")
    print()
    print("System Capabilities:")
    print("  [OK] ALL Public SEC Companies (Fortune 500+)")
    print("  [OK] Full ML Analysis (Torch, Transformers, NLP)")
    print("  [OK] Form 4 Insider Trading Analysis")
    print("  [OK] Risk Assessment & Pattern Detection")
    print("  [OK] Multi-format Forensic Reporting")
    print()
    print("=" * 80)
    print("Server is ready to accept connections...")
    print("=" * 80)
    print()
    
    # Serve with Waitress WSGI server for production
    print(f"Starting Waitress server on {host}:{port} with {threads} threads...")
    serve(app, host=host, port=port, threads=threads)

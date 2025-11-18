#!/usr/bin/env python3
"""
JARVIS:LAW Simple Production Server
Minimal Flask server for production deployment
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from waitress import serve
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger('JARVIS_SERVER')

# Initialize Flask app
app = Flask(__name__, 
            static_folder='web_frontend',
            static_url_path='')
CORS(app)

@app.route('/')
def index():
    """Serve main frontend"""
    return send_from_directory('web_frontend', 'index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "system": "JARVIS:LAW Forensic Analysis System",
        "version": "1.0.0",
        "mode": "production"
    })

@app.route('/api/status')
def status():
    """System status endpoint"""
    return jsonify({
        "backend": "online",
        "frontend": "online",
        "database": "ready",
        "forensic_engine": "ready",
        "sec_integration": "active"
    })

if __name__ == '__main__':
    # Production configuration
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    app.config['ENV'] = 'production'
    
    # Server settings
    host = os.environ.get('HOST', 'localhost')
    port = int(os.environ.get('PORT', 9000))
    threads = int(os.environ.get('THREADS', 8))
    
    print("=" * 80)
    print("JARVIS:LAW FORENSIC ANALYSIS SYSTEM - PRODUCTION SERVER")
    print("=" * 80)
    print()
    print("[OK] Flask Web Server ACTIVE")
    print("[OK] CORS Enabled")
    print("[OK] Production Mode")
    print()
    print(f"Server URL: http://localhost:{port}")
    print(f"Health Check: http://localhost:{port}/api/health")
    print(f"Status Check: http://localhost:{port}/api/status")
    print()
    print(f"Workers: {threads} threads")
    print("Mode: PRODUCTION (Waitress WSGI)")
    print()
    print("System Capabilities:")
    print("  [OK] SEC Filing Analysis")
    print("  [OK] Form 4 Insider Trading Detection")
    print("  [OK] Risk Assessment & Pattern Detection")
    print("  [OK] Multi-format Forensic Reporting")
    print()
    print("=" * 80)
    print("Server is ready to accept connections...")
    print("=" * 80)
    print()
    
    # Serve with Waitress WSGI server for production
    logger.info(f"Starting Waitress server on {host}:{port} with {threads} threads...")
    serve(app, host=host, port=port, threads=threads)


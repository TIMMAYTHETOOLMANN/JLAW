"""
Minimal test server to diagnose the issue
"""
from flask import Flask
import sys

print("Creating Flask app...", flush=True)
app = Flask(__name__)

@app.route('/')
def hello():
    return "JARVIS:LAW Test Server is Running!"

@app.route('/api/health')
def health():
    return {"status": "ok", "message": "Test server operational"}

if __name__ == '__main__':
    print("Starting minimal test server on port 9000...", flush=True)
    try:
        app.run(host='0.0.0.0', port=9000, debug=True, use_reloader=False)
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        sys.exit(1)


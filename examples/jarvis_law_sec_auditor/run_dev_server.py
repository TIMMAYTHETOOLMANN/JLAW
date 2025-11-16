"""
Simple Flask development server for quick testing
"""
from forensic_web_server import app
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9000))
    
    print("=" * 80)
    print("JARVIS:LAW FORENSIC ANALYSIS SYSTEM - DEVELOPMENT SERVER")
    print("=" * 80)
    print()
    print(f"Server URL: http://localhost:{port}")
    print(f"Health Check: http://localhost:{port}/api/health")
    print()
    print("Mode: DEVELOPMENT (Flask built-in server)")
    print("Press Ctrl+C to stop")
    print("=" * 80)
    print()
    
    # Run Flask development server
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


"""
Debug wrapper for production_waitress.py to capture errors
"""
import traceback
import sys

try:
    print("Starting server with error capture...")
    from waitress import serve
    from forensic_web_server import app
    import os
    
    # Production configuration
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    app.config['ENV'] = 'production'
    
    # Server settings
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 9000))
    threads = int(os.environ.get('THREADS', 8))
    
    print("=" * 80)
    print("JARVIS:LAW FORENSIC ANALYSIS SYSTEM - PRODUCTION SERVER (DEBUG MODE)")
    print("=" * 80)
    print()
    print(f"Server URL: http://localhost:{port}")
    print(f"Workers: {threads} threads")
    print()
    
    # Serve with Waitress WSGI server for production
    print(f"Starting Waitress server on {host}:{port} with {threads} threads...")
    serve(app, host=host, port=port, threads=threads)
    
except Exception as e:
    print("\n" + "=" * 80)
    print("ERROR STARTING SERVER:")
    print("=" * 80)
    print(f"\nError Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")
    print("\nFull Traceback:")
    traceback.print_exc()
    print("\n" + "=" * 80)
    sys.exit(1)


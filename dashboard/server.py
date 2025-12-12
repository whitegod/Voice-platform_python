"""
Professional Dashboard Server for VaaS Platform
Run with: python dashboard/server.py
Then open: http://localhost:3000
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 3000
DIRECTORY = Path(__file__).parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def end_headers(self):
        # Enable CORS for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def do_GET(self):
        # Serve app.html as default
        if self.path == '/':
            self.path = '/app.html'
        return super().do_GET()

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    
    print("\n" + "="*70)
    print(" "*15 + "VaaS Enterprise Dashboard")
    print("="*70)
    print()
    print("  🌐 Dashboard URL: http://localhost:3000")
    print("  📱 Access from: Your browser")
    print()
    print("  ✓ Professional UI")
    print("  ✓ Audio upload & testing")
    print("  ✓ Text upload & processing")
    print("  ✓ Real-time conversation interface")
    print("  ✓ Domain management")
    print("  ✓ Analytics & insights")
    print()
    print("  ⚠️  Make sure VaaS platform is running on port 8000!")
    print()
    print("  Press Ctrl+C to stop the dashboard")
    print("="*70)
    print()
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✓ Dashboard stopped gracefully")
            print()


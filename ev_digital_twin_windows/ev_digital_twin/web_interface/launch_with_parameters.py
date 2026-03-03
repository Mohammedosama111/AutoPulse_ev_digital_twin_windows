#!/usr/bin/env python3
"""
Launch script for EV Digital Twin with Parameter Configuration Interface
-----------------------------------------------------------------------
This script launches the web interface with the new parameter setup functionality.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import time
from pathlib import Path

def main():
    """Launch the EV Digital Twin web interface with parameter configuration."""
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Change to the web interface directory
    os.chdir(script_dir)
    
    # Set up the HTTP server
    PORT = 8080
    
    # Create a custom handler to serve files
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Add CORS headers to allow cross-origin requests
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
        
        def do_GET(self):
            # Serve launcher.html as the default page
            if self.path == '/':
                self.path = '/launcher.html'
            return super().do_GET()
    
    try:
        # Create the server
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print("=" * 60)
            print("🚗 Electric Vehicle Digital Twin - Web Interface")
            print("=" * 60)
            print(f"📍 Server running at: http://localhost:{PORT}")
            print(f"📁 Serving files from: {script_dir}")
            print("=" * 60)
            print("🎯 Features:")
            print("   • Parameter Configuration Interface")
            print("   • Vehicle Presets (Sedan, SUV, Sports, Commercial)")
            print("   • Custom Battery & Motor Configuration")
            print("   • Real-time Simulation Dashboard")
            print("   • Advanced Analytics & Reporting")
            print("=" * 60)
            print("🌐 Opening browser...")
            print("💡 Use Ctrl+C to stop the server")
            print("=" * 60)
            
            # Open the browser
            webbrowser.open(f'http://localhost:{PORT}')
            
            # Start the server
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        print("👋 Thank you for using EV Digital Twin!")
        
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use.")
            print("💡 Try using a different port or stop the existing server.")
            print("🔧 You can also manually open: http://localhost:8080/launcher.html")
        else:
            print(f"❌ Error starting server: {e}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 
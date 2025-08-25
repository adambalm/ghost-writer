#!/usr/bin/env python3
"""
Simple HTTPS server for iOS certificate installation with correct MIME types.
Serves .mobileconfig and .der files with proper Content-Type headers.
"""

from flask import Flask, send_file, abort
import os
import ssl
from pathlib import Path

app = Flask(__name__)

# Base directory for certificates
CERT_DIR = Path(__file__).parent / 'ssl-certs'

# MIME type mappings for iOS certificate installation
MIME_TYPES = {
    '.mobileconfig': 'application/x-apple-aspen-config',
    '.der': 'application/pkix-cert',
    '.cer': 'application/pkix-cert',
    '.crt': 'application/pkix-cert',
    '.pem': 'application/x-pem-file'
}

@app.route('/ssl-certs/<filename>')
def serve_cert(filename):
    """Serve certificate files with correct MIME types."""
    file_path = CERT_DIR / filename
    
    # Security: prevent directory traversal
    if '..' in filename or '/' in filename:
        abort(403)
    
    # Check if file exists
    if not file_path.exists() or not file_path.is_file():
        abort(404)
    
    # Get appropriate MIME type
    suffix = file_path.suffix.lower()
    mime_type = MIME_TYPES.get(suffix, 'application/octet-stream')
    
    # Serve file with correct MIME type
    return send_file(
        file_path,
        mimetype=mime_type,
        as_attachment=False,  # Allow browser to handle directly
        download_name=filename
    )

@app.route('/')
def index():
    """Simple index page with links to certificates."""
    host = os.environ.get('CERT_SERVER_HOST', '100.111.114.84')
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ghost Writer CA Installation</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto; }}
            h1 {{ color: #333; }}
            .cert-link {{ display: block; padding: 15px; margin: 10px 0; background: #007AFF; color: white; text-decoration: none; border-radius: 10px; text-align: center; }}
            .cert-link:hover {{ background: #0051D5; }}
            .instructions {{ background: #f5f5f5; padding: 15px; border-radius: 10px; margin: 20px 0; }}
            code {{ background: #fff; padding: 2px 5px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <h1>🔐 Ghost Writer CA Installation</h1>
        
        <div class="instructions">
            <h2>iOS One-Tap Install</h2>
            <p>Tap the link below on your iPhone to install the Ghost Writer development CA:</p>
        </div>
        
        <a href="/ssl-certs/ed-dev-root.mobileconfig" class="cert-link">
            📱 Install Configuration Profile
        </a>
        
        <a href="/ssl-certs/ca-certificate.der" class="cert-link" style="background: #666;">
            🔒 Alternative: Install DER Certificate
        </a>
        
        <div class="instructions">
            <h3>After Installation:</h3>
            <ol>
                <li>Go to Settings → General → VPN & Device Management</li>
                <li>Tap "Ed Dev Root CA" under Configuration Profile</li>
                <li>Tap "Install" and enter your passcode</li>
                <li>Go to Settings → General → About → Certificate Trust Settings</li>
                <li>Enable "Full Trust" for "Ed Dev Root CA"</li>
            </ol>
        </div>
        
        <div class="instructions" style="background: #fff3cd;">
            <h3>Direct URLs:</h3>
            <code>https://{host}:8443/ssl-certs/ed-dev-root.mobileconfig</code><br><br>
            <code>https://{host}:8443/ssl-certs/ca-certificate.der</code>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    # SSL configuration
    ssl_cert = CERT_DIR / 'server-certificate.pem'
    ssl_key = CERT_DIR / 'server-private-key.pem'
    
    if not ssl_cert.exists() or not ssl_key.exists():
        print(f"❌ SSL certificates not found in {CERT_DIR}")
        print("Run: cd ssl-certs && ./cert-helper.sh generate-server")
        exit(1)
    
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(ssl_cert, ssl_key)
    
    print("🔐 Ghost Writer Certificate Server")
    print("=" * 40)
    print(f"📱 iOS Profile: https://100.111.114.84:8443/ssl-certs/ed-dev-root.mobileconfig")
    print(f"🔒 DER Certificate: https://100.111.114.84:8443/ssl-certs/ca-certificate.der")
    print(f"🌐 Web Interface: https://100.111.114.84:8443/")
    print("=" * 40)
    
    # Run server
    app.run(
        host='0.0.0.0',
        port=8443,
        ssl_context=context,
        debug=False
    )
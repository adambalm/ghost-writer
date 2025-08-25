#!/bin/bash
# Quick Start HTTPS Demo Server

set -e

echo "🔐 Ghost Writer HTTPS Demo Starter"
echo "=================================="

# Check if certificates exist
if [ ! -f "ssl-certs/ca-certificate.pem" ] || [ ! -f "ssl-certs/server-certificate.pem" ]; then
    echo "❌ SSL certificates not found!"
    echo "💡 Run certificate generation first:"
    echo "    cd ssl-certs && ./cert-helper.sh generate-ca && ./cert-helper.sh generate-server"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "💡 Create it with: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Show certificate info
echo "📋 Certificate Information:"
cd ssl-certs && ./cert-helper.sh info && cd ..

echo ""
echo "🚀 Starting HTTPS server..."
echo "📱 Access URL: https://100.111.114.84:8443"
echo "🔒 CA Certificate to install on devices: ssl-certs/ca-certificate.pem"
echo "📖 iPhone setup guide: IPHONE_CERTIFICATE_INSTALL.md"
echo ""
echo "Press Ctrl+C to stop server"
echo "=================================="

# Activate virtual environment and start server
source .venv/bin/activate && python web_viewer_with_auth_https.py
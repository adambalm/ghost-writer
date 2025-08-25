#!/bin/bash
# SSL Certificate Helper Script
# Uses environment variables for security

set -e  # Exit on any error

# Load environment variables
if [ -f "../.env" ]; then
    export $(grep -v '^#' ../.env | xargs)
else
    echo "❌ .env file not found. Please run from ssl-certs directory."
    exit 1
fi

# Check if CA password is set
if [ -z "$SSL_CA_PASSWORD" ]; then
    echo "❌ SSL_CA_PASSWORD not set in .env file"
    exit 1
fi

case "$1" in
    "generate-ca")
        echo "🔐 Generating Certificate Authority..."
        openssl genpkey -algorithm RSA -out ca-private-key.pem -pkcs8 -aes256 -pass pass:$SSL_CA_PASSWORD
        openssl req -new -x509 -key ca-private-key.pem -out ca-certificate.pem -days 3650 -config ca.conf -passin pass:$SSL_CA_PASSWORD
        echo "✅ CA certificate generated: ca-certificate.pem"
        ;;
    
    "generate-server")
        echo "🔑 Generating server certificate..."
        openssl genpkey -algorithm RSA -out server-private-key.pem
        openssl req -new -key server-private-key.pem -out server.csr -config server.conf
        openssl x509 -req -in server.csr -CA ca-certificate.pem -CAkey ca-private-key.pem -CAcreateserial -out server-certificate.pem -days 365 -extensions server_cert -extfile server-extensions.conf -passin pass:$SSL_CA_PASSWORD
        echo "✅ Server certificate generated: server-certificate.pem"
        ;;
    
    "renew-server")
        echo "🔄 Renewing server certificate..."
        openssl req -new -key server-private-key.pem -out server.csr -config server.conf
        openssl x509 -req -in server.csr -CA ca-certificate.pem -CAkey ca-private-key.pem -CAcreateserial -out server-certificate.pem -days 365 -extensions server_cert -extfile server-extensions.conf -passin pass:$SSL_CA_PASSWORD
        echo "✅ Server certificate renewed"
        ;;
    
    "verify")
        echo "🔍 Verifying certificate chain..."
        openssl verify -CAfile ca-certificate.pem server-certificate.pem
        ;;
    
    "info")
        echo "📋 Certificate Information:"
        echo "CA Certificate:"
        openssl x509 -in ca-certificate.pem -noout -subject -issuer -dates
        echo ""
        echo "Server Certificate:"
        openssl x509 -in server-certificate.pem -noout -subject -issuer -dates
        echo ""
        echo "Subject Alternative Names:"
        openssl x509 -in server-certificate.pem -text -noout | grep -A 5 "Subject Alternative Name"
        ;;
    
    *)
        echo "SSL Certificate Helper"
        echo "Usage: $0 {generate-ca|generate-server|renew-server|verify|info}"
        echo ""
        echo "Commands:"
        echo "  generate-ca     Generate Certificate Authority"
        echo "  generate-server Generate server certificate"
        echo "  renew-server    Renew server certificate (1 year)"
        echo "  verify          Verify certificate chain"
        echo "  info            Show certificate information"
        exit 1
        ;;
esac
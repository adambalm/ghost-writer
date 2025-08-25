# HTTPS Setup Documentation - Ghost Writer

## Overview
This document explains the complete HTTPS setup implemented to resolve Safari HTTPS-Only Mode issues on iOS devices. The solution uses self-signed certificates with a custom Certificate Authority (CA).

## Problem Statement
- **Issue**: Safari on iPhone with HTTPS-Only Mode enabled refuses to load `http://100.111.114.84`
- **Root Cause**: iOS Safari HTTPS-Only Mode cannot make exceptions for individual domains
- **Solution**: Implement HTTPS with trusted certificates

## Architecture Decision
**Chosen Approach**: Self-Signed Certificate Authority (CA)

**Rationale**:
- ✅ **Best Practice** for development environments
- ✅ **Full Control** - no external dependencies
- ✅ **Educational Value** - complete understanding of PKI
- ✅ **Reliability** - works offline and has no service dependencies
- ✅ **Security** - just as secure as commercial CAs for private networks
- ✅ **Industry Standard** - used by Docker, Kubernetes, and enterprise tools

**Alternative Considered**: Tailscale certificates
- ❌ **Rejected** because it required sudo setup and creates service dependency

## Implementation Steps

### 1. Certificate Authority Creation
```bash
cd /home/ed/ghost-writer/ssl-certs

# Use the secure helper script (reads password from .env)
./cert-helper.sh generate-ca
```

### 2. Server Certificate Creation  
```bash
cd /home/ed/ghost-writer/ssl-certs

# Use the secure helper script
./cert-helper.sh generate-server
```

### Alternative: Manual Commands (Advanced Users)
```bash
# Set environment variable first
export $(grep SSL_CA_PASSWORD ../.env | xargs)

# Generate CA private key (password from environment)
openssl genpkey -algorithm RSA -out ca-private-key.pem -pkcs8 -aes256 -pass pass:$SSL_CA_PASSWORD

# Create CA certificate
openssl req -new -x509 -key ca-private-key.pem -out ca-certificate.pem -days 3650 -config ca.conf -passin pass:$SSL_CA_PASSWORD

# Generate server private key (unencrypted for server use)
openssl genpkey -algorithm RSA -out server-private-key.pem

# Create certificate signing request
openssl req -new -key server-private-key.pem -out server.csr -config server.conf

# Sign server certificate with CA
openssl x509 -req -in server.csr -CA ca-certificate.pem -CAkey ca-private-key.pem -CAcreateserial -out server-certificate.pem -days 365 -extensions server_cert -extfile server-extensions.conf -passin pass:$SSL_CA_PASSWORD
```

### 3. Flask HTTPS Integration
- **Development**: `web_viewer_with_auth_https.py` (port 8443)
- **Production**: `web_viewer_https_production.py` (port 443, requires sudo)

## File Locations

### SSL Certificates
```
/home/ed/ghost-writer/ssl-certs/
├── ca-certificate.pem          # Root CA certificate (install on iPhone)
├── ca-private-key.pem          # CA private key (keep secure)
├── server-certificate.pem     # Server certificate
├── server-private-key.pem     # Server private key
├── ca.conf                     # CA configuration
├── server.conf                 # Server certificate configuration
└── server-extensions.conf     # Server certificate extensions
```

### Applications
```
/home/ed/ghost-writer/
├── web_viewer_with_auth_https.py     # Development HTTPS (port 8443)
└── web_viewer_https_production.py   # Production HTTPS (port 443)
```

## iPhone CA Installation Instructions

### Step 1: Transfer CA Certificate to iPhone
**Method 1 - Email**:
1. Email `ca-certificate.pem` to yourself
2. Open the attachment on your iPhone
3. Tap "Install Profile"

**Method 2 - AirDrop** (macOS):
1. AirDrop `ca-certificate.pem` to your iPhone
2. Accept the file transfer
3. Tap the notification to install

**Method 3 - Cloud Storage**:
1. Upload `ca-certificate.pem` to iCloud/Dropbox/Google Drive
2. Download on iPhone using the respective app
3. Tap "Share" → "Install Profile"

### Step 2: Install Certificate Profile
1. iPhone will show "Install Profile" dialog
2. Tap "Install" (top right)
3. Enter your iPhone passcode if prompted
4. Tap "Install" again to confirm
5. Tap "Done"

### Step 3: Enable Certificate Trust
1. Open **Settings** → **General** → **About**
2. Scroll down to **Certificate Trust Settings**
3. Find "Ghost Writer CA"
4. **Toggle ON** the switch next to it
5. Tap "Continue" on the warning dialog

### Step 4: Verify Installation
1. Open Safari on iPhone
2. Navigate to `https://100.111.114.84` (or `https://100.111.114.84:8443` for development)
3. You should see the site load with a secure lock icon ✅

## Testing Commands

### Verify Certificate Chain
```bash
# Verify certificate chain is valid
openssl verify -CAfile ca-certificate.pem server-certificate.pem

# Expected output: server-certificate.pem: OK
```

### Test HTTPS Connectivity
```bash
# Test with certificate verification
curl --cacert ssl-certs/ca-certificate.pem https://100.111.114.84:8443/status

# Test without certificate verification (should work but not recommended)
curl -k https://100.111.114.84:8443/status

# Test SSL handshake
openssl s_client -connect 100.111.114.84:8443 -servername 100.111.114.84
```

### Test Certificate Details
```bash
# View server certificate details
openssl x509 -in ssl-certs/server-certificate.pem -text -noout

# Check Subject Alternative Names
openssl x509 -in ssl-certs/server-certificate.pem -text -noout | grep -A 10 "Subject Alternative Name"
```

## Running the HTTPS Server

### Development Mode (Port 8443)
```bash
cd /home/ed/ghost-writer
source .venv/bin/activate
python web_viewer_with_auth_https.py
```
- **Access**: `https://100.111.114.84:8443`
- **No sudo required**
- **Includes debug features**

### Production Mode (Port 443)
```bash
cd /home/ed/ghost-writer
source .venv/bin/activate
sudo python web_viewer_https_production.py
```
- **Access**: `https://100.111.114.84`
- **Requires sudo** (for ports 80/443)
- **HTTP redirect** from port 80 to 443
- **No debug features** (production security)

## Security Considerations

### CA Private Key Security
- **Password**: Stored in `.env` as `SSL_CA_PASSWORD` (never committed to git)
- **Location**: `/home/ed/ghost-writer/ssl-certs/ca-private-key.pem`
- **Permissions**: `600` (owner read/write only)
- **Usage**: Only needed when signing new certificates
- **Access**: Use `cert-helper.sh` script for secure operations

### Certificate Validity
- **CA Certificate**: 10 years (2025-2035)
- **Server Certificate**: 1 year (renewable)
- **Renew command**: Re-run the certificate generation steps

### Network Security
- **TLS Version**: TLS 1.2+ (modern cipher suites)
- **Certificate Extensions**: Server Authentication only
- **SAN (Subject Alternative Names)**: IP.1=100.111.114.84, DNS.1=localhost

## Troubleshooting

### "Certificate Not Trusted" on iPhone
1. Verify CA certificate was installed (Settings → General → VPN & Device Management)
2. Verify certificate trust was enabled (Settings → General → About → Certificate Trust Settings)
3. Try clearing Safari cache and reloading

### "Connection Refused"
1. Check if HTTPS server is running: `ss -tlnp | grep 8443`
2. Check firewall settings: `sudo ufw status`
3. Verify certificate files exist: `ls -la ssl-certs/*.pem`

### "Permission Denied" (Port 443)
1. Use `sudo` for production mode
2. Or use development mode (port 8443) without sudo

### Certificate Verification Failed
```bash
# Test certificate chain
openssl verify -CAfile ssl-certs/ca-certificate.pem ssl-certs/server-certificate.pem

# Check certificate expiration
openssl x509 -in ssl-certs/server-certificate.pem -noout -dates
```

## Maintenance

### Certificate Renewal (Annual)
```bash
cd /home/ed/ghost-writer/ssl-certs

# Renew server certificate using secure helper
./cert-helper.sh renew-server

# Verify renewal worked
./cert-helper.sh verify

# Restart HTTPS server to use new certificate
```

### Adding Additional Domains/IPs
1. Edit `server-extensions.conf`
2. Add new `DNS.X` or `IP.X` entries to `[alt_names]` section
3. Regenerate server certificate
4. Restart HTTPS server

## Summary

This HTTPS implementation provides:
- ✅ **Safari Compatibility**: Resolves HTTPS-Only Mode issues
- ✅ **Security**: Full TLS encryption with proper certificate validation
- ✅ **Flexibility**: Works with any hostname/IP address
- ✅ **Self-Contained**: No external dependencies or services
- ✅ **Educational**: Complete understanding of PKI infrastructure
- ✅ **Production Ready**: Suitable for development and internal deployment

The solution follows industry best practices for development environments and provides a foundation for understanding certificate management in production systems.
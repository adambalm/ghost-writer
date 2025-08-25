# SSL Certificates for Ghost Writer

This directory contains SSL certificates and configuration for secure HTTPS access to Ghost Writer services.

## Files

- `ca-certificate.pem` - Certificate Authority in PEM format
- `ca-certificate.cer` - Same CA certificate (PEM content with .cer extension)
- `ca-certificate.der` - CA certificate in DER binary format
- `server-certificate.pem` - Server certificate for HTTPS
- `server-private-key.pem` - Server private key (gitignored)
- `ed-dev-root.mobileconfig` - iOS configuration profile for one-tap CA installation

## iOS One-Tap CA Install

### Local Server Method (Recommended - Correct MIME Types)

Start the certificate server:
```bash
scripts/publish-ios-cert.sh start
```

Then access on your iPhone:
- **Configuration Profile**: https://100.111.114.84:8443/ssl-certs/ed-dev-root.mobileconfig
- **DER Certificate (alt)**: https://100.111.114.84:8443/ssl-certs/ca-certificate.der
- **Web Interface**: https://100.111.114.84:8443/

**Why:** Our local server serves correct MIME types (`application/x-apple-aspen-config` for .mobileconfig, `application/pkix-cert` for .der) so iOS shows the Install dialog instead of rendering as text.

**Update:** After changing certificate files, restart the server with `scripts/publish-ios-cert.sh restart`

### GitHub Method (Fallback)

If the local server is unavailable:
- https://github.com/adambalm/ghost-writer/raw/ios-cert-link/ssl-certs/ed-dev-root.mobileconfig

Note: GitHub serves `text/plain` MIME type, which may cause iOS to display text instead of the install dialog.

## After Installation

1. Go to Settings → General → VPN & Device Management
2. Tap "Ed Dev Root CA" under Configuration Profile
3. Tap "Install" and enter your passcode
4. Go to Settings → General → About → Certificate Trust Settings
5. Enable "Full Trust" for "Ed Dev Root CA"

## Certificate Management

### Generate/Renew Certificates
```bash
cd ssl-certs
./cert-helper.sh generate-ca      # Generate new CA (10 year validity)
./cert-helper.sh generate-server  # Generate server cert (1 year validity)
./cert-helper.sh renew-server     # Renew server cert
./cert-helper.sh verify           # Verify certificate chain
./cert-helper.sh info            # Show certificate details
```

### Certificate Server Commands
```bash
scripts/publish-ios-cert.sh start    # Start certificate server
scripts/publish-ios-cert.sh stop     # Stop certificate server
scripts/publish-ios-cert.sh restart  # Restart server
scripts/publish-ios-cert.sh status   # Check server status
scripts/publish-ios-cert.sh test     # Test MIME types
```

## Troubleshooting

- **Server won't start**: Check port 8443 is free: `lsof -i :8443`
- **Certificate errors**: Verify certificates exist: `ls -la ssl-certs/*.pem`
- **iOS won't install**: Ensure correct MIME type with `curl -I https://100.111.114.84:8443/ssl-certs/ed-dev-root.mobileconfig`
- **View server logs**: `tail -f /tmp/ghost-writer-cert-server.log`
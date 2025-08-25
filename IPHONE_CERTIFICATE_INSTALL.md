# 📱 iPhone Certificate Installation Guide

## Quick Summary
You need to install `/home/ed/ghost-writer/ssl-certs/ca-certificate.pem` on your iPhone to trust our HTTPS site.

## Step-by-Step Instructions

### Step 1: Get the Certificate File to Your iPhone

**Choose ONE of these methods:**

#### Method A: Email (Easiest)
1. **On your computer**, email the file to yourself:
   ```bash
   # Email the certificate (replace with your email)
   echo "Install this certificate profile on your iPhone" | mail -s "Ghost Writer CA Certificate" -a /home/ed/ghost-writer/ssl-certs/ca-certificate.pem your-email@example.com
   ```
   **OR** manually attach `/home/ed/ghost-writer/ssl-certs/ca-certificate.pem` to an email

2. **On your iPhone**, open the email and tap the `ca-certificate.pem` attachment

#### Method B: AirDrop (If you have Mac)
1. **On Mac**: Right-click `ca-certificate.pem` → Share → AirDrop → Select your iPhone
2. **On iPhone**: Accept the AirDrop transfer
3. **Tap notification** to open the certificate

#### Method C: Cloud Storage
1. **Upload** `ca-certificate.pem` to iCloud Drive/Dropbox/Google Drive on your computer
2. **Download** the file using the app on your iPhone  
3. **Tap "Share"** → **"Install Profile"**

### Step 2: Install the Certificate Profile

1. **iPhone shows**: "Install Profile" screen with certificate details
   
2. **Tap "Install"** (top-right corner)

3. **Enter your iPhone passcode** if prompted

4. **Tap "Install"** again to confirm the installation

5. **Tap "Done"** when installation completes

   ✅ **You should see**: "Profile Installed" confirmation

### Step 3: Enable Certificate Trust (CRITICAL STEP)

**This step is essential - Safari won't trust the certificate without it!**

1. **Open Settings** on your iPhone

2. **Go to**: **General** → **About** 

3. **Scroll down** to **"Certificate Trust Settings"**
   - ⚠️ *If you don't see this option, the certificate wasn't installed properly - go back to Step 2*

4. **Find "Ghost Writer CA"** in the list

5. **Toggle the switch ON** next to "Ghost Writer CA"
   - The switch should turn **green**

6. **Read the warning** and tap **"Continue"**
   - Warning says: "Turning on full trust may reduce the overall security of your device"
   - This is normal for custom certificates

   ✅ **You should see**: Green checkmark next to "Ghost Writer CA"

### Step 4: Test the Installation

1. **Open Safari** on your iPhone

2. **Navigate to**: `https://100.111.114.84:8443`
   - (Use port 8443 for development, or just `https://100.111.114.84` if using production mode)

3. **Expected Result**: 
   - ✅ **Site loads normally** with a **lock icon** in the address bar
   - ✅ **No security warnings**
   - ✅ **Ghost Writer interface appears**

4. **If you see security warnings**: Go back and check Step 3 - certificate trust wasn't enabled properly

## Troubleshooting

### ❌ "Certificate Not Trusted" Error
**Cause**: Step 3 (Certificate Trust Settings) was skipped or incomplete

**Fix**: 
1. Settings → General → About → Certificate Trust Settings
2. Make sure "Ghost Writer CA" is **ON** (green)

### ❌ "Cannot Install Profile" Error  
**Cause**: Wrong file or file corrupted during transfer

**Fix**:
1. Re-download/re-transfer the `ca-certificate.pem` file
2. Make sure it's exactly `ca-certificate.pem` (not renamed)

### ❌ Certificate Trust Settings Not Visible
**Cause**: Certificate profile wasn't installed

**Fix**:
1. Settings → General → VPN & Device Management
2. Check if "Ghost Writer CA" appears under Configuration Profiles
3. If not there, repeat Step 2 (Install Profile)

### ❌ Still Getting Security Warnings
**Cause**: Using wrong URL or port

**Fix**: Make sure you're using:
- Development: `https://100.111.114.84:8443`  
- Production: `https://100.111.114.84`
- ⚠️ **Must use `https://`** (not `http://`)

## Verification Commands (Run on Computer)

```bash
# Check if HTTPS server is running
ss -tlnp | grep 8443

# Test HTTPS connection from computer
curl --cacert ssl-certs/ca-certificate.pem https://100.111.114.84:8443/status

# Start development server if needed
cd /home/ed/ghost-writer && source .venv/bin/activate && python web_viewer_with_auth_https.py
```

## Security Note

**This certificate installation is safe because:**
- ✅ You generated the certificate yourself on your own computer
- ✅ The certificate is only valid for `100.111.114.84` (your development box)
- ✅ It only works on your local network (Tailscale/private IP)
- ✅ No external parties can use this certificate

**To remove the certificate later:**
- Settings → General → VPN & Device Management → Configuration Profiles → Ghost Writer CA → Delete Profile

---

## Quick Test Checklist

- [ ] Certificate file transferred to iPhone
- [ ] Profile installed (Settings → General → VPN & Device Management)
- [ ] Certificate trust enabled (Settings → General → About → Certificate Trust Settings)
- [ ] HTTPS server running on computer (`python web_viewer_with_auth_https.py`)
- [ ] Safari loads `https://100.111.114.84:8443` without warnings
- [ ] Lock icon appears in Safari address bar

**Once all checkboxes are ✅, Safari HTTPS-Only Mode will work perfectly!** 🎉
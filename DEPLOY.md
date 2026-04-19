# Onbogo — Google Cloud Deployment Guide

## Overview

This guide walks through deploying Onbogo on Google Cloud's **Always Free** e2-micro VM. The instance runs 24/7 with no sleep, and Playwright runs Chromium locally — no Browserless.io account needed.

---

## Prerequisites

- Google account
- Your app's environment variable values (MongoDB URI, Gmail credentials, etc.)

> **Credit card note:** Google Cloud requires a credit card to sign up, but the e2-micro VM is part of the Always Free tier and is never charged as long as you stay within the free limits.

---

## Step 1 — Create a Google Cloud Account

1. Go to [cloud.google.com](https://cloud.google.com) and click **Get started for free**
2. Sign in with your Google account
3. Complete the billing setup (required, but you won't be charged for Always Free resources)
4. You'll land in the Google Cloud Console

---

## Step 2 — Create the VM

1. In the top search bar, search for **Compute Engine** and click it
2. If prompted, click **Enable** to enable the Compute Engine API (takes ~1 minute)
3. Click **Create Instance**
4. Configure the instance:
   - **Name:** `onbogo`
   - **Region:** `us-east1`, `us-west1`, or `us-central1` — pick the closest to you. **Must be one of these three** for Always Free eligibility
   - **Zone:** leave as default
5. Under **Machine configuration**:
   - Series: **E2**
   - Machine type: **e2-micro** (2 vCPU, 1 GB memory)
6. Under **Boot disk**, click **Change**:
   - Operating system: **Ubuntu**
   - Version: **Ubuntu 22.04 LTS**
   - Boot disk size: **30 GB** (free tier includes 30 GB)
   - Click **Select**
7. Under **Firewall**, check both:
   - **Allow HTTP traffic**
   - **Allow HTTPS traffic**
8. Click **Create**

Wait ~1 minute for the instance to show a green checkmark.

---

## Step 3 — Open Port 8080

Google Cloud blocks custom ports by default. Add a firewall rule to allow port 8080.

1. In the left sidebar go to **VPC Network → Firewall**
2. Click **Create Firewall Rule**
3. Fill in:
   - **Name:** `allow-8080`
   - **Targets:** All instances in the network
   - **Source IPv4 ranges:** `0.0.0.0/0`
   - **Protocols and ports:** Select **TCP** and enter `8080`
4. Click **Create**

---

## Step 4 — SSH Into the VM

Google Cloud has a built-in browser SSH — no key file needed.

1. Go back to **Compute Engine → VM Instances**
2. Find your `onbogo` instance and click **SSH** on the right side
3. A terminal window will open in your browser

---

## Step 5 — Add a Swap File

The e2-micro only has 1 GB RAM. Adding swap prevents the app from crashing if memory gets tight.

```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Step 6 — Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y

# Python and git
sudo apt install -y python3-pip python3-venv git
```

---

## Step 7 — Clone the Repo and Set Up Python

```bash
cd ~
git clone https://github.com/wijabu/onbogo.git
cd onbogo

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

---

## Step 8 — Create the .env File

```bash
nano ~/onbogo/.env
```

Paste the following and fill in your values:

```
SECRET_KEY=
DATABASE_URI=
SENDER_EMAIL=
SENDER_PASSWORD=
API_TOKEN=
USER_KEY=
REGISTER_KEY=
ENV=prod
```

Save with `Ctrl+O`, then `Ctrl+X` to exit.

> **Gmail note:** If using Gmail for SENDER_EMAIL, you need an **App Password**, not your regular password. Generate one at myaccount.google.com → Security → 2-Step Verification → App Passwords.

---

## Step 9 — Set Up the Systemd Service

This makes the app start automatically on boot and restart if it crashes.

```bash
sudo cp ~/onbogo/onbogo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable onbogo
sudo systemctl start onbogo
```

Check that it's running:
```bash
sudo systemctl status onbogo
```

You should see `Active: active (running)`.

---

## Step 10 — Verify the App

Find your VM's external IP on the **VM Instances** page in the Google Cloud Console, then open:

```
http://<your-vm-external-ip>:8080
```

You should see the Onbogo homepage.

---

## Useful Commands

| Task | Command |
|---|---|
| View live logs | `sudo journalctl -u onbogo -f` |
| Restart the app | `sudo systemctl restart onbogo` |
| Stop the app | `sudo systemctl stop onbogo` |
| Pull latest code and redeploy | `cd ~/onbogo && git pull && sudo systemctl restart onbogo` |

---

## Custom Domain + HTTPS (Caddy)

Once the app is running on `http://<vm-ip>:8080`, wire up a real hostname with automatic HTTPS via Caddy.

### Step A — Reserve a static IP

Google Cloud's default external IP is **ephemeral** and will change if the VM stops. Pin it:

1. Go to **VPC Network → IP addresses** in the Google Cloud Console.
2. Find the **Ephemeral** IP attached to your `onbogo` instance.
3. Click **RESERVE** (or use the three-dot menu → **Promote to static IP address**).
4. Give it a name (e.g. `onbogo-ip`). Free while attached to a running VM.

> **Cost warning:** a static IP is free only while **attached to a running VM**. If you ever delete or stop-and-detach the VM, **unreserve the IP immediately** (IP addresses → three-dot menu → Release static address), or you start paying ~$0.01/hr.

### Step B — Point onbogo.duckdns.org at that IP

1. Go to [duckdns.org](https://www.duckdns.org), sign in with Google.
2. Create the subdomain `onbogo` (so the full hostname is `onbogo.duckdns.org`).
3. Paste the static IP from Step A into the IP box for that subdomain, click **update ip**.

Wait ~1 minute, then verify against an external resolver (local resolvers cache aggressively):

```bash
dig +short onbogo.duckdns.org @8.8.8.8
```

Should return your static IP. If it returns nothing or the wrong IP, wait another minute and re-query — don't start Caddy until this resolves correctly or Let's Encrypt will rate-limit you (5 failures/hour/hostname).

### Step C — Open ports 80 and 443 in GCP firewall

**VPC Network → Firewall → Create Firewall Rule**
- Name: `allow-443`
- Targets: All instances in the network
- Source IPv4 ranges: `0.0.0.0/0`
- Protocols and ports: TCP `443`

Caddy also needs **port 80** open for the Let's Encrypt HTTP-01 challenge. GCP's "Allow HTTP traffic" checkbox during VM creation adds a tag-based rule that only applies if your VM has the `http-server` tag. **Verify port 80 is actually reachable** before starting Caddy:

```bash
# From any external machine (not the VM itself):
curl -v http://onbogo.duckdns.org/
```

You should get a connection (any HTTP response, even a 404, is fine — what matters is the TCP handshake completes). If you get `Connection refused` or a timeout, create an `allow-80` rule with the same settings as `allow-443` but TCP port `80`.

### Step D — Install Caddy on the VM

SSH into the VM, then:

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

### Step E — Configure Caddy

The repo's `Caddyfile` is already wired for `onbogo.duckdns.org`:

```bash
sudo cp ~/onbogo/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Watch the logs to confirm the cert was provisioned:

```bash
sudo journalctl -u caddy -f
```

You should see `certificate obtained successfully` within ~30 seconds. Visit `https://onbogo.duckdns.org` — the onbogo homepage should load with a valid cert (padlock in the address bar).

**Smoke tests before proceeding to Step F:**

```bash
# 1. HTTPS responds and serves the app
curl -I https://onbogo.duckdns.org/
# Expect: HTTP/2 200 (or 302 redirect), valid cert — no "SSL certificate problem"

# 2. Password-reset link uses https:// (confirms ProxyFix is working)
# Request a password reset from the app and check the email — the link should start with https://

# 3. Cert renewal dry-run (optional sanity check)
sudo caddy list-modules | head -1   # confirm Caddy is alive
sudo journalctl -u caddy | grep -i 'obtained\|renew'
```

If any of these fail, **do not proceed to Step F** — fix the issue first. If you need to roll back, the app is still reachable at `http://<static-ip>:8080` until Step F closes that port.

### Step F — Close port 8080 publicly (REQUIRED)

Once HTTPS is confirmed working (all smoke tests above passing), lock down direct access to gunicorn. Leaving 8080 open means attackers can hit the app over plain HTTP, bypassing TLS entirely — session cookies and password-reset tokens would travel in cleartext for anyone using that path.

**1. Delete the firewall rule:**

VPC Network → Firewall → delete the `allow-8080` rule.

**2. Bind gunicorn to localhost only (defense in depth):**

Edit `/etc/systemd/system/onbogo.service` and change the `ExecStart` line from `--bind 0.0.0.0:8080` to `--bind 127.0.0.1:8080`. Or apply the change from the repo:

```bash
sudo sed -i 's|--bind 0.0.0.0:8080|--bind 127.0.0.1:8080|' /etc/systemd/system/onbogo.service
sudo systemctl daemon-reload
sudo systemctl restart onbogo
```

Caddy still reaches the app via `localhost:8080`, but the kernel won't accept connections on the public interface even if the firewall rule is accidentally re-added later. Verify:

```bash
curl -I http://localhost:8080/        # still works locally
curl -I http://<static-ip>:8080/      # should fail: connection refused
curl -I https://onbogo.duckdns.org/   # still works
```

---

## Scheduled Runs

The app uses APScheduler to automatically run every **Thursday at 4:30 PM UTC** and send sale alerts to all users with a saved store and shopping list. Because the VM never sleeps, this runs reliably without any external cron service.

To change the schedule, edit the `scheduler.add_job` line in [onbogo/__init__.py](onbogo/__init__.py).

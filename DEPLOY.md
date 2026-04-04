# Onbogo — Oracle Cloud Deployment Guide

## Overview

This guide walks through deploying Onbogo on Oracle Cloud's **Always Free** tier using an Ampere A1 (ARM) VM. The app runs 24/7 with no sleep, and Playwright runs Chromium locally — no Browserless.io account needed.

---

## Prerequisites

- Oracle Cloud account ([cloud.oracle.com](https://cloud.oracle.com)) — credit card required for signup, but Always Free resources are never charged
- Your app's environment variable values (MongoDB URI, Gmail credentials, etc.)
- Git access to your repo

---

## Step 1 — Create the VM

1. Log in to [cloud.oracle.com](https://cloud.oracle.com)
2. Go to **Compute → Instances → Create Instance**
3. Give it a name (e.g. `onbogo`)
4. Under **Image and Shape**, click **Change Shape**
   - Select **Ampere** (ARM-based)
   - Choose **VM.Standard.A1.Flex**
   - Set **1 OCPU** and **6 GB RAM**
5. Under **Networking**, leave defaults (a public IP will be assigned)
6. Under **Add SSH Keys**, download or paste your public key
7. Click **Create**

Wait ~2 minutes for the instance to show **Running**.

---

## Step 2 — Open Port 8080

Oracle blocks all ports by default at two levels — the cloud firewall and the VM's OS firewall. You need to open both.

### Cloud firewall (Security List)
1. In your instance details, click the **Subnet** link
2. Click **Default Security List**
3. Click **Add Ingress Rules**
4. Fill in:
   - Source CIDR: `0.0.0.0/0`
   - IP Protocol: TCP
   - Destination Port Range: `8080`
5. Click **Add Ingress Rules**

### VM OS firewall
SSH in first (see Step 3), then run:
```bash
sudo iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

---

## Step 3 — SSH Into the VM

```bash
ssh -i /path/to/your-private-key.pem ubuntu@<your-vm-ip>
```

Your VM's public IP is shown on the instance details page in the Oracle console.

---

## Step 4 — Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y

# Python and git
sudo apt install -y python3-pip python3-venv git

# System libraries required by Playwright's Chromium browser
sudo apt install -y \
  libglib2.0-0 libnss3 libfontconfig1 libxss1 \
  libxtst6 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
  libgbm1 libasound2 libatk1.0-0 libatk-bridge2.0-0 \
  libpango-1.0-0 libcairo2 libdrm2 libxfixes3 libxkbcommon0
```

---

## Step 5 — Clone the Repo and Set Up Python

```bash
cd ~
git clone https://github.com/wijabu/onbogo.git
cd onbogo

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Chromium browser for Playwright
python -m playwright install chromium
```

---

## Step 6 — Create the .env File

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

## Step 7 — Set Up the Systemd Service

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

## Step 8 — Verify the App

Open a browser and go to:
```
http://<your-vm-ip>:8080
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

## Scheduled Runs

The app uses APScheduler to automatically run every **Thursday at 4:30 PM UTC** and send sale alerts to all users with a saved store and shopping list. Because the VM never sleeps, this runs reliably without any external cron service.

To change the schedule, edit the `scheduler.add_job` line in [onbogo/__init__.py](onbogo/__init__.py).

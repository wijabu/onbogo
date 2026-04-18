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

## Scheduled Runs

The app uses APScheduler to automatically run every **Thursday at 4:30 PM UTC** and send sale alerts to all users with a saved store and shopping list. Because the VM never sleeps, this runs reliably without any external cron service.

To change the schedule, edit the `scheduler.add_job` line in [onbogo/__init__.py](onbogo/__init__.py).

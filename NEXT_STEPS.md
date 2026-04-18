# Onbogo — Open Work & Next Steps

Tracked backlog of things we've identified but deferred. Ordered by rough priority.

---

## 1. Custom DNS name + HTTPS

**Goal:** replace `http://<vm-ip>:8080` with something like `https://onbogo.example.com`.

**Steps:**
1. **Reserve a static external IP** in Google Cloud Console → VPC Network → IP addresses. Free while attached to a running VM. Attach it to the `onbogo` instance so the IP stops changing on restart.
2. **Register a domain** (Namecheap / Cloudflare / Porkbun, ~$10/yr) *or* use a free subdomain service (duckdns.org, freedns.afraid.org).
3. **Create an A record** pointing the hostname → static IP.
4. **Open port 443** in GCP firewall (we already have 80 and 8080).
5. **Install Caddy** on the VM (simpler than nginx + certbot):
   ```bash
   sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
   curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
   sudo apt update && sudo apt install caddy
   ```
6. **Configure Caddy** — edit `/etc/caddy/Caddyfile`:
   ```
   onbogo.example.com {
       reverse_proxy localhost:8080
   }
   ```
7. **Reload Caddy**: `sudo systemctl reload caddy`. It auto-provisions a Let's Encrypt cert on first request.
8. **Optional:** close port 8080 in GCP firewall once 443 is working, so the app is only reachable via the domain.

---

## 2. Password reset flow

**Not implemented.** The "Forgot password?" link on `login.html` is commented out until this exists.

**What needs building:**
- **Route `/reset` (GET):** form asking for email.
- **Route `/reset` (POST):** look up user, generate time-limited token (e.g. `itsdangerous.URLSafeTimedSerializer`, 1-hour expiry), email a link `https://.../reset/<token>`.
- **Route `/reset/<token>` (GET):** verify token, render "set new password" form.
- **Route `/reset/<token>` (POST):** verify token again, update password hash via `User().update_account()`, flash success, redirect to login.
- **Templates:** `reset_request.html` and `reset_form.html`.
- **Env var:** `SECRET_KEY` (already in .env) is used to sign tokens.
- **Reuse:** existing `notify.send_email()` for the reset email.

Non-trivial but self-contained — maybe a half-day of work.

---

## 3. Login Enter-key submission

**Fixed in commit** (added `type="submit"` to login button). If pressing Enter still doesn't log in after `git pull && sudo systemctl restart onbogo`:
- Hard-refresh the browser (Cmd+Shift+R) to clear cached HTML.
- If still broken, check browser devtools Network tab — does pressing Enter fire a POST to `/login`? If yes, it's a server-side issue. If no, something is intercepting the keypress.

---

## 4. Other polish items (low priority)

- **Bootstrap version mismatch:** `base.html` loads Bootstrap 5.3 CSS but Bootstrap 4.0 JS. Components that rely on JS (modals, dropdowns, alert close buttons) may misbehave. Upgrade JS to 5.3 or downgrade CSS to 4.x.
- **Mojibake still possible in some edge cases.** The `_fix()` helper in [sales.py](onbogo/sales.py) handles the common case (double-UTF-8 decoded as Latin-1) but any string the encoding helper can't round-trip falls back to the original. If we see new mojibake, add an alternate decode path.
- **`alert-dismissible` close button** in `base.html` uses Bootstrap 4 syntax (`data-dismiss`) but the CSS is Bootstrap 5 (`data-bs-dismiss`). Close button probably doesn't work. Tied to the Bootstrap-version-mismatch item above.
- **Commented-out "my shopping list" block** in `load.html` can be deleted if we don't plan to bring it back.

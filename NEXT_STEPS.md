# Onbogo — Open Work & Next Steps

Tracked backlog of things we've identified but deferred. Ordered by rough priority.

---

## 1. Custom DNS name + HTTPS — DONE

Live at **https://onbogo.duckdns.org** with Let's Encrypt cert via Caddy reverse proxy.

- Static IP `34.74.221.234` reserved in GCP as `onbogo-ip`.
- A record `onbogo.duckdns.org` → static IP.
- Caddy listening on :80/:443, reverse-proxying to `localhost:8080`. Cert auto-renews every 60 days.
- Flask sees correct scheme/host via `ProxyFix` (password-reset emails correctly use `https://`).
- Gunicorn binds to `127.0.0.1:8080` only (see [onbogo.service](onbogo.service)); GCP `allow-8080` firewall rule deleted. Defense in depth: app is unreachable publicly except via Caddy.
- Session cookies hardened: `Secure`, `HttpOnly`, `SameSite=Lax`.

**If DuckDNS flakes:** see section 5 for Dynu backup plan.

---

## 2. Password reset flow — DONE

Implemented:
- `GET/POST /reset` — email input form, generates `itsdangerous` token (1-hour expiry, signed with `SECRET_KEY`), sends reset link via `notify.send_email()`. Same response whether email exists or not (prevents account enumeration).
- `GET/POST /reset/<token>` — verifies token, renders new-password form, updates password hash via `User().update_password()`, redirects to login.
- Templates: `reset_request.html`, `reset_form.html`.
- "Forgot password?" link re-enabled on login page.

**To test after deploy:** click Forgot password → enter your email → check inbox → click link → set new password → log in with new password.

**Note:** reset links will initially be `http://<vm-ip>:8080/reset/<token>` until DNS+HTTPS (item 1) is set up.

---

## 3. Login Enter-key submission

**Fixed in commit** (added `type="submit"` to login button). If pressing Enter still doesn't log in after `git pull && sudo systemctl restart onbogo`:
- Hard-refresh the browser (Cmd+Shift+R) to clear cached HTML.
- If still broken, check browser devtools Network tab — does pressing Enter fire a POST to `/login`? If yes, it's a server-side issue. If no, something is intercepting the keypress.

---

## 4. Rate limiting on /login and /reset (post-launch)

Once live on HTTPS, `/login` and `/reset` are more exposed than they were on `http://<ip>:8080`. Neither has any throttling today.

**Risks:**
- Password brute-force against `/login`.
- Email-flooding abuse via `/reset` (the endpoint correctly avoids account enumeration, but still sends an email per valid address submitted).

**Fix:** add [flask-limiter](https://flask-limiter.readthedocs.io/) with ~5 req/min per IP on both endpoints. In-memory backend is fine for a single-worker gunicorn; swap to Redis later if we scale to multiple workers.

Not blocking for launch — the app is invite-only (access code gating on `/register`), so exposure is limited.

---

## 5. Backup DDNS — DONE

Dual-hostname setup live:
- **Primary:** `https://onbogo.duckdns.org`
- **Backup:** `https://onbogo.freeddns.org` (Dynu)

Both A records point at the static IP `34.74.221.234`. Caddy serves the same app on both with separate Let's Encrypt certs. If DuckDNS has another outage, users can reach the app via the Dynu hostname.

---

## 6. Other polish items (low priority)

- **Mojibake helper now shared.** `fix_encoding()` lives in [onbogo/text.py](onbogo/text.py) and is applied in both [sales.py](onbogo/sales.py) (product titles/deals) and [store.py](onbogo/store.py) (store names/addresses). If a new encoding edge case appears (e.g. CP1252 smart quotes from a different upstream source), extend the helper there — one place, two callers.

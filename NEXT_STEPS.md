# Onbogo — Open Work & Next Steps

Tracked backlog of things we've identified but deferred. Ordered by rough priority.

---

## 1. Custom DNS name + HTTPS — IN PROGRESS

**Code prep done:**
- [Caddyfile](Caddyfile) template in repo root (placeholder `YOUR_HOSTNAME`).
- Flask wrapped with `ProxyFix` in [onbogo/__init__.py](onbogo/__init__.py) so it trusts `X-Forwarded-Proto`/`Host` from Caddy and `url_for(_external=True)` emits `https://` URLs.
- Full deploy runbook added to [DEPLOY.md](DEPLOY.md) — "Custom Domain + HTTPS (Caddy)" section, Steps A–F.

**Hostname chosen:** `onbogo.duckdns.org` (free). Caddyfile already wired for it.

**Left to do (operational, on GCP console + VM):**
1. Reserve a static IP in GCP (DEPLOY.md Step A).
2. Register `onbogo` on duckdns.org and point it at the static IP (Step B).
3. Open port 443 in GCP firewall (Step C).
4. SSH into VM, install Caddy (Step D), copy `Caddyfile` into `/etc/caddy/` and reload (Step E).
5. Verify cert provisioned, hit `https://onbogo.duckdns.org`.
6. Optional: close port 8080 publicly (Step F).

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

## 5. Backup DDNS option (if duckdns.org flakes)

Architect review surfaced that DuckDNS had an unexplained outage in August 2025 with no status communication. If it happens again during a scheduled Thursday job or password-reset flow, the app is effectively offline for anyone hitting it by hostname.

**Backup option:** [Dynu](https://www.dynu.com) — free, 4-hostname cap, higher uptime reputation, same A-record workflow. Can be wired up in parallel (both DNS records pointing at the static IP) so a fallback hostname exists if DuckDNS goes dark.

Not blocking — only act if DuckDNS reliability becomes a real problem.

---

## 6. Other polish items (low priority)

- **Bootstrap version mismatch:** `base.html` loads Bootstrap 5.3 CSS but Bootstrap 4.0 JS. Components that rely on JS (modals, dropdowns, alert close buttons) may misbehave. Upgrade JS to 5.3 or downgrade CSS to 4.x.
- **Mojibake still possible in some edge cases.** The `_fix()` helper in [sales.py](onbogo/sales.py) handles the common case (double-UTF-8 decoded as Latin-1) but any string the encoding helper can't round-trip falls back to the original. If we see new mojibake, add an alternate decode path.
- **`alert-dismissible` close button** in `base.html` uses Bootstrap 4 syntax (`data-dismiss`) but the CSS is Bootstrap 5 (`data-bs-dismiss`). Close button probably doesn't work. Tied to the Bootstrap-version-mismatch item above.
- **Commented-out "my shopping list" block** in `load.html` can be deleted if we don't plan to bring it back.

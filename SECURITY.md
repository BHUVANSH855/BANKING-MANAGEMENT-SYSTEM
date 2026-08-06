# Security Policy

## Supported versions

This is a single-branch academic/portfolio project — only the latest commit
on `main` is supported. There are no maintained release branches.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security problems.

Instead, report privately via one of:

- A [GitHub private security advisory](../../security/advisories/new) on
  this repository (preferred), or
- Direct message to the repository maintainer.

Please include: the affected file/endpoint, steps to reproduce, and the
potential impact. You should get an acknowledgment within a few days —
this is a small project maintained outside of working hours, so please be
patient.

---

## ⚠️ Known issue: credential committed to the repository

`backend/app/tests/test_email.py` contains a **hardcoded Gmail address and
app password** in plaintext, committed to source control. This is a real
leaked credential, not a placeholder.

**If this is your repository, do this now:**

1. Go to your Google Account → Security → App passwords, and **revoke**
   that app password immediately.
2. Remove the credential from the file (use an environment variable
   instead — see below).
3. **Removing the file in a new commit is not enough** — the credential is
   still readable in git history. Use `git filter-repo` (or BFG Repo
   Cleaner) to purge it from history, then force-push, and ask anyone with
   a clone to re-clone.
4. Treat the credential as compromised even after rotating it — assume it
   may have already been scraped by an automated bot if this repo was ever
   public.

Going forward, load secrets like this from environment variables, e.g.:

```python
import os
EMAIL = os.environ["BANK_ALERT_EMAIL"]
APP_PASSWORD = os.environ["BANK_ALERT_APP_PASSWORD"]
```

and add a `.env` entry to `.gitignore` (already present in this repo — just
make sure secrets actually live there, not inline in `.py` files).

---

## Other known security considerations

These aren't "bugs" exactly, but anyone deploying this project for
anything beyond a demo should be aware of them:

### PINs are short, unsalted SHA-256 hashes
`backend/app/core/utils.py` hashes PINs with plain `hashlib.sha256`, no
salt. Two problems compound here:
- PINs are constrained to 4–6 digits (`^\d{4,6}$`), i.e. at most one
  million possible values — trivially brute-forceable offline even against
  a *properly* salted hash, let alone an unsalted one.
- Without a salt, identical PINs across different accounts produce
  identical hashes, and precomputed rainbow tables for a 6-digit keyspace
  are trivial to generate.

If you extend this project for real use, consider a proper KDF
(`bcrypt`/`argon2`) and/or requiring a longer PIN or a secondary factor.

### Admin auth is a shared PIN on every request, no sessions
Every `/api/admin/*` endpoint expects the admin PIN in the request body on
*every call* — there's no session or token layer. The frontend keeps this
PIN in `sessionStorage` for the tab's lifetime for convenience. This means:
- The PIN is sent over the wire on every admin action — always deploy
  behind HTTPS, never HTTP, for any non-local use.
- There's no way to have multiple admins with distinct, revocable
  credentials, and no audit trail of *which* admin did what.

### Default admin account
A default admin account (`admin@bank.local`, PIN `123456`) is created
automatically on first run (`models.ensure_admin_account()`). **Change this
PIN before any real deployment** — see the README's
[Default admin account](README.md#default-admin-account) section.

### CORS is wide open
`CORS(app)` is applied with no restrictions, so the API accepts
cross-origin requests from any origin. Fine for local development; for a
real deployment, scope it to your actual frontend's origin.

### No rate limiting
There's no rate limiting on login, withdraw, or transfer attempts beyond
the 3-strikes account lock (which only applies to a single account's PIN,
not to request volume generally). A determined attacker could still
enumerate account IDs or hammer the admin login endpoint.

### `backend/app/tests/` scripts are not safe to run as-is
Beyond the leaked credential above, `test_pin.py` imports a module
(`live_pincode_lookup`) that doesn't exist in this repo — it will fail
immediately if run. These are leftover manual debug scripts, not an
automated test suite (see CONTRIBUTING.md).

---

## Reporting non-security bugs

For anything that isn't a security issue, please use the regular issue
tracker instead of the private channels above — see
[CONTRIBUTING.md](CONTRIBUTING.md).
# users

Identity for returning users (ADR 0013): a username plus a 4-digit PIN.

- `models.py`: `User` (username unique, lowercase, `[a-z0-9_]{3,20}`, CHECK in the DB).
- `pins.py`: argon2 hashing. PINs are never stored or logged in plain text.
- `service.py`: entry point. `login_or_register` registers a new username or
  checks the PIN of a known one (`InvalidCredentialsError`). `Credentials`
  normalizes the username before validating it.

The session cookie itself is in `api/session.py`; `api/deps.py` turns it into
`user_id`, the only way any other code learns who the user is.

Depends on: `db`. Used by: `api`.

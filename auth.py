"""
auth.py — SkillMind AI minimal auth helpers

Adds email/password sign-in on top of the existing "one profile_id per
browser" model. No new dependency: passwords are hashed with the
standard-library `hashlib.pbkdf2_hmac`, and session tokens are random
`secrets.token_hex` strings persisted in SQLite (see db.py: `users` and
`sessions` tables). This keeps the "clone and run locally, no extra
infra" spirit of the rest of the project.

A signed-in user is just a wrapper around the same profile_id concept
the app already used: signing up mints a fresh profile_id and remembers
it against the account, so logging in on a different browser restores
the same profile/skills/progress instead of starting over.
"""
import hashlib
import hmac
import re
import secrets

PBKDF2_ITERATIONS = 200_000
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valid_email(email: str) -> bool:
    return bool(email) and bool(EMAIL_RE.match(email.strip()))


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest_hex = stored.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return hmac.compare_digest(check.hex(), digest_hex)


def new_token() -> str:
    return secrets.token_hex(24)


def new_user_id() -> str:
    return "u" + secrets.token_hex(10)


def extract_bearer_token(authorization_header: str) -> str:
    """Pull the token out of an 'Authorization: Bearer <token>' header. Returns '' if absent/malformed."""
    if not authorization_header:
        return ""
    parts = authorization_header.strip().split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return authorization_header.strip()

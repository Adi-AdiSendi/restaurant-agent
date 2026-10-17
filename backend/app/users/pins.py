"""PIN hashing with argon2. PINs are never stored or logged in plain text.

Hashing is CPU-bound (tens of ms), so it runs in a worker thread, not on the
event loop. Parameters follow the OWASP minimum for argon2id (19 MiB, t=2).
"""

import asyncio

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


async def hash_pin(pin: str) -> str:
    return await asyncio.to_thread(_hasher.hash, pin)


async def verify_pin(pin_hash: str, pin: str) -> bool:
    try:
        return await asyncio.to_thread(_hasher.verify, pin_hash, pin)
    except (VerificationError, InvalidHashError):
        return False

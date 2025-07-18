# locks.py  – import this anywhere
import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager

_user_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

def get_user_lock(uid: str) -> asyncio.Lock:
    """Return the asyncio.Lock dedicated to one user's Chroma store."""
    return _user_locks[uid]

@asynccontextmanager
async def chroma_guard(uid: str, timeout: float = 30.0):
    """
    Async-context that acquires the per-user lock.
    If lock isn't free within `timeout` seconds → raises asyncio.TimeoutError.
    """
    lock = get_user_lock(uid)
    try:
        await asyncio.wait_for(lock.acquire(), timeout=timeout)
        yield
    finally:
        if lock.locked():
            lock.release()
"""Lightweight request identity helpers.

This project is still a single-user/local-first app, so the token is not a
real login credential. It is only used to partition records created by each
browser profile.
"""

from __future__ import annotations

ANONYMOUS_USER_TOKEN = "anonymous"


def get_user_token(authorization: str | None) -> str:
    if not authorization:
        return ANONYMOUS_USER_TOKEN
    value = authorization.removeprefix("Bearer ").strip()
    return value or ANONYMOUS_USER_TOKEN

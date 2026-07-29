"""Environment & credentials: ``.env`` loading and the Context7 API key.

Mirrors ``tav_core/environment.py``'s ``.env`` discovery (repo-root-relative
``find_dotenv`` first, falling back to whatever the process environment
already has), but with one deliberate difference: the API key here is never
required. Context7's REST API answers unauthenticated requests too -- this
was confirmed by hand against both endpoints this package calls (see
README "認証") -- so a missing/blank key is a normal, supported state, not an
error. Everything that reads the process environment lives in this one file.
"""

from __future__ import annotations

import os

from dotenv import find_dotenv, load_dotenv

API_KEY_ENV = "CONTEXT7_API_KEY"


def load_environment() -> str | None:
    """Load ``.env`` (repo-root-relative discovery), return the path used, if any."""
    dotenv_path = find_dotenv(filename=".env", usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path, override=False)
        return dotenv_path

    load_dotenv(override=False)
    return None


def get_normalized_api_key() -> str:
    """``CONTEXT7_API_KEY`` from the environment, stripped. Empty string means "no key".

    Never treated as an error condition by this package -- callers pass the
    result straight to ``ctx7_core.client`` functions, which omit the
    ``Authorization`` header entirely when this is falsy.
    """
    return os.getenv(API_KEY_ENV, "").strip()

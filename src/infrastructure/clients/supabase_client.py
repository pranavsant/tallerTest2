"""
SupabaseClient — thin wrapper around the Supabase Python SDK.

Provides a single shared async client instance.
"""
from __future__ import annotations

from functools import lru_cache

from supabase import AsyncClient, acreate_client

from src.infrastructure.config import get_settings


@lru_cache(maxsize=1)
def _get_settings() -> tuple[str, str]:
    s = get_settings()
    return s.supabase_url, s.supabase_service_key


async def get_supabase_client() -> AsyncClient:
    """Return an initialised async Supabase client."""
    url, key = _get_settings()
    return await acreate_client(url, key)

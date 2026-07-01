"""Supabase client for the ingredient cleanup ETL."""

from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from .config import settings


@lru_cache(maxsize=1)
def client() -> Client:
    s = settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


def reset_client() -> None:
    client.cache_clear()


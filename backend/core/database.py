"""
Supabase Database Connection
"""
from supabase import create_client, Client
import os
from typing import Optional

class SupabaseDB:
    """Singleton Supabase client"""
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Get or create Supabase client"""
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")

            if not url or not key:
                raise ValueError(
                    "SUPABASE_URL and SUPABASE_KEY must be set in .env file.\n"
                    "Get them from: Supabase Dashboard → Settings → API"
                )

            cls._instance = create_client(url, key)
            print(f"✅ Connected to Supabase: {url}")

        return cls._instance


def get_db() -> Client:
    """Convenience function to get database client"""
    return SupabaseDB.get_client()

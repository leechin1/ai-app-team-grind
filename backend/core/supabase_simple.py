"""
Simple Supabase integration - no complex dependencies
Just basic connection for testing
"""
import os
from supabase import create_client, Client


def get_supabase_client() -> Client:
    """Get Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise ValueError("Supabase credentials not configured")

    return create_client(url, key)


# Test connection
def test_connection():
    """Test if Supabase connection works"""
    try:
        client = get_supabase_client()
        result = client.table("profiles").select("*").limit(1).execute()
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)

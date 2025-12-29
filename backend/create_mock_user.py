"""
Create mock user profile for development mode
Run this once to set up the test user profile
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

from supabase import create_client

# Mock user ID (same as in backend/core/auth.py)
MOCK_USER_ID = "00000000-0000-0000-0000-000000000001"

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("[ERROR] Missing Supabase credentials in .env file")
    sys.exit(1)

client = create_client(supabase_url, supabase_key)

print("Creating mock user profile for development...")
print(f"User ID: {MOCK_USER_ID}")

try:
    # Check if profile already exists
    result = client.table("profiles").select("*").eq("id", MOCK_USER_ID).execute()

    if result.data:
        print("[OK] Mock user profile already exists!")
        print(f"    Email: {result.data[0]['email']}")
        print(f"    Name: {result.data[0].get('full_name', 'N/A')}")
    else:
        # Create the profile
        profile_data = {
            "id": MOCK_USER_ID,
            "email": "demo@notiq.app",
            "full_name": "Demo User"
        }

        result = client.table("profiles").insert(profile_data).execute()
        print("[OK] Mock user profile created successfully!")
        print(f"    Email: demo@notiq.app")
        print(f"    Name: Demo User")
        print(f"    ID: {MOCK_USER_ID}")

    print("\nYou can now create projects in the frontend!")

except Exception as e:
    print(f"[ERROR] Failed to create profile: {e}")
    print("\nThis might be because:")
    print("1. The user doesn't exist in auth.users table (Supabase Auth)")
    print("2. RLS policies are preventing the insert")
    print("\nSolution: Make sure RLS is disabled for the profiles table")
    print("Run the disable_rls_for_dev.sql script in Supabase SQL Editor")
    sys.exit(1)

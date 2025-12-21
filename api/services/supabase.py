from supabase import create_client, Client
from ..config import settings

class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def get_client(self) -> Client:
        return self.client

supabase_service = SupabaseService()

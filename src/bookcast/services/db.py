from bookcast.config import SUPABASE_API_KEY, SUPABASE_PROJECT_URL
from supabase import Client, create_client
from supabase.client import ClientOptions

supabase: Client = create_client(
    SUPABASE_PROJECT_URL,
    SUPABASE_API_KEY,
    options=ClientOptions(
        postgrest_client_timeout=10,
        storage_client_timeout=10,
    ),
)

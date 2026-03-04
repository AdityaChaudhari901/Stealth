import os
from supabase import create_client, Client

# We rely on the environment variables loaded in main.py
url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY") # Or service role key if needed for backend bypass

if not url or not key:
    raise ValueError("Supabase URL and Key must be defined to use the Supabase Client.")

supabase: Client = create_client(url, key)

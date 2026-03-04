-- Run this in your Supabase SQL Editor to create the generations table

CREATE TABLE generations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  title TEXT,
  transcript TEXT NOT NULL,
  media_url TEXT, -- The public URL to the uploaded podcast
  content_data JSONB NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Turn on Row Level Security (RLS) so users can only see their own generations
ALTER TABLE generations ENABLE ROW LEVEL SECURITY;

-- Create policy for users to insert their own data
CREATE POLICY "Users can insert their own generations" 
ON generations FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Create policy for users to view their own data
CREATE POLICY "Users can view their own generations" 
ON generations FOR SELECT 
USING (auth.uid() = user_id);

-- Create policy for users to delete their own data
CREATE POLICY "Users can delete their own generations" 
ON generations FOR DELETE 
USING (auth.uid() = user_id);

-- ==========================================
-- NEW: Monetization & Usage Tracking
-- ==========================================

-- Create a public users table to track credits and Razorpay details
CREATE TABLE users (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT NOT NULL,
  plan TEXT DEFAULT 'free' NOT NULL,
  credits_used INTEGER DEFAULT 0 NOT NULL,
  razorpay_customer_id TEXT,
  razorpay_subscription_id TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Turn on RLS for users
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users can read their own profile
CREATE POLICY "Users can manage their own profile" 
ON users FOR SELECT 
USING (auth.uid() = id);

-- Backend secure service role bypasses RLS, but we can also allow updates
CREATE POLICY "Users can update their own profile" 
ON users FOR UPDATE 
USING (auth.uid() = id);

-- Trigger to automatically create a user profile when a new Supabase Auth user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = ''
AS $$
BEGIN
  INSERT INTO public.users (id, email, plan, credits_used)
  VALUES (NEW.id, NEW.email, 'free', 0);
  RETURN NEW;
END;
$$;

-- Attach the trigger to the auth.users table
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Enable storage extensions if not present
create extension if not exists "uuid-ossp";

-- Create the new bucket for ephemeral audio
insert into storage.buckets (id, name, public, avif_autodetection, file_size_limit, allowed_mime_types)
values ('temporary-audio', 'temporary-audio', true, false, 52428800, '{audio/*,video/*}')
on conflict (id) do nothing;

-- Set up basic RLS policies to allow anyone to upload and read
create policy "Allow public uploads to temporary audio"
on storage.objects for insert to public
with check ( bucket_id = 'temporary-audio' );

create policy "Allow public read access to temporary audio"
on storage.objects for select to public
using ( bucket_id = 'temporary-audio' );

-- Optional: If pg_cron is available, schedule the cleanup script
-- SELECT cron.schedule(
--   'cleanup-temporary-audio',
--   '0 * * * *', -- Run every hour
--   $$
--   DELETE FROM storage.objects
--   WHERE bucket_id = 'temporary-audio'
--   AND created_at < NOW() - INTERVAL '24 hours';
--   $$
-- );

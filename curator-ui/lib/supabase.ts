import "server-only";
import { createClient } from "@supabase/supabase-js";

export function serviceClient() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!url || !key) throw new Error("Supabase server credentials are not configured");
  return createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });
}

export function remoteIngredientClient() {
  const url = process.env.REMOTE_SUPABASE_URL;
  const key = process.env.REMOTE_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) throw new Error("Remote Supabase ingredient credentials are not configured");
  return createClient(url, key, { auth: { persistSession: false, autoRefreshToken: false } });
}

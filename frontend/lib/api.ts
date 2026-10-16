import { supabase } from "./supabase";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  "https://enterprise-rag-assistant-api.onrender.com/api/v1";

export async function apiFetch(
  path: string,
  options: RequestInit = {}
) {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const token = session?.access_token;

  if (!token) {
    throw new Error(
      "No authenticated session."
    );
  }

  const headers = new Headers(
    options.headers
  );

  headers.set(
    "Authorization",
    `Bearer ${token}`
  );

  const response = await fetch(
    `${API_URL}${path}`,
    {
      ...options,
      headers,
    }
  );

  return response;
}
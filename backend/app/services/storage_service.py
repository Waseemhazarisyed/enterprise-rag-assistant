import os

from supabase import Client, create_client


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "Documents")


if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is not configured.")

if not SUPABASE_SECRET_KEY:
    raise RuntimeError("SUPABASE_SECRET_KEY is not configured.")


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY,
)


def upload_pdf(
    storage_path: str,
    file_bytes: bytes,
):
    return (
        supabase.storage
        .from_(SUPABASE_BUCKET)
        .upload(
            path=storage_path,
            file=file_bytes,
            file_options={
                "content-type": "application/pdf",
                "upsert": "false",
            },
        )
    )


def download_pdf(
    storage_path: str,
) -> bytes:
    return (
        supabase.storage
        .from_(SUPABASE_BUCKET)
        .download(storage_path)
    )


def delete_pdf(
    storage_path: str,
):
    return (
        supabase.storage
        .from_(SUPABASE_BUCKET)
        .remove([storage_path])
    )
from fastapi import Header, HTTPException

from app.services.storage_service import supabase


def get_current_user_id(
    authorization: str | None = Header(default=None),
) -> str:
    # No Authorization header
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    # Expected:
    # Authorization: Bearer <access_token>
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header.",
        )

    token = authorization.replace(
        "Bearer ",
        "",
        1,
    ).strip()

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Access token is missing.",
        )

    try:
        response = supabase.auth.get_user(token)

        user = response.user

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired access token.",
            )

        return str(user.id)

    except HTTPException:
        raise

    except Exception as error:
        print(
            "Authentication verification error:",
            error,
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token.",
        )
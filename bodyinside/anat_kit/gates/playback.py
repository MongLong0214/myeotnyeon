"""Bind the owner's final listening and phone check to the approved draft bytes."""


def checked(record, movie_sha256):
    return (
        record.get("movie_sha256") == movie_sha256
        and record.get("listened") is True
        and bool(str(record.get("listener") or "").strip())
        and bool(str(record.get("phone") or "").strip())
    )

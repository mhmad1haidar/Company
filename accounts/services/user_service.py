from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model

User = get_user_model()


class UserService:
    """Business logic for user profiles (keeps serializers/views thin)."""

    @staticmethod
    def update_profile(user: User, **fields: Any) -> User:
        allowed = {"first_name", "last_name", "email", "department", "job_title"}
        updated: list[str] = []
        for key in allowed:
            if key in fields and fields[key] is not None:
                setattr(user, key, fields[key])
                updated.append(key)
        if updated:
            user.save(update_fields=updated)
        return user

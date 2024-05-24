import json
import typing

import asyncpg

from server.models.user import User
from server.models.context import Context


def user(func):
    """
    Decorator to turn the User/user id passed to the function
    into a user_id param.
    """

    async def wrapper(self, user: Context | User | str, *args, **kwargs):
        if isinstance(user, Context):
            user_id = user.user.id
        elif isinstance(user, User):
            user_id = user.id
        elif isinstance(user, str):
            user_id = user
        else:
            raise ValueError("Invalid user type")

        return await func(self, user_id, *args, **kwargs)

    return wrapper


class Database:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    ## USER QUERIES ##

    async def get_user(self, value: str, by: str = "token") -> typing.Optional[User]:
        """Return the user object from the database given the "by"."""
        assert by in ("id", "spotify_id", "token"), "Invalid 'by' value"

        raw_user = await self.pool.fetchrow(
            f"SELECT * FROM users WHERE {by} = $1", value
        )
        return User(**raw_user) if raw_user else None

    async def add_user(self, user: User) -> None:
        """Add a user to the database."""
        await self.pool.execute(
            """
      INSERT INTO users (spotify_id, email, username, avatar, role, access_token, refresh_token, expires_at, token)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
      """,
            user.spotify_id,
            user.email,
            user.username,
            user.avatar,
            user.role,
            user.access_token,
            user.refresh_token,
            user.expires_at,
            user.token,
        )

    @user
    async def update_stat(self, user_id: str, key: str, add_value: int):
        """Update a stat."""

        assert key in (
            "generated_playlists",
            "daily_smashes",
            "filtered_playlists",
            "archived_songs",
            "weather_changes",
        ), "Invalid key"

        return await self.pool.fetchval(
            f"""
      INSERT INTO user_stats (user_id, {key}) VALUES ($1, $2)
      ON CONFLICT (user_id) DO UPDATE SET {key} = user_stats.{key} + $2
      RETURNING {key}
      """,
            user_id,
            add_value,
        )

    @user
    async def log_event(
        self, user_id: str, name: str, success: bool, data: dict = None
    ):
        """Log an event."""
        return await self.pool.execute(
            """
      INSERT INTO events (name, user_id, success, data)
      VALUES ($1, $2, $3, $4)
      """,
            name,
            user_id,
            success,
            json.dumps(data or {}),
        )

    @user
    async def enable_feature(self, user_id: str, feature: str):
        """Enable a feature."""
        return await self.pool.execute(
            "UPDATE users SET enabled_features = array_append(enabled_features, $1) WHERE id = $2",
            feature,
            user_id,
        )

    @user
    async def disable_feature(self, user_id: str, feature: str):
        """Disable a feature."""
        return await self.pool.execute(
            "UPDATE users SET enabled_features = array_remove(enabled_features, $1) WHERE id = $2",
            feature,
            user_id,
        )

    @user
    async def load_cache(self, user_id: str, key: str, default: str | type = None):
        """Load a cache value."""

        if default is list:
            default = "[]"

        val = (
            await self.pool.fetchval(
                "SELECT value FROM user_cache WHERE user_id = $1 AND KEY = $2",
                user_id,
                key,
            )
            or default
        )

        if val is not None:
            return json.loads(val)

    @user
    async def save_cache(self, user_id: str, key: str, value: dict | list):
        """Save a cache value."""
        return await self.pool.execute(
            """
      INSERT INTO user_cache (user_id, key, value)
      VALUES ($1, $2, $3)
      ON CONFLICT (user_id, key) DO UPDATE SET value = $3::jsonb
      """,
            user_id,
            key,
            json.dumps(value),
        )

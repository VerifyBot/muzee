from sanic import Request, text, json, empty

from server.models.context import Context
from .helpers.auth import authorized


async def route_hello(request: Request):
    return text("Hello, World!")


async def route_health(request: Request):
    return empty()


@authorized(force=False)
async def route_status(request: Request, ctx: Context):
    """
    Get the status of the server (active users)
    and the status of the user (is logged, profile)
    """

    served_users = await ctx.db.pool.fetchval(
        """
  SELECT COUNT(*) FROM user_stats WHERE
    generated_playlists > 0 OR 
    daily_smashes > 0 OR
    filtered_playlists > 0 OR
    archived_songs > 0 OR
    weather_changes > 0
  """
    )

    if ctx.user is None:
        return json(dict(served_users=served_users, status="online", is_logged=False))

    return json(
        dict(
            served_users=served_users,
            status="online",
            is_logged=True,
            profile=dict(
                username=ctx.user.username,
                photo=ctx.user.avatar,
                id=ctx.user.spotify_id,
            ),
            enabled_features=ctx.user.enabled_features,
        )
    )

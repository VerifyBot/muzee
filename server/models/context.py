import typing

from sanic import json

if typing.TYPE_CHECKING:
    from server.app import Muzee
    from server.models.user import User
    from server.database import Database
    from server.utils.spotify import Spotify, MySpotifyClient
    from sanic.response import JSONResponse


class Context:
    """
    Context for the routes to have as a parameter (dependency injection).
    that holds the database, the oauth functions object, etc.
    Note, this isn't relevant to sanic app.ctx or request.ctx.
    """

    def __init__(self, app: "Muzee", db: "Database", spotify: "Spotify"):
        self.app = app
        self.db = db
        self.spotify = spotify

        # this might be injected by the @authorized decorator
        self.user: User | None = None

        # this might be injected by the @use_spotify decorator
        self.sc: MySpotifyClient | None = None

    async def playlist_response(self, playlist_id: str) -> "JSONResponse":
        return json(
            {
                "status": "ok",
                "playlist": playlist_id,
                "image": await self.sc.get_image(playlist_id),
            }
        )

    async def toggle_feature(self, feature: str, enabled: bool) -> bool:
        """
        Toggle a feature for the user
        Returns False if the feature's state didn't change or was disabled.
        Return True if the feature was enabled.

        :param enabled: True to enable, False to disable
        """

        is_enabled = feature in self.user.enabled_features

        if is_enabled == enabled:  # no change
            return False

        if not enabled:  # disable
            await self.db.disable_feature(self.user, feature)
            return False

        # enable
        await self.db.enable_feature(self.user, feature)
        return True

import typing

if typing.TYPE_CHECKING:
    from server.models.user import User
    from server.database import Database
    from server.utils.spotify import Spotify, MySpotifyClient


class Context:
    """
    Context for the routes to have as a parameter (dependency injection).
    that holds the database, the oauth functions object, etc.
    Note, this isn't relevant to sanic app.ctx or request.ctx.
    """

    def __init__(self, db: "Database", spotify: "Spotify"):
        self.db = db
        self.spotify = spotify

        # this might be injected by the @authorized decorator
        self.user: User | None = None

        # this might be injected by the @use_spotify decorator
        self.sc: MySpotifyClient | None = None

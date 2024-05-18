import typing

from .models import User

if typing.TYPE_CHECKING:
  from .database import Database
  from .utils.spotify import Spotify


class Context:
  """
  Context for the routes to have as a parameter (dependency injection).
  that holds the database, the oauth functions object, etc.
  Note, this isn't relevant to sanic app.ctx or request.ctx.
  """

  def __init__(self, db: 'Database', spotify: 'Spotify'):
    self.db = db
    self.spotify = spotify

    self.user: User | None = None  # this might be injected by the @authorized decorator
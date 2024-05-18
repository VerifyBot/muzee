import contextlib
from functools import wraps

from sanic.response import json
from sanic import Request

from .database import Database


def authorized(func):
  """
  Check if the user is authorized to access the endpoint
  This is done by checking is the provided token in the Authorization header
  is in the database.

  If the user is authorized, the user object is added to the request context
  """

  @wraps(func)
  async def wrapper(request: Request, *args, **kwargs):
    # get the database dependency
    db: Database = request.app.ctx._dependencies.ctx.db

    # get the token from the Authorization header
    token = request.headers.get("Authorization")

    if not token:
      return json({"error": "unauthorized", "msg": "Authorization header is required"})

    # check if the token is in the database
    user = await db.get_user(token)

    if not user:
      return json({"error": "unauthorized", "msg": "Invalid token"})

    if (tzo := (request.json or {}).get('timezone_offset')) and user.timezone_offset != tzo:
      if -12 * 60 <= tzo <= 12 * 60:
        await db.pool.execute(
          "UPDATE users SET timezone_offset = $1 WHERE id = $2",
          tzo, user.id
        )
        user.timezone_offset = tzo
        print(f'Updated timezone_offset for user')


    # inject the user object as a parameter
    assert 'ctx' in kwargs, "You must provide the ctx object in the kwargs"
    kwargs['ctx'].user = user

    return await func(request, *args, **kwargs)

  return wrapper

def maybe_authorized(func):
  """
  Just like the authorized decorator, but if the user is not authorized,
  the user object is None
  """

  @wraps(func)
  async def wrapper(request: Request, *args, **kwargs):
    # get the database dependency
    db: Database = request.app.ctx._dependencies.ctx.db

    # get the token from the Authorization header
    token = request.headers.get("Authorization")

    if token:
      # check if the token is in the database
      user = await db.get_user(token)

      if user:
        # inject the user object as a parameter
        assert 'ctx' in kwargs, "You must provide the ctx object in the kwargs"

        kwargs['ctx'].user = user

    return await func(request, *args, **kwargs)

  return wrapper

def use_spotify(func):
  """
  Inject the Spotify Client object into the function
  """

  @wraps(func)
  async def wrapper(request: Request, *args, **kwargs):
    # get the database dependency
    assert 'ctx' in kwargs, "You must provide the ctx object in the kwargs"

    sc = await kwargs['ctx'].spotify.get_client(user=kwargs['ctx'].user)
    kwargs['sc'] = sc

    try:
      return await func(request, *args, **kwargs)
    finally:
      await sc.close()

  return wrapper

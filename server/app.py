import copy
from datetime import datetime
import aiocron
import pydantic
import pytz

from sanic import Sanic, Blueprint, Request, json
from sanic_ext import Extend

import asyncpg
from aiocache import SimpleMemoryCache

import json as json_lib

import configparser
import logging

from sanic_ext.exceptions import ValidationError

from .database import Database
from .models import User
from .routes.utils.actions import run_daily_smash, run_public_liked

from .utils import spotify as sp

from .context import Context




class Muzee:
  def __init__(self, *args, app: Sanic, config: configparser.ConfigParser, mode: str = "dev", **kwargs):
    self.app = app
    self.config = config



    self.ctx: Context = None  # created in setup_hook

    # CORS for all origins. todo: change this to the website url
    app.config.CORS_ORIGINS = "*"
    Extend(app)

    # register listeners for database connection
    self.register_listeners()

    ## Global Variables ##
    self.setup_globals(mode)

    ## Routes ##
    self.load_routes()

    ## Error Handlers ##
    self.app.error_handler.add(ValidationError, self.on_pydantic_error)  # pydantic errors
    self.app.error_handler.add(AssertionError, self.on_assertion_error)  # assertion errors



  async def daily_smash_task(self):
    """
    Task to run every 5 minutes and look for
    daily smashes that need to be generated
    """


    # i dont trust aiocron enough...
    now = datetime.now(pytz.UTC)
    rounded_minute = now.minute - (now.minute % 5)
    rounded_now = now.replace(minute=rounded_minute, second=0, microsecond=0).time()

    logging.info(f'daily smash task ({rounded_now.replace()} UTC)')

    users = await self.ctx.db.pool.fetch(
      """
      SELECT * FROM users
      WHERE
        'daily-smash' = ANY(enabled_features)
        AND ds_playlist IS NOT NULL
        AND ds_songs_count > 0
        AND ds_update_at = $1
      """,
      rounded_now
    )

    for raw_user in users:
      ctx = copy.copy(self.ctx)
      ctx.user = User(**raw_user)

      print(f'Running daily smash for {ctx.user.username}')
      await run_daily_smash(ctx=ctx)

    # print(f"DS users for {rounded_now.strftime('%H:%M')}:\n{'\n'.join(str(u) for u in users)}")

  async def public_liked_task(self):
    """
    Task to run every 30 minutes
    and update the public liked playlists
    """

    users = await self.ctx.db.pool.fetch(
      """
      SELECT * FROM users
      WHERE
        'public-liked' = ANY(enabled_features)
        AND pl_playlist IS NOT NULL
      """
    )

    for raw_user in users:
      ctx = copy.copy(self.ctx)
      ctx.user = User(**raw_user)

      print(f'Running public liked for {ctx.user.username}')
      await run_public_liked(ctx=ctx)



  async def on_pydantic_error(self, request: Request, exception: ValidationError):
    exc: pydantic.ValidationError = exception.extra['exception']

    return json({"error": {
      "type": "ValidationError",
      "detail": json_lib.loads(exc.json())
    }})

  async def on_assertion_error(self, request: Request, exception: AssertionError):
    return json({"error": {
      "type": "AssertionError",
      "detail": str(exception)
    }})

  async def setup_hook(self, app: Sanic):
    logging.info("Setting up db connection")



    pool = await asyncpg.create_pool(
      user=self.config.get("database", "username"),
      password=self.config.get("database", "password"),
      database=self.config.get("database", "database"),
    )

    db_conn = Database(pool)
    app.ctx.db = db_conn

    spotify = sp.Spotify(
      client_id=self.config.get("spotify", "client_id"),
      client_secret=self.config.get("spotify", "client_secret"),
      scope=self.config.get("spotify", "scope"),
      server_url=app.ctx.SERVER_URL,
      db=db_conn
    )

    ctx = Context(
      db=db_conn,
      spotify=spotify
    )

    self.ctx = ctx
    app.ext.dependency(ctx, name="ctx")


    ## Tasks ##
    aiocron.crontab('*/5 * * * * 15', func=self.daily_smash_task, start=True)
    aiocron.crontab('0,30 * * * *', func=self.public_liked_task, start=True)


  async def close_hook(self, app: Sanic):
    logging.info("Closing db connection")
    db_conn: Database = app.ctx.db
    await db_conn.pool.close()

  def register_listeners(self):
    self.app.register_listener(self.setup_hook, "before_server_start")
    self.app.register_listener(self.close_hook, "before_server_stop")

  def setup_globals(self, mode: str):
    DEBUG_MODE = mode == "dev"
    server_section = "app" if DEBUG_MODE else "prod_app"

    self.app.ctx.states_cache = SimpleMemoryCache(ttl=300)

    self.app.ctx.config = self.config
    self.app.ctx.DEBUG_MODE = DEBUG_MODE
    self.app.ctx.APP_ADMINS = set(uid for uid in self.config.get("misc", "admins").split(","))
    self.app.ctx.SERVER_URL = self.config.get(server_section, "server_url")
    self.app.ctx.WEBSITE_URL = self.config.get(server_section, "website_url")



  def load_routes(self):
    # OAuth
    from .routes.oauth2 import route_connect, route_callback

    oauth2 = Blueprint("oauth2", url_prefix="/oauth2")
    oauth2.add_route(route_connect, "/connect")
    oauth2.add_route(route_callback, "/callback")
    self.app.blueprint(oauth2)

    # Misc
    from .routes.misc import route_hello, route_health, route_status

    self.app.add_route(route_hello, "/", methods=["GET"])
    self.app.add_route(route_health, "/health", methods=["GET"])
    self.app.add_route(route_status, "/status", methods=["GET"])

    # Features
    from .routes.features import route_generate_playlist
    from .routes.features import route_toggle_daily_smash, route_feature_details
    from .routes.features import route_language_filter
    from .routes.features import route_toggle_public_liked

    self.app.add_route(route_generate_playlist, "/generate_playlist", methods=["POST"])
    self.app.add_route(route_toggle_daily_smash, "/toggle_daily_smash", methods=["POST"])
    self.app.add_route(route_feature_details, "/feature_details", methods=["POST"])
    self.app.add_route(route_language_filter, "/language_filter", methods=["POST"])
    self.app.add_route(route_toggle_public_liked, "/toggle_public_liked", methods=["POST"])



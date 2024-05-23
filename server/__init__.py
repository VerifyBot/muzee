from sanic import Sanic
import os
import configparser
import coloredlogs
import logging

from server.database import Database
from server.app import Muzee

coloredlogs.install(level="INFO")

# since we're running this as a module, the current working directory is the parent directory
# this is changed here to the server directory, for simpler file access
os.chdir(os.path.dirname(os.path.abspath(__file__)))
logging.info(f"Current working directory: {os.getcwd()}")

config = configparser.ConfigParser()
config.read("./config.ini")


def _create_app(mode: str = "dev") -> Sanic:
    """
    Create the Sanic app
    """

    app = Sanic("Muzee")

    # Extend the app with our custom functionality
    Muzee(app=app, config=config, mode=mode)

    return app


def dev() -> Sanic:
    """
    Run a development app

    Usage:
      sanic server:dev
    """
    return _create_app(mode="dev")


def prod() -> Sanic:
    """
    Run a production app

    Usage:
      sanic server:prod
    """

    return _create_app(mode="prod")

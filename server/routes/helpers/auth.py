import contextlib
import copy
from functools import wraps

import pytz
from sanic.response import json
from sanic import Request
import logging
from server.database import Database


def authorized(force: bool = True):
    """
    Check if the user is authorized to access the endpoint
    This is done by checking is the provided token in the Authorization header
    is in the database.

    If the user is authorized, the user object is added to the request context

    If not and force is enabled (default), an error is returned
    If not and force is disabled, the ctx.user object will be None
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            db: Database = request.app.ctx._dependencies.ctx.db
            token = request.headers.get("Authorization")

            if not token:
                if force:
                    return json(
                        {
                            "error": "unauthorized",
                            "msg": "Authorization header is required",
                        }
                    )
                return await func(request, *args, **kwargs)

            # check if the token is in the database
            user = await db.get_user(token)

            if not user:
                if force:
                    return json({"error": "unauthorized", "msg": "Invalid token"})
                return await func(request, *args, **kwargs)

            if (tz := request.headers.get("Timezone")) and user.timezone != tz:
                # is valid?
                with contextlib.suppress(pytz.UnknownTimeZoneError):
                    pytz.timezone(
                        tz
                    )  # raises and exists the context manager if the timezone is invalid

                    await db.pool.execute(
                        "UPDATE users SET timezone = $1 WHERE id = $2", tz, user.id
                    )
                    user.timezone = tz
                    logging.info(f"Updated timezone for {user.username}: {tz}")

            # inject the user object as a parameter
            assert "ctx" in kwargs, "You must provide the ctx object in the kwargs"
            kwargs["ctx"] = copy.copy(kwargs["ctx"])
            kwargs["ctx"].user = user

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator

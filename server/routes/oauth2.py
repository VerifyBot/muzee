from urllib.parse import urlencode
from datetime import datetime, timedelta
import uuid
import logging

from sanic import Request, json, redirect

from server.models.user import User, RoleEnum
from server.models.context import Context
from server.utils.spotify import OAuthError


# GET /oauth2/connect
async def route_connect(request: Request):
    """
    On the "Connect to Discord" button click,
    redirect the user to the Discord OAuth page
    """

    state = uuid.uuid4().hex
    await request.app.ctx.states_cache.set(state, True)

    return redirect(
        "https://accounts.spotify.com/authorize?"
        + urlencode(
            dict(
                response_type="code",
                client_id=request.app.ctx.config.get("spotify", "client_id"),
                scope=request.app.ctx.config.get("spotify", "scope"),
                redirect_uri=request.app.ctx.SERVER_URL + "/oauth2/callback",
                state=state,
                show_dialog="false",
            )
        )
    )


# GET /oauth2/callback
async def route_callback(request: Request, ctx: Context):
    """
    On the callback from Discord,
    get the user's access token and refresh token
    """
    state = request.args.get("state")
    code = request.args.get("code")
    error = request.args.get("error")
    error_description = request.args.get("error_description")

    cached_state = await request.app.ctx.states_cache.get(state)

    if not cached_state:
        return json({"error": "state mismatch"})

    await request.app.ctx.states_cache.delete(state)

    if error:
        return json({"error": "oauth_failed", "msg": f"{error}: {error_description}"})

    # get access token
    try:
        js = await ctx.spotify.get_access_token_from_code(code)
    except OAuthError as e:
        return json({"error": "oauth_error", "msg": str(e)})

    if set(js["scope"].split(" ")) != set(
        request.app.ctx.config.get("spotify", "scope").split(" ")
    ):
        return json({"error": "scope mismatch"})

    access_token = js["access_token"]
    refresh_token = js["refresh_token"]
    expires_in = js["expires_in"]
    expires_at = datetime.now() + timedelta(seconds=expires_in)

    # get user info
    try:
        me = await ctx.spotify.fetch_user_info(
            access_token=access_token, refresh_token=refresh_token
        )

    except Exception as e:
        logging.warning(f"Failed to fetch user info after /callback", exc_info=e)
        return json({"error": "failed to fetch user info"})

    # is user already in the db?
    logging.info(me)
    user = await ctx.db.get_user(me.id, by="spotify_id")

    if user:
        return redirect(request.app.ctx.WEBSITE_URL + f"/?token={user.token}")

    # generate a token for the user
    token = uuid.uuid4().hex

    user = User(
        spotify_id=me.id,
        email=me.email,
        username=me.display_name,
        avatar=me.images[0].url if me.images else None,
        role=RoleEnum.admin if me.id in request.app.ctx.APP_ADMINS else RoleEnum.user,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        token=token,
    )

    await ctx.db.add_user(user)

    # the user can now send requests to the endpoints below with the token as an Authorization header (see @authorized)
    return redirect(request.app.ctx.WEBSITE_URL + f"/?token={token}")

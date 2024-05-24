import re

from datetime import datetime
import pydantic
import pytz
from sanic import Request, json
from sanic_ext import validate

from server.models.context import Context
from server import actions

from server.utils.decos import use_spotify
from .helpers.auth import authorized

playlist_regex = (
    r"(?:https:\/\/open\.spotify\.com\/playlist\/)?([a-zA-Z0-9]{22})(?:\?.+)?"
)


class GeneratePlaylistData(pydantic.BaseModel):
    topic: pydantic.constr(min_length=2, max_length=100)
    songs_count: pydantic.conint(ge=5, le=100)


class ToggleDailySmashData(pydantic.BaseModel):
    enabled: bool
    update_at: pydantic.conint(ge=0, le=1440)
    songs_count: pydantic.conint(ge=5, le=100)


class LanguageFilterData(pydantic.BaseModel):
    playlist: str = pydantic.Field(pattern=playlist_regex, min_length=22)
    keep_chars: pydantic.constr(min_length=1, max_length=150)

    @pydantic.computed_field
    @property
    def playlist_id(self) -> str:
        return re.match(playlist_regex, self.playlist).groups()[0]


class TogglePublicLikedData(pydantic.BaseModel):
    enabled: bool


class ToggleLiveWeatherData(pydantic.BaseModel):
    enabled: bool
    playlist: str = pydantic.Field(pattern=playlist_regex, min_length=22)
    lat: pydantic.confloat(ge=-90, le=90)
    lon: pydantic.confloat(ge=-180, le=180)
    scale: str = pydantic.Field(pattern=r"^(celcius|fahrenheit|kelvin)$")

    @pydantic.computed_field
    @property
    def playlist_id(self) -> str:
        return re.match(playlist_regex, self.playlist).groups()[0]


class ToggleLikedArchiveData(pydantic.BaseModel):
    enabled: bool


@authorized()
@validate(json=GeneratePlaylistData)
async def route_generate_playlist(
    request: Request, ctx: Context, body: GeneratePlaylistData
):
    """
    Generate a playlist for the user based on the topic and the number of songs
    """

    topics = [topic.strip() for topic in body.topic.split(",")][:5]
    js = await actions.run_generate_playlist(
        ctx=ctx, topics=topics, songs_count=body.songs_count
    )
    return json(js)


@authorized()
@validate(json=ToggleDailySmashData)
@use_spotify
async def route_toggle_daily_smash(
    request: Request, ctx: Context, body: ToggleDailySmashData
):
    """
    Toggle the daily smash feature
    """

    smash_enabled = "daily-smash" in ctx.user.enabled_features

    if smash_enabled == body.enabled:  # no change
        return json(
            {"status": "ok", "image": await ctx.sc.get_image(ctx.user.ds_playlist)}
        )

    # disable
    if not body.enabled:
        # remove the feature (remove daily-smash from the array of features)
        await ctx.db.disable_feature(ctx.user, "daily-smash")
        return json({"status": "ok"})

    # enable
    await ctx.db.enable_feature(ctx.user, "daily-smash")

    # ds_update_at will always be in UTC
    hours, minutes = divmod(body.update_at, 60)
    clients_time = datetime.now(ctx.user.tz).replace(
        hour=hours, minute=minutes, second=0, microsecond=0
    )
    utc_time = clients_time.astimezone(pytz.utc).time()

    # has a daily smash already?
    if ctx.user.ds_playlist:
        # need to update anything?
        if (
            ctx.user.ds_songs_count != body.songs_count
            or ctx.user.ds_update_at != utc_time
        ):
            # need to update the playlist
            await ctx.db.pool.execute(
                "UPDATE users SET ds_songs_count = $1, ds_update_at = $2 WHERE id = $3",
                body.songs_count,
                utc_time,
                ctx.user.id,
            )

        return json(
            {
                "status": "ok",
                "playlist": ctx.user.ds_playlist,
                "image": await ctx.sc.get_image(ctx.user.ds_playlist),
            }
        )

    else:
        # create a new playlist ... update database
        # update context
        ctx.user.ds_songs_count = body.songs_count
        playlist = await actions.run_daily_smash(ctx=ctx, create=True)
        ctx.user.ds_playlist = playlist

        await ctx.db.pool.execute(
            "UPDATE users SET ds_playlist = $1, ds_songs_count = $2, ds_update_at = $3 WHERE id = $4",
            playlist,
            body.songs_count,
            utc_time,
            ctx.user.id,
        )

        return json(
            {
                "status": "ok",
                "playlist": ctx.user.ds_playlist,
                "image": await ctx.sc.get_image(
                    ctx.user.ds_playlist
                ),  # need an updated version
            }
        )


@authorized()
@use_spotify
async def route_feature_details(request: Request, ctx: Context):
    """
    Get the details of a feature (like the daily smash)
    """

    feature = request.json.get("key")
    assert feature in (
        "daily-smash",
        "public-liked",
        "live-weather",
        "liked-archive",
    ), "Route details for this feature is not implemented."

    if feature not in ctx.user.enabled_features:
        return json({"status": "disabled"})

    playlist = {
        "daily-smash": ctx.user.ds_playlist,
        "public-liked": ctx.user.pl_playlist,
        "live-weather": ctx.user.lw_playlist,
        "liked-archive": ctx.user.la_playlist,
    }

    js = await ctx.playlist_response(playlist[feature])

    if feature == "daily-smash":
        js.update({"songs_count": ctx.user.ds_songs_count})
    elif feature == "live-weather":
        js.update(
            {"lat": ctx.user.lw_lat, "lon": ctx.user.lw_lon, "scale": ctx.user.lw_scale}
        )

    return js


@authorized()
@validate(json=LanguageFilterData)
@use_spotify
async def route_language_filter(
    request: Request, ctx: Context, body: LanguageFilterData
):
    """
    Generate a playlist for the user based on the topic and the number of songs
    """

    # get the spotify client to generate the playlist

    # playlist name?
    js = await ctx.sc.get(f"playlists/{body.playlist_id}", fields="name")
    pname = js["name"]

    # get songs
    tracks = await ctx.sc.get_all_playlist_tracks(
        body.playlist_id, fields="items(type,track(is_local,uri,name))"
    )
    keep_tracks = set()

    for track in tracks:
        name = track["track"]["name"]

        if any(c in body.keep_chars for c in name):
            keep_tracks.add(track["track"]["uri"])

    # create a new playlist
    filtered_pname = f"Filtered {pname}"
    playlist = await ctx.sc.create_playlist(
        user=ctx.user.spotify_id,
        name=filtered_pname,
        description=f"🪄 Filtered by Muzee @ {ctx.user.now().strftime('%H:%M %d/%m/%Y')}.",
    )

    await ctx.sc.add_tracks_to_playlist(playlist.id, list(keep_tracks))

    return json(
        {
            "status": "ok",
            "id": playlist.id,
            "songs_count": len(keep_tracks),
            "image": None,  # await sc.get_image(playlist.id),
            "name": filtered_pname,
        }
    )


@authorized()
@validate(json=TogglePublicLikedData)
@use_spotify
async def route_toggle_public_liked(
    request: Request, ctx: Context, body: TogglePublicLikedData
):
    """
    Toggle the public liked feature
    """

    liked_enabled = "public-liked" in ctx.user.enabled_features

    if liked_enabled == body.enabled:  # no change
        return json(
            {"status": "ok", "image": await ctx.sc.get_image(ctx.user.pl_playlist)}
        )

    # disable
    if not body.enabled:
        # remove the feature (remove public-liked from the array of features)
        await ctx.db.disable_feature(ctx.user, "public-liked")
        return json({"status": "ok"})

    # enable
    await ctx.db.enable_feature(ctx.user, "public-liked")

    # has a public liked already?
    if ctx.user.pl_playlist:
        return json(
            {
                "status": "ok",
                "playlist": ctx.user.pl_playlist,
                "image": await ctx.sc.get_image(ctx.user.pl_playlist),
            }
        )

    else:
        playlist = await actions.run_public_liked(ctx=ctx, create=True)
        ctx.user.pl_playlist = playlist

        await ctx.db.pool.execute(
            "UPDATE users SET pl_playlist = $1 WHERE id = $2", playlist, ctx.user.id
        )

        return json(
            {
                "status": "ok",
                "playlist": ctx.user.pl_playlist,
                "image": await ctx.sc.get_image(ctx.user.pl_playlist),
            }
        )


@authorized()
@validate(json=ToggleLiveWeatherData)
@use_spotify
async def route_toggle_live_weather(
    request: Request, ctx: Context, body: ToggleLiveWeatherData
):
    """
    Toggle the live weather feature
    """

    if not await ctx.toggle_feature("live-weather", body.enabled):
        print("disabled or no change")
        return await ctx.playlist_response(ctx.user.lw_playlist)

    print("wow change")

    first_time = not ctx.user.lw_playlist

    # has a live weather playlist already?
    if first_time or (
        not first_time
        and (
            ctx.user.lw_playlist != body.playlist_id
            or ctx.user.lw_lat != body.lat
            or ctx.user.lw_lon != body.lon
            or ctx.user.lw_scale != body.scale
        )
    ):
        await ctx.db.pool.execute(
            "UPDATE users SET lw_playlist = $1, lw_lat = $2, lw_lon = $3, lw_scale = $4 WHERE id = $5",
            body.playlist_id,
            body.lat,
            body.lon,
            body.scale,
            ctx.user.id,
        )
        ctx.user.lw_playlist = body.playlist_id
        ctx.user.lw_lat = body.lat
        ctx.user.lw_lon = body.lon
        ctx.user.lw_scale = body.scale

    if first_time:
        print("running...")
        await actions.run_live_weather(ctx=ctx)

    return await ctx.playlist_response(ctx.user.lw_playlist)


@authorized()
@validate(json=ToggleLikedArchiveData)
@use_spotify
async def route_toggle_liked_archive(
    request: Request, ctx: Context, body: ToggleLikedArchiveData
):
    """
    Toggle the liked archive feature
    """

    if not await ctx.toggle_feature("liked-archive", body.enabled):
        return await ctx.playlist_response(ctx.user.la_playlist)

    if ctx.user.la_playlist is None:
        playlist_id = await actions.run_liked_archive(ctx=ctx, create=True)

        await ctx.db.pool.execute(
            """
            UPDATE users
            SET la_playlist = $1
            WHERE id = $2
            """,
            playlist_id,
            ctx.user.id,
        )
        ctx.user.la_playlist = playlist_id

    return await ctx.playlist_response(ctx.user.la_playlist)

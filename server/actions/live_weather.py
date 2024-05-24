import itertools
import logging
import random

import aiohttp

from server.models.context import Context
from server.utils.decos import use_spotify


@use_spotify
async def run_live_weather(ctx: Context):
    """
    🌦️ Live Weather

    Edit the description of the user's Live Weather playlist to include the current weather.
    """

    assert (
        ctx.user.lw_playlist
        and ctx.user.lw_lat
        and ctx.user.lw_lon
        and ctx.user.lw_scale
    ), "Live Weather isn't configured."

    # get the weather
    api_key = ctx.app.config.get("weather", "api_key")

    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{ctx.user.lw_lat},{ctx.user.lw_lon}"
    params = dict(unitGroup="metric", key=api_key, contentType="json")

    async with aiohttp.ClientSession() as cs:
        async with cs.get(url, params=params) as resp:
            js = await resp.json()

    if not (cc := js.get("currentConditions")):
        logging.warning(
            f"Could not get the current weather in {ctx.user.lw_lat},{ctx.user.lw_lon} for {ctx.user.username}: {js}"
        )
        return

    temp = cc["temp"]
    humidity = cc["humidity"]
    wind = cc["windspeed"]

    if ctx.user.lw_scale != "celcius":
        temp = (
            temp * 1.8 + 32 if ctx.user.lw_scale == "fahrenheit" else temp + 273.15
        )  # kelvin
    temp_symbol = dict(celcius="C", fahrenheit="F", kelvin="K")[ctx.user.lw_scale]

    # update the playlist description
    desc = f"🌡️ {temp}°{temp_symbol} | Humidity: 💧 {humidity}% Wind: 💨 {wind}km/h"

    await ctx.sc.edit_playlist(ctx.user.lw_playlist, description=desc)

    await ctx.db.log_event(
        ctx.user,
        "live_weather",
        success=True,
        data=dict(
            request={
                "playlist_id": ctx.user.lw_playlist,
                "temp": temp,
                "humidity": humidity,
                "wind": wind,
            }
        ),
    )

    return desc

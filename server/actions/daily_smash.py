import itertools
import logging
import random

from server.models.context import Context
from server.utils.decos import use_spotify


@use_spotify
async def run_daily_smash(ctx: Context, create: bool = False):
    """
    🥒 Create a playlist with random songs from the user's library playlists.

    :param create: Create a new playlist for the Daily Smash
    """

    assert ctx.user.ds_playlist or create is True, "No playlist set for Daily Smash."

    if create:
        playlist = await ctx.sc.create_playlist(
            user=ctx.user.spotify_id, name=f"Daily Smash", description="🕺🕺🕺"
        )
        ds_playlist_id = playlist.id
    else:
        ds_playlist_id = ctx.user.ds_playlist

        # does it exist? no point to continue if we can't add songs to it.
        js = await ctx.sc.get(f"playlists/{ds_playlist_id}", fields="id")

        if js.get("error"):
            return

    # get the user's library playlists
    playlists = await ctx.sc.get_user_playlists(ctx.user.spotify_id)

    if len(playlists) == 0:  # nothing to work with
        return ds_playlist_id if create else None

    random.shuffle(playlists)
    source_playlists_iter = itertools.cycle(playlists)

    songs = set()
    empty_tries = 0

    while len(songs) < (songs_count := ctx.user.ds_songs_count):
        if empty_tries > 3:  # give up
            break

        playlist = next(source_playlists_iter)

        take_songs = min(
            10, max(2, random.randint(-10, 10) + songs_count // len(playlists))
        )

        # get playlist songs count
        resp = await ctx.sc.get(f"playlists/{playlist.id}", fields="tracks.total")
        playlist_songs_count = resp["tracks"]["total"]

        if playlist_songs_count == 0:
            empty_tries += 1
            continue

        take_offset = random.randint(0, max(0, playlist_songs_count - take_songs))

        # get songs from playlist
        resp = await ctx.sc.get(
            f"playlists/{playlist.id}/tracks",
            limit=min(50, take_songs),
            fields="items(is_local,track(uri,type))",
            offset=take_offset,
        )

        songs.update(
            {
                id
                for t in resp["items"]
                if (id := t["track"]["uri"]) is not None
                and t["track"]["type"] == "track"
                and not t["is_local"]
            }
        )

        logging.info(f'+ Added {len(resp["items"])} songs from {playlist.name}')

    # clear it
    await ctx.sc.put(f"playlists/{ds_playlist_id}/tracks", uris=[], body=True)

    # fill it
    await ctx.sc.add_tracks_to_playlist(ds_playlist_id, list(songs)[:songs_count])

    # edit last update time
    await ctx.sc.edit_playlist(
        ds_playlist_id,
        description=f'🕺 Last updated by Muzee @ {ctx.user.now().strftime("%H:%M %d/%m/%Y")}.',
    )

    await ctx.db.log_event(
        ctx.user,
        "daily_smash",
        success=True,
        data=dict(
            request={
                "playlist_id": ds_playlist_id,
                "songs_count": songs_count,
                "create": create,
            }
        ),
    )

    return ds_playlist_id

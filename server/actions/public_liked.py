from server.models.context import Context
from server.utils.decos import use_spotify


@use_spotify
async def run_public_liked(ctx: Context, create: bool = False):
    """
    🩷 Create a public playlist from the user's unshareable Liked Songs.

    :param create: Create a new playlist for the Public Liked Songs
    """

    assert ctx.user.pl_playlist or create is True, "No playlist set for Public Liked."

    if create:
        playlist = await ctx.sc.create_playlist(
            user=ctx.user.spotify_id,
            name=f"Public Liked - {ctx.user.username}",
            description="🎸 Here is what I listen to...",
            public=True,
        )
        pl_playlist_id = playlist.id
    else:
        pl_playlist_id = ctx.user.pl_playlist

        # does it exist? no point to continue if we can't add songs to it.
        js = await ctx.sc.get(f"playlists/{pl_playlist_id}", fields="id")

        if js.get("error"):
            return

    # method: remove songs that are not in liked and add songs that are missing

    # get the user's liked songs
    liked = await ctx.sc.get_all_playlist_tracks("likedsongs")
    mirror = await ctx.sc.get_all_playlist_tracks(
        pl_playlist_id, fields="items(is_local,track(type,uri))"
    )

    liked_uris = {t["track"]["uri"] for t in liked}
    mirror_uris = {t["track"]["uri"] for t in mirror}

    remove_uris = mirror_uris - liked_uris
    add_uris = liked_uris - mirror_uris

    if remove_uris:
        await ctx.sc.delete_playlist_tracks(pl_playlist_id, list(remove_uris))

    if add_uris:
        await ctx.sc.add_tracks_to_playlist(pl_playlist_id, list(add_uris))

    # edit last update time
    await ctx.sc.edit_playlist(
        pl_playlist_id,
        description=f'🩷 Last updated by Muzee @ {ctx.user.now().strftime("%H:%M %d/%m/%Y")}.',
    )

    await ctx.db.log_event(
        ctx.user,
        "public_liked",
        success=True,
        data=dict(request={"playlist_id": pl_playlist_id, "create": create}),
    )

    return pl_playlist_id

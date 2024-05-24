import logging

from server.models.context import Context
from server.utils.decos import use_spotify


@use_spotify
async def run_liked_archive(ctx: Context, create: bool = False):
    """
    📦 Liked Archive

    Update the liked archive playlist with the latest unliked songs.
    Save current liked songs in the database for next-run comparison.

    :param create: Create a new playlist for the Liked Archive songs
    """

    assert ctx.user.la_playlist or create is True, "No playlist set for Liked Archive."

    if create:
        playlist = await ctx.sc.create_playlist(
            user=ctx.user.spotify_id,
            name=f"Liked Archive - {ctx.user.username}",
            description="💥 songs i used to like",
        )

        # save liked
        liked = await ctx.sc.get_all_playlist_tracks("likedsongs")
        liked = [t["track"]["uri"] for t in liked]
        await ctx.db.save_cache(ctx.user, "liked_songs", liked)

        await ctx.db.log_event(
            ctx.user,
            "liked_archive",
            success=True,
            data=dict(request={"playlist_id": playlist.id, "create": create}),
        )

        return playlist.id

    # pull the old liked songs from the database
    old_liked = await ctx.db.load_cache(ctx.user, "liked_songs", default=list)

    # get the user's liked songs count
    # this is currently the best way to check if the playlist has changed,
    # as spotify doesnt provide a snapshot_id for the liked songs playlist.
    # tldr; spotify api is not perfect \_(ツ)_/¯
    now_liked = [
        t["track"]["uri"] for t in await ctx.sc.get_all_playlist_tracks("likedsongs")
    ]

    unliked = list(set(old_liked) - set(now_liked))

    logging.info(f"Old liked: {len(old_liked)} | Now liked: {len(now_liked)}")

    if now_liked != old_liked:
        logging.info(f"liked songs have changed for {ctx.user.username}")
        await ctx.db.save_cache(ctx.user, "liked_songs", now_liked)

    if not unliked:
        return

    # add the unliked songs to the archive
    await ctx.sc.add_tracks_to_playlist(ctx.user.la_playlist, unliked)
    await ctx.db.log_event(
        ctx.user,
        "liked_archive",
        success=True,
        data=dict(
            request={
                "playlist_id": ctx.user.la_playlist,
                "create": create,
                "added": unliked,
            }
        ),
    )
    logging.info(
        f"updated liked archive for {ctx.user.username} +{len(unliked)} unliked"
    )

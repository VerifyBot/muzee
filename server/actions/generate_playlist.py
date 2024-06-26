import random

from server.models.context import Context
from server.utils.decos import use_spotify


@use_spotify
async def run_generate_playlist(ctx: Context, topics: list[str], songs_count: int):
    """
    🎲 Playlist Generator

    Create a random playlist based on a topic or a list of topics.
    The songs will be taken from playlists in the topic's search results.
    """

    playlists = []

    for topic in topics:
        resp = await ctx.sc.get("search", q=topic, type="playlist", limit=5)
        playlists += resp["playlists"]["items"]

    total_songs_available = sum(p["tracks"]["total"] for p in playlists)

    if total_songs_available == 0:
        return dict(error="No songs found")

    # shuffle results
    random.shuffle(playlists)

    songs_per_playlist = (songs_count // len(playlists)) + 15

    songs = set()

    for p in playlists:
        # get the songs
        offset = 0

        if (count := p["tracks"]["total"]) > songs_per_playlist:
            offset = random.randint(0, count - songs_per_playlist)

        resp = await ctx.sc.get(
            f'playlists/{p["id"]}/tracks',
            playlist_id=p["id"],
            limit=min(50, songs_per_playlist),
            fields="items(track(uri))",
            offset=offset,
        )

        # add the songs
        songs |= set(it["track"]["uri"] for it in resp["items"])

    songs = list(songs)
    random.shuffle(songs)
    songs = songs[:songs_count]

    generation_id = await ctx.db.update_stat(ctx.user, "generated_playlists", +1)

    # generate the playlist
    resp = await ctx.sc.create_playlist(
        user=ctx.user.spotify_id,
        name=f"Generated #{generation_id} - {', '.join(topics)}",
        description=f"🪄 Generated by Muzee @ {ctx.user.now().strftime('%H:%M %d/%m/%Y')}.",
    )

    # add the songs
    await ctx.sc.playlist_add_tracks(resp.id, *songs)

    result = dict(
        id=resp.id,
        name=resp.name,
        image=await ctx.sc.get_image(resp.id),
        songs_count=len(songs),
    )

    await ctx.db.log_event(
        ctx.user,
        "generate_playlist",
        success=True,
        data=dict(
            request={"topics": topics, "songs_count": songs_count}, result=result
        ),
    )

    return result

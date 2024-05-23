import itertools
import random

from ...context import Context
from ...decos import use_spotify
from ...utils.spotify import MySpotifyClient


@use_spotify
async def run_daily_smash(ctx: Context, sc: MySpotifyClient, create: bool = False):
  """
  🥒 Create a playlist with random songs from the user's library playlists.

  :param create: Create a new playlist for the Daily Smash
  """

  assert ctx.user.ds_playlist or create is True, "No playlist set for Daily Smash."

  if create:
    playlist = await sc.create_playlist(
      user=ctx.user.spotify_id,
      name=f'Daily Smash',
      description='🕺🕺🕺'
    )
    ds_playlist_id = playlist.id
  else:
    ds_playlist_id = ctx.user.ds_playlist

    # does it exist? no point to continue if we can't add songs to it.
    js = await sc.get(f'playlists/{ds_playlist_id}', fields='id')

    if js.get('error'):
      return

  # get the user's library playlists
  playlists = await sc.get_user_playlists(ctx.user.spotify_id)

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

    take_songs = min(10, max(2, random.randint(-10, 10) + songs_count // len(playlists)))

    # get playlist songs count
    resp = await sc.get(f'playlists/{playlist.id}', fields='tracks.total')
    playlist_songs_count = resp['tracks']['total']

    if playlist_songs_count == 0:
      empty_tries += 1
      continue

    take_offset = random.randint(0, max(0, playlist_songs_count - take_songs))

    # get songs from playlist
    resp = await sc.get(
      f'playlists/{playlist.id}/tracks',
      limit=min(50, take_songs),
      fields='items(is_local,track(uri,type))',
      offset=take_offset
    )

    songs.update({id for t in resp['items'] if (id := t['track']['uri']) is not None and t['track']['type'] == 'track' and not t['is_local']})

    print(f'+ Added {len(resp["items"])} songs from {playlist.name}')

  # clear it
  await sc.put(f'playlists/{ds_playlist_id}/tracks', uris=[], body=True)

  # fill it
  await sc.add_tracks_to_playlist(ds_playlist_id, list(songs)[:songs_count])

  # edit last update time
  await sc.edit_playlist(ds_playlist_id,
                         description=f'🕺 Last updated by Muzee @ {ctx.user.now().strftime("%H:%M %d/%m/%Y")}.')

  return ds_playlist_id


@use_spotify
async def run_public_liked(ctx: Context, sc: MySpotifyClient, create: bool = False):
  """
  🩷 Create a public playlist from the user's unshareable Liked Songs.

  :param create: Create a new playlist for the Public Liked Songs
  """

  assert ctx.user.pl_playlist or create is True, "No playlist set for Public Liked."

  if create:
    playlist = await sc.create_playlist(
      user=ctx.user.spotify_id,
      name=f'Public Liked - {ctx.user.username}',
      description='🎸 Here is what I listen to...',
      public=True
    )
    pl_playlist_id = playlist.id
  else:
    pl_playlist_id = ctx.user.pl_playlist

    # does it exist? no point to continue if we can't add songs to it.
    js = await sc.get(f'playlists/{pl_playlist_id}', fields='id')

    if js.get('error'):
      return

  # method: remove songs that are not in liked and add songs that are missing

  # get the user's liked songs
  liked = await sc.get_all_playlist_tracks("likedsongs")
  print(f'{len(liked)} {liked=}')
  mirror = await sc.get_all_playlist_tracks(pl_playlist_id, fields='items(is_local,track(type,uri))')
  print(f'{len(mirror)} {mirror=}')

  liked_uris = {t['track']['uri'] for t in liked}
  print(f'{len(liked_uris)} {liked_uris=}')
  mirror_uris = {t['track']['uri'] for t in mirror}
  print(f'{len(mirror_uris)} {mirror_uris=}')

  remove_uris = mirror_uris - liked_uris
  print(f'{len(remove_uris)} {remove_uris=}')
  add_uris = liked_uris - mirror_uris
  print(f'{len(add_uris)} {add_uris=}')

  if remove_uris:
    await sc.delete_playlist_tracks(pl_playlist_id, list(remove_uris))

  if add_uris:
    await sc.add_tracks_to_playlist(pl_playlist_id, list(add_uris))

  # edit last update time
  await sc.edit_playlist(pl_playlist_id,
                         description=f'🩷 Last updated by Muzee @ {ctx.user.now().strftime("%H:%M %d/%m/%Y")}.')

  return pl_playlist_id

import base64
import logging

import aiohttp
import asyncspotify.exceptions

from server.database import Database
from server.models.user import User


class OAuthError(Exception):
    pass


class CantRefresh(Exception):
    pass


import asyncspotify as sp


class MyAuthenticator(sp.oauth.flows.Authenticator):
    def __init__(
        self, client: "MySpotifyClient", client_id, client_secret, access_token
    ):
        super().__init__(client_id, client_secret)

        self.my_client = client

    @property
    def access_token(self):
        return self.my_client.access_token

    @property
    def header(self):
        return {"Authorization": f"Bearer {self.access_token}"}


class MyHTTP(sp.http.HTTP):
    async def refresh_token(self):
        data = dict(
            grant_type="refresh_token",
            refresh_token=self.client.refresh_token,
            client_id=self.client.auth.client_id,
            client_secret=self.client.auth.client_secret,
        )

        async with aiohttp.ClientSession() as cs:
            async with cs.post(
                "https://accounts.spotify.com/api/token", data=data
            ) as resp:
                js = await resp.json()

        if js.get("error") == "invalid_grant":
            raise CantRefresh()

        old_access_token = self.client.access_token
        self.client.access_token = js["access_token"]

        await self.client.db.pool.execute(
            """UPDATE users SET access_token = $1 WHERE access_token = $2""",
            self.client.access_token,
            old_access_token,
        )

        return

    async def request(self, *args, _refresh=0, **kwargs):
        self.client: MySpotifyClient

        try:
            return await super().request(*args, **kwargs)
        except sp.Unauthorized as e:
            if _refresh > 2:
                raise CantRefresh()

            await self.refresh_token()

            return await self.request(*args, _refresh=_refresh + 1, **kwargs)
        except (sp.BadRequest, sp.Forbidden) as e:
            logging.error(f"{e.__class__.__name__} on {args=} {kwargs=}")

            raise e


class MySpotifyClient(sp.Client):
    # noinspection PyMissingConstructor
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        refresh_token: str,
        db: Database,
    ):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.db = db

        self.client_id = client_id
        self.client_secret = client_secret

        self.auth = MyAuthenticator(
            self,
            client_id=self.client_id,
            client_secret=self.client_secret,
            access_token=self.access_token,
        )
        self.http = MyHTTP(self)

    async def get(self, endpoint: str, **params):
        return await self.http.request(sp.Route("GET", endpoint, **params))

    async def put(self, endpoint: str, **params):
        is_body = params.pop("body", False)

        if is_body:
            return await self.http.request(sp.Route("PUT", endpoint), json=params)

        return await self.http.request(sp.Route("PUT", endpoint, **params))

    async def post(self, endpoint: str, **data):
        return await self.http.request(sp.Route("POST", endpoint), json=data)

    async def delete(self, endpoint: str, **data):
        return await self.http.request(sp.Route("DELETE", endpoint), json=data)

    @staticmethod
    def _is_track(it: dict) -> bool:
        if it["track"]["uri"] is None:
            return False
        if it["track"].get("type", "track") != "track":
            return False
        if it.get("is_local", False):
            return False
        if it["track"].get("is_local", False):
            return False

        return True

    async def get_all_playlist_tracks(self, playlist_id: str, **kw) -> list[dict]:
        """
        Return all the tracks in a playlist
        """

        tracks = []
        offset = 0
        limit = 50

        if playlist_id == "likedsongs":
            kw.pop("fields", None)
            endpoint = f"me/tracks"
        else:
            endpoint = f"playlists/{playlist_id}/tracks"

        while True:
            js = await self.get(endpoint, limit=limit, offset=offset, **kw)
            items = js["items"]
            tracks += [t for t in items if MySpotifyClient._is_track(t)]

            if len(items) < limit:
                break

            offset += limit

        return tracks

    async def add_tracks_to_playlist(self, playlist_id: str, tracks_ids: list[str]):
        """
        Add tracks to a playlist
        """

        limit = 50

        while tracks_ids:
            await self.post(f"playlists/{playlist_id}/tracks", uris=tracks_ids[:limit])
            tracks_ids = tracks_ids[limit:]

    async def delete_playlist_tracks(self, playlist_id: str, tracks_ids: list[str]):
        """
        Remove the tracks from a playlist
        """

        limit = 50

        while tracks_ids:
            await self.delete(
                f"playlists/{playlist_id}/tracks",
                tracks=[{"uri": uri} for uri in tracks_ids[:limit]],
            )
            tracks_ids = tracks_ids[limit:]

    async def get_image(self, playlist_id: str) -> str | None:
        """
        Get the image of a playlist
        """

        try:
            js = await self.get(f"playlists/{playlist_id}/images")
            return js[0]["url"] if js else None
        except sp.NotFound:
            return None


def sp_endpoint(keep_client: bool = False):
    """
    Allows a caller to simply enter the user's model object or the user's access token and refresh token
    and the function will automatically create a SpotifyApiClient object and pass it to the function.

    If the user provides an access_token but not a refresh_token, no refresh will be done and an exception may be raised.
    """

    def wrapper(func):
        async def inner(
            self: "Spotify",
            *args,
            user: User = None,
            access_token: str = None,
            refresh_token: str = None,
            **kwargs,
        ):
            assert user or (
                access_token and refresh_token
            ), "You must provide either a user object or an access token and a refresh token"

            if user:
                access_token = user.access_token
                refresh_token = user.refresh_token

            sc = MySpotifyClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                access_token=access_token,
                refresh_token=refresh_token,
                db=self.db,
            )

            try:
                resp = await func(self, sc, *args, **kwargs)
            except asyncspotify.exceptions.SpotifyException as e:
                resp = {"error": e.args[0]}

            if keep_client is False:
                await sc.close()

            return resp

        return inner

    return wrapper


class Spotify:
    API_ENDPOINT = "https://api.spotify.com/v1"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scope: str,
        server_url: str,
        db: Database,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.server_url = server_url
        self.db = db

    async def get_access_token_from_code(self, code: str):
        """
        Get the access token & refresh token from Spotify using the code
        """

        data = dict(
            grant_type="authorization_code",
            code=code,
            redirect_uri=self.server_url + "/oauth2/callback",
        )

        headers = {
            "Authorization": "Basic "
            + base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
        }

        async with aiohttp.ClientSession() as cs:
            async with cs.post(
                "https://accounts.spotify.com/api/token", data=data, headers=headers
            ) as resp:
                js = await resp.json()

                if resp.status != 200:
                    raise OAuthError(js)

                return js

    async def refresh_access_token(self, refresh_token: str):
        """
        Refresh the access token using the refresh token
        """

        data = dict(
            grant_type="refresh_token",
            refresh_token=refresh_token,
        )

        auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.API_ENDPOINT + "/oauth2/token", data=data, auth=auth
            ) as resp:
                js = await resp.json()

                if resp.status != 200:
                    raise OAuthError(js)

                return js

    @sp_endpoint(keep_client=True)
    async def get_client(self, sc: MySpotifyClient) -> MySpotifyClient:
        """
        Returns the SpotifyClient
        The caller needs to close the client.
        """

        return sc

    @sp_endpoint()
    async def fetch_user_info(self, sc: MySpotifyClient):
        return await sc.get_me()

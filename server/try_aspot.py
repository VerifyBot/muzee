import asyncio

import aiohttp
import asyncspotify as sp

from asyncspotify.http import Route

client_id = "1700b889495042f69c024ef1f55287f6"
client_secret = "d1d8c5ad27bf43eca11b8be53347206c"
access_token = 'BQD-JYErSTB2ejXQx7OA7Nmkrp5Ef_wQK2jcTyUTsZwVAtvtBTL5EJcqw3aKM66RGPmy2XlCy29qqjnDhFZ7IB4e7GssPmTr2WXAAuxaf4JLnrtdLg2b3DSEHTbaqjNDLS6vO6ivSPHoeDWUaKX1NUDR5n4KCKTG4ieuoldKek_32Imkhl2npS3c3IJx9XVCHCcx-Ygy5no6SHtBYdc1BxL14n7bu6eCtu0s0Oa4tNXcM7EPGB1D541RKPvEwK-N27PH56Cr0lBBws7n'
refresh_token = "AQBZvVC419Ryctf7JBjEQfks-xvLDE4Pda8v3J1g1DgHyIx_IQEXal0O1hnksU_M_BllfhFX_TGPNa1UiOnyF6qH7FiaJ3Nwq80zoGg4PaZ-3Hs3VQNMsQZw2V_Ch80xNJc"



class MyAuthenticator(sp.oauth.flows.Authenticator):
  @property
  def header(self):
    return {"Authorization": f"Bearer {access_token}"}

class MyHTTP(sp.http.HTTP):
  async def request(self, *args, **kwargs):
    global access_token, refresh_token
    try:
      return await super().request(*args, **kwargs)
    except sp.Unauthorized as e:
      # refresh
      print('REFRESHING....')
      async with aiohttp.ClientSession() as cs:
        async with cs.post(
          "https://accounts.spotify.com/api/token",
          data=dict(
            grant_type="refresh_token",
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
          )
        ) as resp:
          js = await resp.json()
          print(js)
          access_token = js["access_token"]

        print(f'NEW: {access_token=} {refresh_token=}')
        return await self.request(*args, **kwargs)

class MyClient(sp.Client):
  def __init__(self, auth):
    self.auth = auth(self)
    self.http = MyHTTP(self)

c = MyClient(MyAuthenticator(client_id=client_id, client_secret=client_secret))

async def main():
  try:
    p = await c.http.request(
      Route('GET', 'search', q='test', type='playlist', limit=1)
    )
    print(p)
  finally:
    await c.close()

if __name__ == '__main__':
  loop = asyncio.get_event_loop()
  loop.run_until_complete(main())
